import os
import re
import uuid
import shutil
import tempfile
from django.shortcuts import render
from django.http import JsonResponse, StreamingHttpResponse
from django.views.decorators.csrf import csrf_exempt
import imageio_ffmpeg
import yt_dlp


# Copy read-only Render secret to a writable temp file once at startup
_cookie_tmp = tempfile.NamedTemporaryFile(suffix='.txt', delete=False)
_render_cookie = '/etc/secrets/cookies.txt'
if os.path.exists(_render_cookie):
    try:
        shutil.copy2(_render_cookie, _cookie_tmp.name)
    except Exception as e:
        print(f"Warning: Could not copy cookies: {e}")


ALLOWED_DOMAINS = {
    "youtube.com", "youtu.be", "tiktok.com",
    "instagram.com", "twitter.com", "x.com"
}


def _ydl_opts(skip_download=False, outtmpl=None):
    opts = {
        'quiet': True,
        'skip_download': skip_download,
        'noplaylist': True,
        'nocheckcertificate': True,
        #'youtube_include_dash_manifest': True,
        'cookiefile': _cookie_tmp.name,
        'ffmpeg_location': imageio_ffmpeg.get_ffmpeg_exe(),
        'extractor_args': {
            'youtube': {
                'player_client': ['ios'],
            },
        },
    }
    if outtmpl:
        opts['outtmpl'] = outtmpl
    return opts


def is_url_allowed(url):
    from urllib.parse import urlparse
    try:
        host = urlparse(url).netloc.lower().removeprefix("www.")
        return any(host == d or host.endswith("." + d) for d in ALLOWED_DOMAINS)
    except Exception:
        return False


def detect_platform(url):
    if "youtube" in url or "youtu.be" in url:
        return "YouTube"
    if "tiktok" in url:
        return "TikTok"
    if "instagram" in url:
        return "Instagram"
    if "twitter" in url or "x.com" in url:
        return "X (Twitter)"
    return "Unknown"


def home(request):
    return render(request, "home.html")


# ── Debug view — remove after confirming formats work ──
def debug_formats(request):
    url = request.GET.get("url", "").strip()
    if not url:
        return JsonResponse({"error": "Pass ?url=YOUR_YOUTUBE_URL"})
    try:
        results = []
        with yt_dlp.YoutubeDL(_ydl_opts(skip_download=True)) as ydl:
            info = ydl.extract_info(url, download=False)
            if 'entries' in info:
                info = info['entries'][0]
            for f in info.get('formats', []):
                results.append({
                    'format_id': f.get('format_id'),
                    'ext': f.get('ext'),
                    'height': f.get('height'),
                    'vcodec': f.get('vcodec'),
                    'acodec': f.get('acodec'),
                    'tbr': f.get('tbr'),
                })
        return JsonResponse({"total": len(results), "formats": results})
    except Exception as e:
        return JsonResponse({"error": str(e)})


def preview_video(request):
    if request.method != "POST":
        return render(request, "home.html")

    url = request.POST.get("url", "").strip()
    if not url:
        return render(request, "home.html", {"error": "Please enter a URL."})
    if not is_url_allowed(url):
        return render(request, "home.html", {"error": "Unsupported URL."})

    try:
        with yt_dlp.YoutubeDL(_ydl_opts(skip_download=True)) as ydl:
            info = ydl.extract_info(url, download=False)
            if 'entries' in info:
                info = info['entries'][0]

        formats_dict = {}
        for f in info.get('formats', []):
            if not f.get('vcodec') or f.get('vcodec') == 'none':
                continue
            height = f.get('height')
            if not height or height < 144:
                continue
            bitrate = f.get('tbr') or f.get('vbr') or 0
            if height not in formats_dict or bitrate > (formats_dict[height].get('tbr') or 0):
                formats_dict[height] = f

        if not formats_dict:
            return render(request, "home.html", {
                "error": "No formats found.",
                "url": url,
            })

        formats = sorted(
            [{'format_id': f['format_id'], 'quality': f'{h}p'} for h, f in formats_dict.items()],
            key=lambda x: int(x['quality'].replace('p', '')),
            reverse=True,
        )

        return render(request, "home.html", {
            "title": info.get("title"),
            "thumbnail": info.get("thumbnail"),
            "formats": formats,
            "url": url,
            "platform": detect_platform(url),
        })

    except Exception as e:
        return render(request, "home.html", {"error": str(e)})


