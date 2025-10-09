from aiogram import BaseMiddleware, types

from database import db

# Определяем список админов прямо здесь (или импортируйте из config.py)
ADMIN_IDS = {1708398974}  # замените на ваши ID

def is_admin(user_id: int) -> bool:
    return user_id in ADMIN_IDS

class AdminStatsMiddleware(BaseMiddleware):
    async def __call__(self, handler, event, data):
        message = event
        if message and message.from_user:
            user_id = message.from_user.id
            if is_admin(user_id):
                db.increment_admin_stat(chat_id=user_id, stat_field="commands_used", increment=1)
        return await handler(event, data)
    
class IsAdminMiddleware(BaseMiddleware):
    async def __call__(self, handler, event, data):
        message = event
        if message and message.from_user:
            user_id = message.from_user.id
            if not is_admin(user_id):
                await message.answer("У вас нет прав для выполнения этой команды.")
                return
        return await handler(event, data)

