from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


async def choice_button():
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text='mp4(Video🎥)', callback_data='mp4'),
         InlineKeyboardButton(text='mp3(Audio🎧)', callback_data='mp3')],
        [InlineKeyboardButton(text='Отмена❌', callback_data='cancel')]
    ])
    return keyboard


async def create_quality_buttons(qualities):
    keyboard = InlineKeyboardMarkup(inline_keyboard=[])
    for quality in qualities:
        keyboard.inline_keyboard.append([InlineKeyboardButton(text=quality, callback_data=quality)])
    keyboard.inline_keyboard.append([InlineKeyboardButton(text='◀️Назад', callback_data='back')])
    return keyboard
