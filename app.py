from fastapi import FastAPI, Request, Response, Header, HTTPException, Path as FastAPIPath
from fastapi.responses import HTMLResponse, FileResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from pathlib import Path
from typing import List
from fastapi.templating import Jinja2Templates
import ffmpeg
import os
import re
from datetime import datetime
import aiofiles
import logging
import mimetypes

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.StreamHandler()
    ]
)

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")
app.mount("/videos", StaticFiles(directory="videos"), name="videos")
app.mount("/audio", StaticFiles(directory="videos"), name="audio")

templates = Jinja2Templates(directory="templates")

VIDEO_EXTENSIONS = ['.mp4', '.avi', '.mkv']
AUDIO_EXTENSIONS = ['.mp3', '.wav', '.ogg']


# Валидация имени аккаунта и имени файла
def validate_account_name(account_name: str):
    if not re.match(r'^[\w\sа-яА-ЯёЁ _\'-]+$', account_name):
        logging.warning(f"Неверный формат имени аккаунта: {account_name}")
        raise HTTPException(status_code=400, detail="Неверный формат имени аккаунта")


def validate_file_name(file_name: str, allowed_extensions: List[str]):
    if not re.match(r'^[\w\sа-яА-ЯёЁ _\'-]+\.(mp4|avi|mkv|mp3|wav|ogg)$', file_name.lower()):
        logging.warning(f"Неверный формат имени файла: {file_name}")
        raise HTTPException(status_code=400, detail="Неверный формат имени файла")
    if not any(file_name.lower().endswith(ext) for ext in allowed_extensions):
        logging.warning(f"Недопустимое расширение файла: {file_name}")
        raise HTTPException(status_code=400, detail="Недопустимое расширение файла")


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
            logging.info(f"Превью сгенерировано для {video_name}")
        except ffmpeg.Error as e:
            logging.error(f"Ошибка при генерации превью для {video_name}: {e.stderr.decode()}")
            return "/static/images/video.png"
        except FileNotFoundError as e:
            logging.error(f"FFmpeg не найден: {e}")
            return "/static/images/video.png"
    return f"/videos/{account_name}/{thumbnail_name}"


@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request, query: str = None):
    videos_path = Path("videos")
    accounts = [d for d in videos_path.iterdir() if d.is_dir()]
    results = {'accounts': [], 'videos': [], 'audios': []}

    if query:
        for account_dir in accounts:
            account = account_dir.name
            validate_account_name(account)
            account_path = videos_path / account
            logo_url = await get_account_logo_url(account)
            if query.lower() in account.lower():
                video_count = len([f for f in account_path.glob("*") if f.is_file() and f.suffix.lower() in VIDEO_EXTENSIONS])
                audio_count = len([f for f in account_path.glob("*") if f.is_file() and f.suffix.lower() in AUDIO_EXTENSIONS])
                results['accounts'].append({'type': 'account', 'name': account, 'logo_url': logo_url, 'video_count': video_count, 'audio_count': audio_count})
            # Поиск видео
            videos = [f for f in account_path.glob("*") if f.is_file() and f.suffix.lower() in VIDEO_EXTENSIONS]
            for video in videos:
                if query.lower() in video.stem.lower():
                    thumbnail_url = await generate_video_thumbnail(account, video.name)
                    results['videos'].append({'type': 'video', 'account': account, 'name': video.name, 'thumbnail_url': thumbnail_url, 'logo_url': logo_url})
            # Поиск аудио
            audios = [f for f in account_path.glob("*") if f.is_file() and f.suffix.lower() in AUDIO_EXTENSIONS]
            for audio in audios:
                if query.lower() in audio.stem.lower():
                    results['audios'].append({'type': 'audio', 'account': account, 'name': audio.name, 'logo_url': logo_url})
    else:
        for account_dir in accounts:
            account = account_dir.name
            validate_account_name(account)
            account_path = videos_path / account
            logo_url = await get_account_logo_url(account)
            video_count = len([f for f in account_path.glob("*") if f.is_file() and f.suffix.lower() in VIDEO_EXTENSIONS])
            audio_count = len([f for f in account_path.glob("*") if f.is_file() and f.suffix.lower() in AUDIO_EXTENSIONS])
            results['accounts'].append({'type': 'account', 'name': account, 'logo_url': logo_url, 'video_count': video_count, 'audio_count': audio_count})

    return templates.TemplateResponse("index.html", {"request": request, "results": results, "query": query})


