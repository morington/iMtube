from fastapi import FastAPI, Request, Response, Header, HTTPException
from fastapi.responses import HTMLResponse, FileResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from pathlib import Path
from typing import List
from fastapi.templating import Jinja2Templates
import ffmpeg
import os
import re
from datetime import datetime

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")
app.mount("/videos", StaticFiles(directory="videos"), name="videos")
app.mount("/audio", StaticFiles(directory="videos"), name="audio")

templates = Jinja2Templates(directory="templates")

async def get_account_logo_url(account_name: str):
    account_logo_path = Path("videos") / account_name / "logo.png"
    if account_logo_path.exists():
        return f"/videos/{account_name}/logo.png"
    else:
        return "/static/images/account.png"

async def generate_video_thumbnail(account_name: str, video_name: str):
    video_path = Path("videos") / account_name / video_name
    thumbnail_name = f"{video_name}.png"
    thumbnail_path = Path("videos") / account_name / thumbnail_name

    if not thumbnail_path.exists():
        try:
            (
                ffmpeg
                .input(str(video_path), ss=1)
                .filter('scale', 320, -1)
                .output(str(thumbnail_path), vframes=1)
                .run(capture_stdout=True, capture_stderr=True)
            )
        except ffmpeg.Error as e:
            print(f"Ошибка при генерации превью для {video_name}: {e.stderr.decode()}")
            return "/static/images/video.png"
        except FileNotFoundError as e:
            print(f"FFmpeg не найден: {e}")
            return "/static/images/video.png"
    return f"/videos/{account_name}/{thumbnail_name}"

@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request, query: str = None):
    videos_path = Path("videos")
    accounts = [d for d in videos_path.iterdir() if d.is_dir()]
    results = {'accounts': [], 'videos': [], 'audios': []}
    video_extensions = ['.mp4', '.avi', '.mkv']
    audio_extensions = ['.mp3', '.wav', '.ogg']

    if query:
        for account_dir in accounts:
            account = account_dir.name
            account_path = videos_path / account
            logo_url = await get_account_logo_url(account)
            if query.lower() in account.lower():
                video_count = len([f for f in account_path.glob("*") if f.is_file() and f.suffix.lower() in video_extensions])
                audio_count = len([f for f in account_path.glob("*") if f.is_file() and f.suffix.lower() in audio_extensions])
                results['accounts'].append({'type': 'account', 'name': account, 'logo_url': logo_url, 'video_count': video_count, 'audio_count': audio_count})
            # Поиск видео
            videos = [f for f in account_path.glob("*") if f.is_file() and f.suffix.lower() in video_extensions]
            for video in videos:
                if query.lower() in video.stem.lower():
                    thumbnail_url = await generate_video_thumbnail(account, video.name)
                    results['videos'].append({'type': 'video', 'account': account, 'name': video.name, 'thumbnail_url': thumbnail_url, 'logo_url': logo_url})
            # Поиск аудио
            audios = [f for f in account_path.glob("*") if f.is_file() and f.suffix.lower() in audio_extensions]
            for audio in audios:
                if query.lower() in audio.stem.lower():
                    results['audios'].append({'type': 'audio', 'account': account, 'name': audio.name, 'logo_url': logo_url})
    else:
        for account_dir in accounts:
            account = account_dir.name
            account_path = videos_path / account
            logo_url = await get_account_logo_url(account)
            video_count = len([f for f in account_path.glob("*") if f.is_file() and f.suffix.lower() in video_extensions])
            audio_count = len([f for f in account_path.glob("*") if f.is_file() and f.suffix.lower() in audio_extensions])
            results['accounts'].append({'type': 'account', 'name': account, 'logo_url': logo_url, 'video_count': video_count, 'audio_count': audio_count})

    return templates.TemplateResponse("index.html", {"request": request, "results": results, "query": query})

@app.get("/account/{account_name}", response_class=HTMLResponse)
async def read_account(request: Request, account_name: str):
    account_path = Path("videos") / account_name
    if not account_path.exists() or not account_path.is_dir():
        return HTMLResponse("Аккаунт не найден", status_code=404)
    # Видео
    video_extensions = ['.mp4', '.avi', '.mkv']
    videos = [f.name for f in account_path.glob("*") if f.is_file() and f.suffix.lower() in video_extensions and f.name != 'logo.png']
    video_items = []
    for video in videos:
        thumbnail_url = await generate_video_thumbnail(account_name, video)
        video_items.append({'name': video, 'thumbnail_url': thumbnail_url})
    # Аудио
    audio_extensions = ['.mp3', '.wav', '.ogg']
    audios = [f.name for f in account_path.glob("*") if f.is_file() and f.suffix.lower() in audio_extensions]
    audio_items = [{'name': audio} for audio in audios]
    # Логотип
    logo_url = await get_account_logo_url(account_name)
    return templates.TemplateResponse("account.html", {
        "request": request,
        "account": account_name,
        "videos": video_items,
        "audios": audio_items,
        "logo_url": logo_url
    })

