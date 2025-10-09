from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, ReplyKeyboardRemove
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from aiogram.filters import Command
import asyncio

from services.utils import generate_quiz, answer_isright
from bot_handlers.start import show_start_buttons
import database.db as db
from services.utils import show_loading_animation
from keyboards.inline import levels_inline_markup, continue_markup, return_to_main_markup
from keyboards.reply import get_subjects_markup
from middlewares.middlewares import AdminStatsMiddleware
import states.states as states






quiz_router = Router()

quiz_router.message.middleware(AdminStatsMiddleware())


@quiz_router.message(Command('quiz'))
@quiz_router.message(F.text == '📚 Начать викторину')
async def first_step(message: Message, state: FSMContext) -> None:
    """Start the quiz by asking the user to choose a subject."""
    await state.set_state(states.QuizSettingsState.subject)
    subjects_markup = get_subjects_markup()
    await message.answer('Выберите предмет:', reply_markup=subjects_markup)


@quiz_router.message(states.QuizSettingsState.subject)
async def choose_subject(message: Message, state: FSMContext) -> None:
    """Handle the subject choice and ask for difficulty level."""
    await message.answer("✅ Предмет выбран!", reply_markup=ReplyKeyboardRemove())
    await state.update_data(subject=message.text.strip().lower())
    await state.set_state(states.QuizSettingsState.level)
    await message.answer('Выберите уровень сложности:', reply_markup=levels_inline_markup, )


@quiz_router.callback_query(F.data.startswith('level_'))
async def choose_level_and_start_quiz(callback: CallbackQuery, state: FSMContext) -> None:
    """Handle the level choice and start the quiz."""
    level_map = {
        'level_easy': '🔰 Лёгкий',
        'level_medium': '⚖️ Средний',
        'level_hard': '🔥 Сложный'
    }

    level_key = callback.data
    level_text = level_map.get(level_key)

    if not level_text:
        await callback.answer("Некорректный выбор.")
        return

    await state.update_data(level=level_text)
    data = await state.get_data()

    subject = data.get('subject')
    level = data.get('level')

    await callback.message.edit_text(
        f"✅ Предмет: {subject}\n"
        f"📊 Уровень сложности: {level}\n"
        f"Данные сохранены. Готово к началу викторины!"
    )

    await callback.answer('Мы начинаем!')
    await start_quiz(callback, state)


async def start_quiz(callback: CallbackQuery, state: FSMContext) -> None:
    """Generate the quiz and send the first question."""
    data = await state.get_data()
    subject = data.get('subject')
    level = data.get('level')

    await callback.bot.send_chat_action(callback.message.chat.id, 'typing')

    task = asyncio.create_task(generate_quiz(subject, level))
    try:
        quiz = await show_loading_animation(callback.message, task)
    except Exception as e:
        await callback.message.answer('Ошибка.', reply_markup=return_to_main_markup)
        await state.clear()
        return

    if not quiz or len(quiz) != 10 or not all(isinstance(q, list) and len(q) == 4 for q in quiz):
        await callback.message.answer("❌ Не удалось сгенерировать викторину. Попробуйте снова позже.", reply_markup=return_to_main_markup)
        await state.clear()
        return

    await state.update_data(quiz=quiz)

    message_question = f"Вопрос №1.\n\n {quiz[0][0]}"
    keyboard_question = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=str(ans),
                    callback_data=f'answer_0:{str(a).lower()}',

                )
            ] for a, ans in quiz[0][1].items()
        ]
    )

    await state.set_state(states.QuizState.current_question)
    await callback.message.answer(message_question, reply_markup=keyboard_question)


@quiz_router.callback_query(F.data.startswith('answer_'), states.QuizState.current_question)
async def check_answer(callback: CallbackQuery, state: FSMContext) -> None:
    """Check the user's answer and provide feedback."""
    answer_num, answer = callback.data.replace('answer_', '').split(':')

    data = await state.get_data()
    quiz = data.get('quiz')

    answer_num, answer = int(answer_num), answer.strip().lower()
    if not quiz or answer_num >= len(quiz):
        await callback.answer("⚠️ Викторина уже завершена. Начните новую из меню.")
        return
    if answer_isright(answer_num, answer, quiz):
        data = await state.get_data()
        right_answers = data.get('right_answers', 0) + 1
        await state.update_data(right_answers=right_answers, current_question=answer_num)
        await callback.message.edit_text("✅ Правильно!", reply_markup=None)

    else:
        correct_answer = quiz[answer_num][2]
        explanation = quiz[answer_num][3]
        await state.update_data(current_question=answer_num)
        await callback.message.edit_text(
            f"❌ Неправильно!\n\n"
            f"Правильный ответ: {correct_answer}\n"
            f"Объяснение: {explanation}",
            reply_markup=None
        )

    if answer_num == 9:
        await finish_quiz(callback, state)
        return

    else:
        await callback.message.answer("Нажмите 'Следующий вопрос', чтобы продолжить.", reply_markup=continue_markup)



@quiz_router.callback_query(F.data == 'next_qst', states.QuizState.current_question)
async def next_question(callback: CallbackQuery, state: FSMContext) -> None:
    """Send the next question or finish the quiz."""
    data = await state.get_data()
    quiz = data.get('quiz')

    if not quiz:
        await callback.answer("⚠️ Викторина уже завершена. Начните новую из меню.")
        return

    current_qst_num = data.get('current_question', 0)

    if current_qst_num >= 9:
        await finish_quiz(callback, state)
        return

    next_qst_num = current_qst_num + 1

    if next_qst_num < 10:
        message_question = f"Вопрос №{next_qst_num + 1}.\n\n {quiz[next_qst_num][0]}"
        keyboard_question = InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text=str(ans),
                        callback_data=f'answer_{next_qst_num}:{str(a).lower()}'
                    )
                ] for a, ans in quiz[next_qst_num][1].items()
            ]
        )
        await state.update_data(current_question=next_qst_num)
        await callback.message.answer(message_question, reply_markup=keyboard_question)
    else:
        await finish_quiz(callback, state)


@quiz_router.callback_query(F.data == 'main_menu')
async def return_to_main(callback: CallbackQuery) -> None:
    """Return to the main menu."""
    await show_start_buttons(callback.message)


@quiz_router.callback_query(F.data == 'next_quiz')
async def restart_quiz(callback: CallbackQuery, state: FSMContext) -> None:
    """Restart the quiz process."""
    await state.clear()
    await first_step(callback.message, state)



async def finish_quiz(callback: CallbackQuery, state: FSMContext) -> None:
    """Вывод финального результата и очистка состояния."""
    data = await state.get_data()
    right_answers = data.get('right_answers', 0)
    subject = data.get('subject', 'unknown')

    await callback.message.answer(
        f"🏁 Викторина завершена!\n\n"
        f"Ваш результат: {right_answers}/10 правильных ответов.",
        reply_markup=return_to_main_markup
    )
    db.save_stats(callback.message.chat.id, right_answers, subject)
    db.increment_admin_stat(chat_id=callback.message.chat.id, stat_field="quizzes_taken", increment=1)
    db.increment_admin_stat(chat_id=callback.message.chat.id, stat_field="total_score", increment=right_answers)
    await state.clear()
