from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
from yt_dlp import YoutubeDL


async def choice_button():
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text='mp4(Video🎥)', callback_data='mp4'),
         InlineKeyboardButton(text='mp3(Audio🎧)', callback_data='mp3')],
        [InlineKeyboardButton(text='Cancel❌', callback_data='cancel')]
    ])
    return keyboard


async def quality_button():
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="240p", callback_data="240p")],
        [InlineKeyboardButton(text="360p", callback_data="360p")],
        [InlineKeyboardButton(text="480p", callback_data="480p")],
        [InlineKeyboardButton(text="720p", callback_data="720p")],
        [InlineKeyboardButton(text="1080p", callback_data="1080p")],
        [InlineKeyboardButton(text="◀️Back", callback_data="back")]
    ])
    return keyboard


async def get_available_qualities(url):
    ydl_opts = {'quiet': True}
    with YoutubeDL(ydl_opts) as ydl:
        info_dict = ydl.extract_info(url, download=False)
        formats = info_dict.get('formats', [])
        qualities = sorted(set([f.get('height') for f in formats if f.get('height') and f.get('height') >= 144]))
        return [f"{quality}p" for quality in qualities]


async def create_quality_buttons(qualities):
    keyboard = InlineKeyboardMarkup(inline_keyboard=[])
    for quality in qualities:
        keyboard.inline_keyboard.append([InlineKeyboardButton(text=quality, callback_data=quality)])
    keyboard.inline_keyboard.append([InlineKeyboardButton(text='◀️Back', callback_data='back')])
    return keyboard


async def back_button():
    keyboard = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text='Back', callback_data='back')]])

    return keyboard
