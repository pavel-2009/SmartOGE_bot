from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

import database.db as db


def get_subjects_markup() -> list:
    subjects = db.get_subjects()

    subjects_markup = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=subject[0].upper())] for subject in subjects
        ],
        resize_keyboard=True,
        input_field_placeholder='📚 Выберите предмет:'
    )

    return subjects_markup

start_keyboard = ReplyKeyboardMarkup(keyboard=[
    [KeyboardButton(text='📚 Начать викторину'),
    KeyboardButton(text='📈 Моя статистика')],
    [KeyboardButton(text='🏆 Рейтинг'), KeyboardButton(text='❓ Помощь')]
], resize_keyboard=True)


settings_markup = ReplyKeyboardMarkup(
        keyboard=[  
            [KeyboardButton(text='1. Управление пользователями')],
            [KeyboardButton(text='2. Настройки викторины')],
            [KeyboardButton(text='🔙 Назад')]
        ],
        resize_keyboard=True
    )

admin_buttons = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text='📊 Статистика пользователей')],
            [KeyboardButton(text='🏆 Рейтинг')],
            [KeyboardButton(text='❓ Помощь')],
            [KeyboardButton(text='⚙️ Настройки')]
        ],
        resize_keyboard=True
    )