@app.get("/video/{account_name}/{video_name}", response_class=HTMLResponse)
async def play_video(request: Request, account_name: str, video_name: str):
    video_path = Path("videos") / account_name / video_name
    if not video_path.exists():
        return HTMLResponse("Видео не найдено", status_code=404)
    # Получаем другие видео канала
    account_path = Path("videos") / account_name
    video_extensions = ['.mp4', '.avi', '.mkv']
    audio_extensions = ['.mp3', '.wav', '.ogg']

    other_videos = [f.name for f in account_path.glob("*") if f.is_file() and f.name != video_name and f.suffix.lower() in video_extensions]
    other_video_items = []
    for other_video in other_videos:
        thumbnail_url = await generate_video_thumbnail(account_name, other_video)
        other_video_items.append({'name': other_video, 'thumbnail_url': thumbnail_url})

    # Получаем другие аудио с канала
    audios = [f.name for f in account_path.glob("*") if f.is_file() and f.suffix.lower() in audio_extensions]
    other_audio_items = [{'name': audio} for audio in audios]

    # Получаем дату добавления видео
    video_added_date = datetime.fromtimestamp(video_path.stat().st_ctime).strftime('%Y-%m-%d %H:%M:%S')

    # Получаем URL логотипа канала
    logo_url = await get_account_logo_url(account_name)

    return templates.TemplateResponse("video.html", {
        "request": request,
        "account": account_name,
        "video": video_name,
        "other_videos": other_video_items,
        "other_audios": other_audio_items,
        "video_added_date": video_added_date,
        "logo_url": logo_url
    })

@app.get("/stream/{account_name}/{video_name}")
async def stream_video(request: Request, account_name: str, video_name: str):
    video_path = Path("videos") / account_name / video_name
    if not video_path.exists():
        raise HTTPException(status_code=404, detail="Видео не найдено")
    file_size = video_path.stat().st_size
    headers = {}
    content_range = request.headers.get('range')
    if content_range:
        content_range = content_range.strip().lower()
        range_match = re.match(r'bytes=(\d+)-(\d*)', content_range)
        if range_match:
            start = int(range_match.group(1))
            end = range_match.group(2)
            end = int(end) if end else file_size - 1
            if start >= file_size or end >= file_size:
                return Response(status_code=416)
            def iterfile():
                with open(video_path, 'rb') as f:
                    f.seek(start)
                    bytes_to_send = end - start + 1
                    chunk_size = 1024 * 1024
                    while bytes_to_send > 0:
                        read_bytes = min(chunk_size, bytes_to_send)
                        data = f.read(read_bytes)
                        if not data:
                            break
                        yield data
                        bytes_to_send -= read_bytes
            headers['Content-Range'] = f'bytes {start}-{end}/{file_size}'
            return StreamingResponse(iterfile(), status_code=206, headers=headers, media_type='video/mp4')
    else:
        return FileResponse(video_path, media_type='video/mp4')

@app.get("/audio/{account_name}/{audio_name}")
async def stream_audio(request: Request, account_name: str, audio_name: str):
    audio_path = Path("videos") / account_name / audio_name
    if not audio_path.exists():
        raise HTTPException(status_code=404, detail="Аудио не найдено")
    file_size = audio_path.stat().st_size
    headers = {}
    content_range = request.headers.get('range')
    if content_range:
        content_range = content_range.strip().lower()
        range_match = re.match(r'bytes=(\d+)-(\d*)', content_range)
        if range_match:
            start = int(range_match.group(1))
            end = range_match.group(2)
            end = int(end) if end else file_size - 1
            if start >= file_size or end >= file_size:
                return Response(status_code=416)
            def iterfile():
                with open(audio_path, 'rb') as f:
                    f.seek(start)
                    bytes_to_send = end - start + 1
                    chunk_size = 1024 * 1024
                    while bytes_to_send > 0:
                        read_bytes = min(chunk_size, bytes_to_send)
                        data = f.read(read_bytes)
                        if not data:
                            break
                        yield data
                        bytes_to_send -= read_bytes
            headers['Content-Range'] = f'bytes {start}-{end}/{file_size}'
            return StreamingResponse(iterfile(), status_code=206, headers=headers, media_type='audio/mpeg')
    else:
        return FileResponse(audio_path, media_type='audio/mpeg')

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", host="127.0.0.1", port=8000, reload=True)
