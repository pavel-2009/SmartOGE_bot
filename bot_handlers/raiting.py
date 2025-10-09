from aiogram import types, Router, F

from database.db import get_raiting

raiting_router = Router()


@raiting_router.message(F.text == "🏆 Рейтинг")
async def raiting_handler(message: types.Message) -> None:
    """Handle the '🏆 Рейтинг' command."""

    raiting = get_raiting()
    if raiting:
        text = "🏆 <b>Рейтинг пользователей:</b>\n\n"
        for idx, (user, score) in enumerate(raiting, start=1):
            text += f"{idx}. {user}: {score:.2f}\n"
        await message.answer(text, parse_mode="HTML")

    else:
        await message.answer("Рейтинг недоступен в данный момент.")
