import os
import random
import re
import asyncio
from concurrent.futures import ThreadPoolExecutor

from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import CommandStart
from aiogram.types import FSInputFile
from yt_dlp import YoutubeDL
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext

from app.database import requests as rq
from app.keyboards import choice_button, quality_button, back_button

router = Router()


class UserStates(StatesGroup):
    waiting_for_link = State()
    waiting_for_format = State()
    waiting_for_quality = State()


emojis = ['😀', '🥶', '😃', '🫨', '🫥', '🥰', '👋', '🦋', '🐱', '🦁', '🦉', '🌚', '⭐️']


@router.message(CommandStart())
async def start(message: Message):
    await rq.set_user(message.from_user.id)
    random_emoji = random.choice(emojis)
    await message.answer(f'{random_emoji}')
    await message.answer('Welcome!\nSend me the link from YouTube and I will convert it to \nAudio or Video♻️')


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
    quality_formats = {
        '240p': 'bestvideo[height<=240]+bestaudio/best',
        '360p': 'bestvideo[height<=360]+bestaudio/best',
        '480p': 'bestvideo[height<=480]+bestaudio/best',
        '720p': 'bestvideo[height<=720]+bestaudio/best',
        '1080p': 'bestvideo[height<=1080]+bestaudio/best',
    }
    #'1080p': 'bestvideo[height<=1080][vcodec=avc1]+bestaudio[acodec=mp4a]/best',
    ydl_opts = {
        'format': quality_formats.get(quality, 'bestvideo+bestaudio/best'),
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


@router.message(F.text.contains('youtu'))
async def handle_youtube_link(message: Message, state: FSMContext):
    url = message.text
    clean_url = clean_youtube_url(url)
    await state.set_state(UserStates.waiting_for_format)
    await state.update_data(url=clean_url)
    reply_message = await message.reply("Select the format you want to convert the video to.",
                                        reply_markup=await choice_button())
    await state.update_data(reply_message_id=reply_message.message_id)


@router.callback_query(F.data.in_(['mp4', 'mp3']))
async def process_format_callback(callback: CallbackQuery, state: FSMContext):
    format_type = callback.data
    await callback.answer()
    await state.update_data(format_type=format_type)

    if format_type == 'mp4':
        quality_buttons = await quality_button()
        await state.set_state(UserStates.waiting_for_quality)
        await callback.message.edit_text("Select the video quality.", reply_markup=quality_buttons)

    elif format_type == 'mp3':
        user_data = await state.get_data()
        url = user_data.get('url')
        await convert_and_send_audio(callback, state, url)


async def convert_and_send_audio(callback: CallbackQuery, state: FSMContext, url: str):
    con_answer = await callback.message.answer(text="Converting video to MP3, please wait...⏳")
    await state.update_data(con_answer_id=con_answer.message_id)
    user_data = await state.get_data()
    reply_message_id = user_data.get('reply_message_id')

    if reply_message_id:
        try:
            await callback.bot.delete_message(chat_id=callback.message.chat.id, message_id=reply_message_id)
        except Exception as e:
            print(f"Error deleting message: {e}")
    audio_file_path = None
    try:
        audio_file_path = await download_youtube_audio(url)
        audio_file = FSInputFile(audio_file_path)
        await callback.message.answer_audio(audio_file)
        os.remove(audio_file_path)
        con_answer_id = (await state.get_data()).get('con_answer_id')
        if con_answer_id:
            await callback.bot.edit_message_text(
                text="✅",
                chat_id=callback.message.chat.id,
                message_id=con_answer_id
            )
    except Exception as e:
        await callback.message.answer(f"Error: Failed to convert audio! {str(e)}")
        os.remove(audio_file_path)


@router.callback_query(F.data.in_(['240p', '360p', '480p', '720p', '1080p']))
async def process_quality_callback(callback: CallbackQuery, state: FSMContext):
    quality = callback.data
    await callback.answer()

    user_data = await state.get_data()
    url = user_data.get('url')

    if not url:
        await callback.message.answer("Error: You need to provide a valid YouTube URL first.")
        return

    con_answer = await callback.message.answer(f"Downloading video in {quality}, please wait...⏳")
    await state.update_data(con_answer_id=con_answer.message_id)
    reply_message_id = user_data.get('reply_message_id')

    if reply_message_id:
        try:
            await callback.bot.delete_message(chat_id=callback.message.chat.id, message_id=reply_message_id)
        except Exception as e:
            print(f"Error deleting message: {e}")
    video_file_path = None
    try:
        video_file_path = await download_youtube_video(url, quality)
        if video_file_path:
            video_file = FSInputFile(video_file_path)
            file_size = os.path.getsize(video_file_path)
            if file_size <= 44 * 1024 * 1024:  # 50 MB
                await callback.message.answer_video(video_file)
            else:
                await callback.message.answer_document(video_file)
            os.remove(video_file_path)
            con_answer_id = (await state.get_data()).get('con_answer_id')
            if con_answer_id:
                await callback.bot.edit_message_text(
                    text="✅",
                    chat_id=callback.message.chat.id,
                    message_id=con_answer_id
                )
        else:
            await callback.message.answer("Error: Failed to download video.")
            os.remove(video_file_path)
    except Exception as e:
        await callback.message.answer(f"Error: Failed to download video! {str(e)}\nFile is more than 50mb!")
        os.remove(video_file_path)


@router.callback_query(F.data == 'back')
async def return_to_back(callback: CallbackQuery, state: FSMContext):
    await state.set_state(UserStates.waiting_for_format)

    await callback.message.edit_text(
        text='Select the format you want to convert the video to.',
        reply_markup=await choice_button()
    )


@router.callback_query(F.data == 'cancel')
async def cancel(callback: CallbackQuery):
    await callback.message.delete()