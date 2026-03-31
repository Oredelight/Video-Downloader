from django.shortcuts import render
import yt_dlp
import os
from django.http import FileResponse

def home(request):
    return render(request, "home.html")

def download_video(request):
    if request.method == "POST":
        url = request.POST.get("url")

        if not url:
            return render(request, "home.html", {"error": "Please enter a valid URL."})
        
        ydl_opts = {
            'format': 'best',
            'outtmpl': 'media/%(title)s.%(ext)s',
        }

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                filename = ydl.prepare_filename(info)

                return FileResponse(
                    open(filename, 'rb'),
                    as_attachment=True,
                    filename=os.path.basename(filename)
                )
        except Exception as e:
            return render(request, "home.html", {"error": str(e)})
        
    return render(request, "home.html")
