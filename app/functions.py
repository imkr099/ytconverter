import re
import asyncio
from concurrent.futures import ThreadPoolExecutor
from yt_dlp import YoutubeDL


async def run_in_executor(func, *args):
    loop = asyncio.get_event_loop()
    with ThreadPoolExecutor() as pool:
        return await loop.run_in_executor(pool, func, *args)


def download_youtube_audio_sync(url):
    ydl_opts = {
        'format': 'bestaudio/best',
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
        'outtmpl': 'downloads/%(title)s.%(ext)s',
        'quiet': True,
    }
    with YoutubeDL(ydl_opts) as ydl:
        info_dict = ydl.extract_info(url, download=True)
        audio_file = ydl.prepare_filename(info_dict)
        return audio_file.replace('.webm', '.mp3').replace('.m4a', '.mp3')


def download_youtube_video_sync(url, quality) -> str:
    ydl_opts = {
        'format': f'bestvideo[height<={quality[:-1]}]+bestaudio/best',
        'merge_output_format': 'mp4',
        'outtmpl': 'downloads/%(title)s.%(ext)s',
        'quiet': True,
    }
    with YoutubeDL(ydl_opts) as ydl:
        try:
            info_dict = ydl.extract_info(url, download=True)
            video_file = ydl.prepare_filename(info_dict)
            return video_file
        except Exception as e:
            print(f"Error downloading video: {e}")
            return None


async def download_youtube_audio(url):
    return await run_in_executor(download_youtube_audio_sync, url)


async def download_youtube_video(url, quality):
    return await run_in_executor(download_youtube_video_sync, url, quality)


def clean_youtube_url(url: str) -> str:
    match = re.match(r'(https://www\.youtube\.com/watch\?v=[\w-]+)', url)
    if match:
        return match.group(1)
    return url


async def get_available_qualities(url):
    ydl_opts = {'quiet': True}
    with YoutubeDL(ydl_opts) as ydl:
        info_dict = ydl.extract_info(url, download=False)
        formats = info_dict.get('formats', [])
        qualities = sorted(set([f.get('height') for f in formats if f.get('height') and f.get('height') >= 144]))
        return [f"{quality}p" for quality in qualities]