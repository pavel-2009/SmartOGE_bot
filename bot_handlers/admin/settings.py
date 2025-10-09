from aiogram import F, Router
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton
from aiogram.fsm.context import FSMContext

from database import db
from keyboards.reply import settings_markup, admin_buttons
import states.states as states

admin_settings_router = Router()




@admin_settings_router.message(F.text == '⚙️ Настройки')
async def admin_settings(message: Message) -> None:
    """Provide settings options for admin users."""
    text = """
Виды настроек:
1. Управление пользователями 
2. Настройки викторины
3. Настройки уведомлений
4. Настройки безопасности."""
    
    await message.answer(text, reply_markup=settings_markup)



@admin_settings_router.message(F.text == '🔙 Назад')
async def back_to_admin_menu(message: Message) -> None:
    """Return to the main admin menu."""
    await message.answer('Вы вернулись в главное меню администратора.', reply_markup=admin_buttons)



@admin_settings_router.message(F.text == '1. Управление пользователями')
async def handle_settings_1(message: Message) -> None:
    """Handle user management settings."""
    users = db.get_all_users()

    await message.answer(f"Список всех пользователей:")

    for user in users:
        user_id, name, lastname, chat_id, statistics = user

        markup = InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text='Удалить пользователя', callback_data=f'delete_user_{user_id}')]
            ]
        )

        await message.answer(f"ID: {user_id}, \nИмя: {name}, \nФамилия: {lastname}, \nChat ID: {chat_id}", reply_markup=markup)


@admin_settings_router.callback_query(F.data.startswith('delete_user_'))
async def delete_user_callback(callback_query, state: FSMContext) -> None:
    """Handle user deletion."""
    user_id = int(callback_query.data.split('_')[-1])
    db.delete_user(user_id)
    await callback_query.message.answer(f"Пользователь с ID {user_id} был удален.", reply_markup=admin_buttons)
    await callback_query.answer()



@admin_settings_router.message(F.text == '2. Настройки викторины')
async def handle_settings_2(message: Message) -> None:
    """Handle quiz settings."""
    text = "Настройки викторины:\n1. Добавить/Удалить предметы"
    markup = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text='1. Добавить/Удалить предметы')],
            [KeyboardButton(text='🔙 Назад')]
        ],
        resize_keyboard=True
    )
    await message.answer(text, reply_markup=markup)



@admin_settings_router.message(F.text == '1. Добавить/Удалить предметы')
async def manage_quiz_subjects(message: Message) -> None:
    """Manage quiz subjects."""
    subjects = db.get_subjects()
    subject_list = "\n".join([f"- {subject[0].upper()}" for subject in subjects])
    markup = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text='Добавить предмет')],
            [KeyboardButton(text='Удалить предмет')],
            [KeyboardButton(text='🔙 Назад')]
        ],
        resize_keyboard=True
    )
    await message.answer(f"Текущие предметы викторины:\n{subject_list}", reply_markup=markup)



@admin_settings_router.message(F.text == 'Добавить предмет')
async def add_quiz_subject_prompt(message: Message, state: FSMContext) -> None:
    """Prompt admin to enter a new quiz subject."""
    await message.answer("Введите название нового предмета для викторины:")
    await state.set_state(states.NewSubjectState.new_subject)



@admin_settings_router.message(states.NewSubjectState.new_subject)
async def process_add_quiz_subject(message: Message, state: FSMContext) -> None:
    """Process adding a new quiz subject."""
    new_subject = message.text.strip()
    if new_subject in db.get_subjects():
        await message.answer("Этот предмет уже существует.")
    else:
        db.add_subject(new_subject)
        await message.answer(f"Предмет '{new_subject}' успешно добавлен.")
    await state.clear()



@admin_settings_router.message(F.text == 'Удалить предмет')
async def delete_quiz_subject_prompt(message: Message, state: FSMContext) -> None:
    """Prompt admin to enter a quiz subject to delete."""
    await message.answer("Введите название предмета, который хотите удалить:")
    await state.set_state(states.DeleteSubjectState.subject)



@admin_settings_router.message(states.DeleteSubjectState.subject)
async def process_delete_quiz_subject(message: Message, state: FSMContext) -> None:
    """Process deleting a quiz subject."""
    subjects = [subject[0] for subject in db.get_subjects()]
    subject_to_delete = message.text.strip()
    if subject_to_delete not in subjects:
        await message.answer("Этот предмет не найден.")
    else:
        db.delete_subject(subject_to_delete)
        await message.answer(f"Предмет '{subject_to_delete}' успешно удален.")
        await state.clear()






