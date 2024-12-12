import re
import asyncio
from concurrent.futures import ThreadPoolExecutor
import os
from yt_dlp import YoutubeDL
import subprocess


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
        'cookiefile': 'www.youtube.com_cookies.txt',
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
        'cookiefile': 'www.youtube.com_cookies.txt',
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
    ydl_opts = {'quiet': True,
                'cookiefile': 'www.youtube.com_cookies.txt'}
    with YoutubeDL(ydl_opts) as ydl:
        info_dict = ydl.extract_info(url, download=False)
        formats = info_dict.get('formats', [])
        qualities = sorted(set([f.get('height') for f in formats if f.get('height') and f.get('height') >= 144]))
        return [f"{quality}p" for quality in qualities]


def download_spotify_track_sync(url: str) -> str:
    output_dir = 'downloads'
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    command = ["spotdl", "download", url, "--output", output_dir]
    try:
        subprocess.run(command, shell=True, check=True, text=True, capture_output=True)
    except subprocess.CalledProcessError as e:
        print(f"Error occurred while running spotdl: {e}")
        print("Command output:", e.output)
        print("Command error:", e.stderr)
        raise Exception("Failed to download track.")

    downloaded_files = [f for f in os.listdir(output_dir) if f.endswith('.mp3')]
    if downloaded_files:
        downloaded_file_path = os.path.join(output_dir, downloaded_files[0])
        return downloaded_file_path
    else:
        raise Exception("Failed to download track.")


async def download_spotify_track(url: str) -> str:
    return await run_in_executor(download_spotify_track_sync, url)