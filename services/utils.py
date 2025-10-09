import aiohttp
import json
import ast
import asyncio
from aiogram import types
from dotenv import load_dotenv
import os
import logging

load_dotenv()
logger = logging.getLogger(__name__)


async def generate_quiz(subject: str, level: str) -> list | None:
    """Асинхронная генерация викторины через OpenRouter API."""
    API_KEY = os.getenv("OPENROUTER_API_KEY")
    if not API_KEY:
        raise ValueError("OPENROUTER_API_KEY не установлен в переменные окружения.")

    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json",
    }

    payload = {
        "model": "mistralai/mixtral-8x7b-instruct",
        "messages": [
            {
                "role": "user",
                "content": f"""
Сгенерируй 10 экзаменационных вопросов для подготовки к ОГЭ по предмету "{subject}" уровня сложности "{level}".

Каждый вопрос — список из 4 элементов:
[
"Вопрос",
{{
    "A": "...",
    "B": "...",
    "C": "...",
    "D": "..."
}},
"Правильный вариант (A|B|C|D)",
"Подробное объяснение"
]

Ответ: только **валидный Python-список из 10 таких списков**. Без заголовков, markdown и комментариев.
"""
            }
        ]
    }

    for attempt in range(10):
        try:
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=30)) as session, session.post(url, headers=headers, json=payload) as response:
                if response.status != 200:
                    text = await response.text()
                    logger.warning(f"[{attempt+1}/10] API {response.status}: {text[:150]}")
                    continue

                result = await response.json()
                content = result.get("choices", [{}])[0].get("message", {}).get("content", "").strip()

            if not content:
                logger.warning(f"[{attempt+1}/10] Пустой ответ от API.")
                continue

            try:
                # Сначала пробуем JSON
                quiz_list = json.loads(content)
            except Exception:
                try:
                    quiz_list = ast.literal_eval(content)
                except Exception as parse_err:
                    logger.warning(f"[{attempt+1}/10] Ошибка парсинга ответа: {parse_err}")
                    continue

            if (
                isinstance(quiz_list, list)
                and len(quiz_list) == 10
                and all(
                    isinstance(q, list)
                    and len(q) == 4
                    and isinstance(q[0], str)
                    and isinstance(q[1], dict)
                    and isinstance(q[2], str)
                    and isinstance(q[3], str)
                    for q in quiz_list
                )
            ):
                logger.info(f"✅ Квиз успешно сгенерирован на {attempt+1}-й попытке.")
                return quiz_list
            else:
                logger.warning(f"[{attempt+1}/10] Ответ не соответствует ожидаемому формату.")
                continue

        except aiohttp.ClientError as e:
            logger.error(f"[{attempt+1}/10] Ошибка сети: {e}")
            await asyncio.sleep(1)
            continue
        except Exception as e:
            logger.error(f"[{attempt+1}/10] Неизвестная ошибка: {e}", exc_info=True)
            await asyncio.sleep(1)
            continue

    logger.error("❌ Не удалось получить валидный список от ИИ после 10 попыток.")
    return None


def answer_isright(answer_num: int, answer: str, quiz: list) -> bool:
    """Проверяет правильность ответа пользователя."""
    return quiz[answer_num][2].strip().lower() == answer.strip().lower()


async def show_loading_animation(message: types.Message, task: asyncio.Task) -> any:
    """Показывает анимацию загрузки, пока выполняется задача."""
    loading_text = "⏳ Генерируется квиз"
    dots = ["", ".", "..", "..."]
    i = 0

    msg = await message.answer(f"<b>{loading_text}{dots[i]}</b>", parse_mode="HTML")

    while not task.done():
        i = (i + 1) % len(dots)
        try:
            await msg.edit_text(f"<b>{loading_text}{dots[i]}</b>", parse_mode="HTML")
        except Exception:
            pass
        await asyncio.sleep(0.3)

    return await task
