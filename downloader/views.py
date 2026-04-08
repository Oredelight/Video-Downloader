import os
import re
import uuid
import shutil
import tempfile
from django.conf import settings
from django.shortcuts import render
from django.http import StreamingHttpResponse
from django.views.decorators.csrf import csrf_exempt
import yt_dlp


ALLOWED_DOMAINS = {
    "youtube.com", "youtu.be", "tiktok.com",
    "instagram.com", "twitter.com", "x.com"
}

COOKIE_FILE = os.path.join(settings.BASE_DIR, 'youtube_cookies.txt')

def _ydl_opts(skip_download=False, outtmpl=None):
    opts = {
        'quiet': True,
        'skip_download': skip_download,
        'noplaylist': True,
        'nocheckcertificate': True,
        'youtube_include_dash_manifest': True,
        'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/bestvideo+bestaudio/best',
        'merge_output_format': 'mp4',
        'cookiefile': '/etc/secrets/cookies.txt'
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


def preview_video(request):
    if request.method != "POST":
        return render(request, "home.html")

    url = request.POST.get("url", "").strip()
    if not url:
        return render(request, "home.html", {"error": "Please enter a URL."})
    if not is_url_allowed(url):
        return render(request, "home.html", {"error": "Unsupported URL. Paste a YouTube, TikTok, or Instagram link."})

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
                "error": "No formats found. Try again or check your cookie file.",
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
    format_id = request.POST.get("format_id", "").strip()

    if not url or not format_id:
        return render(request, "home.html", {"error": "Missing URL or format."})
    if not is_url_allowed(url):
        return render(request, "home.html", {"error": "Unsupported URL."})
    if not re.match(r'^[\w\-.]+$', format_id):
        return render(request, "home.html", {"error": "Invalid format ID."})

    tmp_dir = tempfile.mkdtemp(prefix='vdrop_')
    safe_name = str(uuid.uuid4())

    opts = _ydl_opts(
        skip_download=False,
        outtmpl=os.path.join(tmp_dir, f'{safe_name}.%(ext)s'),
    )
    opts.update({
        'format': f'{format_id}+bestaudio[ext=m4a]/{format_id}+bestaudio/best',
        'merge_output_format': 'mp4',
        'overwrites': True,
        'nopart': True,
    })

    filename = None
    try:
        with yt_dlp.YoutubeDL(opts) as ydl:
            info = ydl.extract_info(url, download=True)
            if 'entries' in info:
                info = info['entries'][0]

            base = os.path.splitext(ydl.prepare_filename(info))[0]
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

        safe_title = re.sub(r'[^\w\s\-.]', '', info.get('title', 'video')).strip()[:80] or 'video'
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