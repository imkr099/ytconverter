import os

from aiogram import Router, F
from aiogram.types import Message
from aiogram.filters import CommandStart, Command
from aiogram.types import FSInputFile
from yt_dlp import YoutubeDL

from app.database import requests as rq


router = Router()


@router.message(CommandStart())
async def start(message: Message):
    await rq.set_user(message.from_user.id)
    await message.answer('Welcome! Send me the link from YouTube and I will convert it to mp3)')


def download_youtube_audio(url):
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


@router.message(F.text.startswith('https://www.youtube.com/'))
async def download_audio(message: Message):
    url = message.text
    await message.reply("Converting video, please wait...🌚")
    try:
        audio_file_path = download_youtube_audio(url)
        audio_file = FSInputFile(audio_file_path)
        await message.bot.send_audio(message.chat.id, audio_file)

        os.remove(audio_file_path)
    except Exception:
        await message.answer("Error! Wrong format!")