@app.get("/account/{account_name}", response_class=HTMLResponse)
async def read_account(request: Request, account_name: str = FastAPIPath(..., pattern="^[\w\sа-яА-ЯёЁ _\'-]+$")):
    validate_account_name(account_name)
    account_path = Path("videos") / account_name
    if not account_path.exists() or not account_path.is_dir():
        logging.warning(f"Аккаунт не найден: {account_name}")
        return HTMLResponse("Аккаунт не найден", status_code=404)
    # Видео
    videos = [f.name for f in account_path.glob("*") if f.is_file() and f.suffix.lower() in VIDEO_EXTENSIONS and f.name != 'logo.png']
    video_items = []
    for video in videos:
        thumbnail_url = await generate_video_thumbnail(account_name, video)
        video_items.append({'name': video, 'thumbnail_url': thumbnail_url})
    # Аудио
    audios = [f.name for f in account_path.glob("*") if f.is_file() and f.suffix.lower() in AUDIO_EXTENSIONS]
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
async def play_video(request: Request, account_name: str = FastAPIPath(..., pattern="^[\w\sа-яА-ЯёЁ _\'-]+$"),
                     video_name: str = FastAPIPath(..., pattern="^[\w\sа-яА-ЯёЁ _\'-]+\.(mp4|avi|mkv)$")):
    validate_account_name(account_name)
    validate_file_name(video_name, VIDEO_EXTENSIONS)
    video_path = Path("videos") / account_name / video_name
    if not video_path.exists():
        logging.warning(f"Видео не найдено: {video_name} в аккаунте {account_name}")
        return HTMLResponse("Видео не найдено", status_code=404)
    # Получаем другие видео канала
    account_path = Path("videos") / account_name
    other_videos = [f.name for f in account_path.glob("*") if f.is_file() and f.name != video_name and f.suffix.lower() in VIDEO_EXTENSIONS]
    other_video_items = []
    for other_video in other_videos:
        thumbnail_url = await generate_video_thumbnail(account_name, other_video)
        other_video_items.append({'name': other_video, 'thumbnail_url': thumbnail_url})

    # Получаем другие аудио с канала
    audios = [f.name for f in account_path.glob("*") if f.is_file() and f.suffix.lower() in AUDIO_EXTENSIONS]
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
async def stream_video(request: Request, account_name: str = FastAPIPath(..., pattern="^[\w\sа-яА-ЯёЁ _\'-]+$"),
                       video_name: str = FastAPIPath(..., pattern="^[\w\sа-яА-ЯёЁ _\'-]+\.(mp4|avi|mkv)$")):
    validate_account_name(account_name)
    validate_file_name(video_name, VIDEO_EXTENSIONS)
    video_path = Path("videos") / account_name / video_name
    if not video_path.exists():
        logging.warning(f"Видео не найдено для стриминга: {video_name} в аккаунте {account_name}")
        raise HTTPException(status_code=404, detail="Видео не найдено")

    mime_type, _ = mimetypes.guess_type(video_path)
    mime_type = mime_type or 'application/octet-stream'
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
                logging.warning(f"Неверный диапазон запроса: {content_range}")
                return Response(status_code=416)

            async def iterfile():
                async with aiofiles.open(video_path, 'rb') as f:
                    await f.seek(start)
                    bytes_to_send = end - start + 1
                    chunk_size = 1024 * 1024
                    while bytes_to_send > 0:
                        read_bytes = min(chunk_size, bytes_to_send)
                        data = await f.read(read_bytes)
                        if not data:
                            break
                        yield data
                        bytes_to_send -= len(data)

            headers['Content-Range'] = f'bytes {start}-{end}/{file_size}'
            return StreamingResponse(iterfile(), status_code=206, headers=headers, media_type=mime_type)
    else:
        return FileResponse(video_path, media_type=mime_type)


@app.get("/audio/{account_name}/{audio_name}")
async def stream_audio(request: Request, account_name: str = FastAPIPath(..., pattern="^[\w\sа-яА-ЯёЁ _\'-]+$"),
                       audio_name: str = FastAPIPath(..., pattern="^[\w\sа-яА-ЯёЁ _\'-]+\.(mp3|wav|ogg)$")):
    validate_account_name(account_name)
    validate_file_name(audio_name, AUDIO_EXTENSIONS)
    audio_path = Path("videos") / account_name / audio_name
    if not audio_path.exists():
        logging.warning(f"Аудио не найдено для стриминга: {audio_name} в аккаунте {account_name}")
        raise HTTPException(status_code=404, detail="Аудио не найдено")

    mime_type, _ = mimetypes.guess_type(audio_path)
    mime_type = mime_type or 'application/octet-stream'
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
                logging.warning(f"Неверный диапазон запроса: {content_range}")
                return Response(status_code=416)

            async def iterfile():
                async with aiofiles.open(audio_path, 'rb') as f:
                    await f.seek(start)
                    bytes_to_send = end - start + 1
                    chunk_size = 1024 * 1024
                    while bytes_to_send > 0:
                        read_bytes = min(chunk_size, bytes_to_send)
                        data = await f.read(read_bytes)
                        if not data:
                            break
                        yield data
                        bytes_to_send -= len(data)

            headers['Content-Range'] = f'bytes {start}-{end}/{file_size}'
            return StreamingResponse(iterfile(), status_code=206, headers=headers, media_type=mime_type)
    else:
        return FileResponse(audio_path, media_type=mime_type)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app:app", host="127.0.0.1", port=8000, reload=True)
