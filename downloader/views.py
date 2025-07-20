import os
import tempfile
from django.http import FileResponse, HttpResponseBadRequest
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import render
from yt_dlp import YoutubeDL
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.forms import AuthenticationForm
from django.shortcuts import redirect
from .forms import RegisterForm


def register_view(request):
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)  # Log the user in after registration
            return redirect('index')
    else:
        form = RegisterForm()
    return render(request, 'downloader/register.html', {'form': form})

def login_view(request):
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            return redirect('index')
    else:
        form = AuthenticationForm()
    return render(request, 'downloader/login.html', {'form': form})

def logout_view(request):
    logout(request)
    return redirect('index')


@csrf_exempt
def index(request):
    if request.method == 'POST':
        url = request.POST.get('url')
        fmt = request.POST.get('format', 'mp4')
        quality = request.POST.get('quality', 'best')
        subtitle = request.POST.get('subtitle', 'no')

        if not url:
            return HttpResponseBadRequest("Missing URL")

        # Base options
        options = {
            'outtmpl': os.path.join(tempfile.gettempdir(), '%(title)s.%(ext)s'),
            'quiet': True,
            'no_warnings': True,
        }

        # Format selection logic
        if fmt == 'mp3':
            options['format'] = 'bestaudio/best'
            options['postprocessors'] = [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }]
        else:
            # Video format and quality filtering
            if quality in ['1080', '720', '480']:
                # Select best video up to specified height + best audio
                options['format'] = f'bestvideo[height<={quality}]+bestaudio/best[height<={quality}]'
            elif quality == 'audio':
                options['format'] = 'bestaudio/best'
            else:
                options['format'] = 'bestvideo+bestaudio/best'

            # If user wants mp4 or webm explicitly, add format restrictions
            if fmt in ['mp4', 'webm']:
                options['format'] += f'[ext={fmt}]'

        # Subtitles option
        if subtitle == 'yes':
            options['writesubtitles'] = True
            options['subtitleslangs'] = ['en']
            options['subtitlesformat'] = 'srt'  # You can choose 'srt' or 'vtt'

        with YoutubeDL(options) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)

            # Adjust filename extension for mp3 postprocessor
            if fmt == 'mp3':
                filename = os.path.splitext(filename)[0] + '.mp3'

        # Serve the file to user for download
        return FileResponse(open(filename, 'rb'), as_attachment=True, filename=os.path.basename(filename))

    # Render your template in downloader/templates/downloader/index.html
    return render(request, 'downloader/index.html')
