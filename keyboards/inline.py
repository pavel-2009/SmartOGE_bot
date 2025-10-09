from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton



levels_inline_markup = InlineKeyboardMarkup(
    inline_keyboard=[
        [
            InlineKeyboardButton(text='🔰 Лёгкий', callback_data='level_easy'),
            InlineKeyboardButton(
                text='⚖️ Средний', callback_data='level_medium'),
            InlineKeyboardButton(text='🔥 Сложный', callback_data='level_hard')
        ]
    ]
)

continue_markup = InlineKeyboardMarkup(
    inline_keyboard=[
        [
            InlineKeyboardButton(text='Следующий вопрос', callback_data='next_qst')
        ]
    ]
)

return_to_main_markup = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text='Еще викторина', callback_data='next_quiz'),
        InlineKeyboardButton(text='Вернуться в главное меню', callback_data='main_menu')]
    ]
)