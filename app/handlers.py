import os
import random

from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import CommandStart, Command
from aiogram.types import FSInputFile
from yt_dlp import YoutubeDL
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext

from app.database import requests as rq
from app.keyboards import choice_button

router = Router()


class UserStates(StatesGroup):
    waiting_for_link = State()
    waiting_for_format = State()


emojis = ['😀', '🥶', '😃', '🫨', '🫥', '🥰', '👋', '🦋', '🐱', '🦁', '🦉', '🌚', '⭐️']


@router.message(CommandStart())
async def start(message: Message):
    await rq.set_user(message.from_user.id)
    random_emoji = random.choice(emojis)
    await message.answer(f'{random_emoji}')
    await message.answer('Welcome!\nSend me the link from YouTube and I will convert it to \nAudio or Video♻️')


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


def download_youtube_video(url):
    ydl_opts = {
        'format': 'bestvideo+bestaudio/best',
        'merge_output_format': 'mp4',
        'outtmpl': 'downloads/%(title)s.%(ext)s',
        'quiet': True,
    }
    with YoutubeDL(ydl_opts) as ydl:
        info_dict = ydl.extract_info(url, download=True)
        video_file = ydl.prepare_filename(info_dict)
        return video_file.replace('.webm', '.mp4').replace('.m4a', '.mp4')


@router.message(F.text.startswith('https://www.youtube.com/'))
async def handle_youtube_link(message: Message, state: FSMContext):
    url = message.text
    await state.set_state(UserStates.waiting_for_format)
    await state.update_data(url=url)
    reply_message = await message.reply("Select the format you want to convert the video to.",
                                        reply_markup=await choice_button())
    await state.update_data(reply_message_id=reply_message.message_id)


@router.callback_query(F.data.in_(['mp4', 'mp3']))
async def process_callback(callback: CallbackQuery, state: FSMContext):
    format_type = callback.data
    await callback.answer()

    user_data = await state.get_data()
    url = user_data.get('url')
    reply_message_id = user_data.get('reply_message_id')

    if url:
        if format_type == 'mp4':
            con_answer1 = await callback.message.answer("Converting video to MP4, please wait...")
            await state.update_data(con_answer1=con_answer1.message_id)
            try:
                video_file_path = download_youtube_video(url)
                video_file = FSInputFile(video_file_path)
                await callback.message.answer_video(video_file)
                os.remove(video_file_path)
                if con_answer1.message_id:
                    await callback.bot.edit_message_text(
                        text="✅",
                        chat_id=callback.message.chat.id,
                        message_id=con_answer1.message_id
                    )
            except Exception:
                await callback.message.answer("Error: Error: Failed to convert video!")
        elif format_type == 'mp3':
            con_answer = await callback.message.answer("Converting video to MP3, please wait...")
            await state.update_data(con_answer_id=con_answer.message_id)
            try:
                audio_file_path = download_youtube_audio(url)
                audio_file = FSInputFile(audio_file_path)
                await callback.message.answer_audio(audio_file)
                os.remove(audio_file_path)
                if con_answer.message_id:
                    await callback.bot.edit_message_text(
                        text="✅",
                        chat_id=callback.message.chat.id,
                        message_id=con_answer.message_id
                    )
            except Exception:
                await callback.message.answer("Error: Failed to convert video!")

        if reply_message_id:
            try:
                await callback.bot.delete_message(chat_id=callback.message.chat.id, message_id=reply_message_id)
            except Exception:
                print("Error! Can't delete message!")

        await state.clear()
    else:
        await callback.message.answer("Please send the YouTube video link first.")
