from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


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


async def back_button():
    keyboard = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text='Back', callback_data='back')]])

    return keyboard