@csrf_exempt
def download_video(request):
    if request.method != "POST":
        return render(request, "home.html")

    url = request.POST.get("url", "").strip()
    quality = request.POST.get("quality", "").strip()  # "1080p", "720p" etc.

    if not url or not quality:
        return render(request, "home.html", {"error": "Missing URL or quality."})
    if not is_url_allowed(url):
        return render(request, "home.html", {"error": "Unsupported URL."})

    try:
        height = int(quality.replace('p', ''))
    except ValueError:
        return render(request, "home.html", {"error": "Invalid quality."})

    tmp_dir = tempfile.mkdtemp(prefix='vdrop_')
    safe_name = str(uuid.uuid4())

    opts = _ydl_opts(
        skip_download=False,
        outtmpl=os.path.join(tmp_dir, f'{safe_name}.%(ext)s'),
    )

    # Re-fetch available formats fresh at download time so we never
    # use a stale format_id that YouTube has already rotated out.
    try:
        fresh_formats = []
        with yt_dlp.YoutubeDL(_ydl_opts(skip_download=True)) as ydl:
            info = ydl.extract_info(url, download=False)
            if 'entries' in info:
                info = info['entries'][0]
            for f in info.get('formats', []):
                if not f.get('vcodec') or f.get('vcodec') == 'none':
                    continue
                h = f.get('height')
                if not h:
                    continue
                fresh_formats.append((h, f['format_id']))

        # Pick the best format_id at or below the requested height
        candidates = [(h, fid) for h, fid in fresh_formats if h <= height]
        if candidates:
            chosen_id = max(candidates, key=lambda x: x[0])[1]
        else:
            # Nothing at or below requested height — just take highest available
            chosen_id = max(fresh_formats, key=lambda x: x[0])[1]

    except Exception as e:
        shutil.rmtree(tmp_dir, ignore_errors=True)
        return render(request, "home.html", {"error": f"Could not fetch formats: {e}"})

    opts.update({
        'format': f'{chosen_id}+bestaudio[ext=m4a]/{chosen_id}+bestaudio/{chosen_id}',
        'merge_output_format': 'mp4',
        'overwrites': True,
        'nopart': True,
    })

    filename = None
    try:
        with yt_dlp.YoutubeDL(opts) as ydl:
            dl_info = ydl.extract_info(url, download=True)
            if 'entries' in dl_info:
                dl_info = dl_info['entries'][0]

            base = os.path.splitext(ydl.prepare_filename(dl_info))[0]
            if os.path.exists(base + '.mp4'):
                filename = base + '.mp4'
            else:
                files = [
                    os.path.join(tmp_dir, f)
                    for f in os.listdir(tmp_dir)
                    if f.startswith(safe_name)
                ]
                if not files:
                    raise FileNotFoundError("Output file not found after download.")
                filename = files[0]

        safe_title = re.sub(r'[^\w\s\-.]', '', dl_info.get('title', 'video')).strip()[:80] or 'video'
        download_name = safe_title + os.path.splitext(filename)[1]
        file_size = os.path.getsize(filename)

        def stream_file(path, folder):
            try:
                with open(path, 'rb') as f:
                    while chunk := f.read(512 * 1024):
                        yield chunk
            finally:
                shutil.rmtree(folder, ignore_errors=True)

        response = StreamingHttpResponse(stream_file(filename, tmp_dir), content_type='video/mp4')
        response['Content-Disposition'] = f'attachment; filename="{download_name}"'
        response['Content-Length'] = file_size
        response['X-Accel-Buffering'] = 'no'
        return response

    except Exception as e:
        shutil.rmtree(tmp_dir, ignore_errors=True)
        return render(request, "home.html", {"error": str(e)})