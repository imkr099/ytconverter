import os
import random

from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import CommandStart, Command
from aiogram.types import FSInputFile
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from aiogram.types.dice import DiceEmoji

from app.database import requests as rq
from app.functions import (clean_youtube_url, get_available_qualities, download_youtube_audio,
                           download_youtube_video, download_spotify_track)
from app.keyboards import choice_button, create_quality_buttons


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
    await message.answer('Приветствую!\nПоделитесь сссылкой YouTube и я конвертирую его в  \nАудио или Видео♻️')


@router.message(Command('dice'))
async def send_dice(message: Message):
    dice_emojis = [
        DiceEmoji.DICE,
        DiceEmoji.DART,
        DiceEmoji.BASKETBALL,
        DiceEmoji.FOOTBALL,
        DiceEmoji.SLOT_MACHINE,
        DiceEmoji.BOWLING
    ]
    random_dice = random.choice(dice_emojis)
    await message.answer_dice(emoji=random_dice)


@router.message(F.text.contains('youtu'))
async def handle_youtube_link(message: Message, state: FSMContext):
    url = message.text
    clean_url = clean_youtube_url(url)
    await state.set_state(UserStates.waiting_for_format)
    await state.update_data(url=clean_url)
    reply_message = await message.reply("Выберите формат конвертации:",
                                        reply_markup=await choice_button())
    await state.update_data(reply_message_id=reply_message.message_id)


@router.callback_query(F.data.in_(['mp4', 'mp3']))
async def process_format_callback(callback: CallbackQuery, state: FSMContext):
    format_type = callback.data
    await callback.answer()
    await state.update_data(format_type=format_type)

    if format_type == 'mp4':
        user_data = await state.get_data()
        url = user_data.get('url')
        qualities = await get_available_qualities(url)
        quality_buttons = await create_quality_buttons(qualities)
        await state.set_state(UserStates.waiting_for_quality)
        await callback.message.edit_text("Выберите качество видео:", reply_markup=quality_buttons)

    elif format_type == 'mp3':
        user_data = await state.get_data()
        url = user_data.get('url')
        await convert_and_send_audio(callback, state, url)


async def convert_and_send_audio(callback: CallbackQuery, state: FSMContext, url: str):
    con_answer = await callback.message.answer(text="Конвертируем в MP3, пожалуйста подождите...⏳")
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
        await callback.message.answer(f"Ошибка: Не удалось конвертировать аудио! {str(e)}")
        os.remove(audio_file_path)


@router.callback_query(F.data.regexp(r'\d+p'))
async def process_quality_callback(callback: CallbackQuery, state: FSMContext):
    quality = callback.data
    await callback.answer()

    user_data = await state.get_data()
    url = user_data.get('url')

    if not url:
        await callback.message.answer("Ошибка: Нужна правильная ссылка")
        return

    con_answer = await callback.message.answer(f"Загружаем видео в {quality}, пожалуйста подождите...⏳")
    await state.update_data(con_answer_id=con_answer.message_id)
    reply_message_id = user_data.get('reply_message_id')

    if reply_message_id:
        try:
            await callback.bot.delete_message(chat_id=callback.message.chat.id, message_id=reply_message_id)
        except Exception as e:
            print(f"Ошибка удаления сообщения: {e}")
    video_file_path = None
    try:
        video_file_path = await download_youtube_video(url, quality)
        if video_file_path:
            video_file = FSInputFile(video_file_path)
            file_size = os.path.getsize(video_file_path)
            if file_size <= 44 * 1024 * 1024:  # 44 MB
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
            await callback.message.answer("Не удалось загрузить видео!")
            os.remove(video_file_path)
    except Exception as e:
        await callback.message.answer(f"Не удалось загрузить видео! {str(e)}")
        os.remove(video_file_path)


@router.message(F.text.startswith("https://open.spotify.com/track/"))
async def spotify_downloader(message: Message):
    url = message.text
    con_answer = await message.answer(text="Загружаем музыку из Spotify...⏳")

    try:
        audio_file_path = await download_spotify_track(url)
        if not os.path.exists(audio_file_path):
            raise Exception(f"Файл {audio_file_path} отсутствует")
        audio_file = FSInputFile(audio_file_path)
        await message.answer_audio(audio_file)
        os.remove(audio_file_path)
        await con_answer.edit_text("✅")
    except Exception as e:
        await message.answer(f"{str(e)}")
        if 'audio_file_path' in locals() and os.path.exists(audio_file_path):
            os.remove(audio_file_path)


@router.callback_query(F.data == 'back')
async def return_to_back(callback: CallbackQuery, state: FSMContext):
    await state.set_state(UserStates.waiting_for_format)

    await callback.message.edit_text(
        text='Выберите формат конвертации:',
        reply_markup=await choice_button()
    )


@router.callback_query(F.data == 'cancel')
async def cancel(callback: CallbackQuery):
    await callback.message.delete()