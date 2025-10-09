from aiogram import Router, F
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton
from aiogram.filters import CommandStart, Command
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext

import database.db as db
from keyboards.reply import start_keyboard
from .admin.start import IsNotAdmin
import states.states as states

start_router = Router()




@start_router.message(CommandStart(), IsNotAdmin())
async def cmd_start(message: Message, state: FSMContext) -> None:
    """Handle the /start command."""
    await message.answer(
        '👋 <b>Привет!</b> Я — <b>Умный репетитор</b>, твой помощник в подготовке к ОГЭ. \n\n'
        '📚 Вместе мы разберёмся в самых сложных темах, потренируемся на заданиях и узнаем полезные советы,\n\n'
        'чтобы ты <b>уверенно сдал экзамен</b>.',
        parse_mode='html'
    )

    
    if db.is_registered(message):
        await show_start_buttons(message)
    else:
        await message.answer('Пожалуйста, введите ваше имя:')
        await state.set_state(states.Reg.name)


@start_router.message(states.Reg.name)
async def process_name(message: Message, state: FSMContext) -> None:
    """Process the user's name."""
    text = message.text.strip()

    await state.update_data({'name': text})
    await message.answer('Введите вашу фамилию.')
    await state.set_state(states.Reg.last_name)


@start_router.message(states.Reg.last_name)
async def process_lastname(message: Message, state: FSMContext) -> None:
    """Process the user's last name and complete registration."""
    text = message.text.strip()

    lastname = text
    await state.update_data({'last_name': lastname})

    data = await state.get_data()
    name = data['name']
    last_name = data['last_name']
    user_id = message.from_user.id

    saved_success = db.save_new_users(name, last_name, user_id)
    await state.clear()

    if saved_success:
        await message.answer('Вы успешно зарегистрированы!')
        await show_start_buttons(message)
    else:
        await message.answer('Произошла ошибка при регистрации. Пожалуйста, попробуйте ещё раз позже.')


async def show_start_buttons(message: Message) -> None:
    """Show start buttons to the user."""
    await message.answer('Готов начать? Давай разбираться вместе! 🚀', reply_markup=start_keyboard)


@start_router.message(F.text == '')
async def handle_empty_message(message: Message) -> None:
    """Handle empty messages."""
    await message.answer('Пожалуйста, введите корректное сообщение или выберите одну из доступных опций, используя кнопки ниже.', reply_markup=start_keyboard)


@start_router.message
async def handle_other_messages(message: Message) -> None:
    """Handle other messages."""
    await message.answer('Пожалуйста, выберите одну из доступных опций, используя кнопки ниже.', reply_markup=start_keyboard)


@start_router.message(Command('help'), IsNotAdmin())
@start_router.message(F.text == '❓ Помощь')
async def help_handler(message: Message) -> None:
    """Handle the '❓ Помощь' command."""
    help_text = (
        "Вот список доступных команд и функций бота:\n\n"
        "📚 <b>Начать викторину</b> - Начать тренировочную викторину по различным темам.\n"
        "📈 <b>Моя статистика</b> - Просмотреть вашу текущую статистику и прогресс.\n"
        "🏆 <b>Рейтинг</b> - Посмотреть рейтинг пользователей по набранным баллам.\n"
        "❓ <b>Помощь</b> - Показать это сообщение помощи.\n\n"
        "Если у вас есть вопросы или нужна дополнительная помощь, не стесняйтесь обращаться!"
    )
    await message.answer(help_text, parse_mode="HTML")
