from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


async def choice_button():
    keyboard = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text='mp4(Video🎥)', callback_data='mp4'),
                                                     InlineKeyboardButton(text='mp3(Audio🎧)', callback_data='mp3')]])
    return keyboard