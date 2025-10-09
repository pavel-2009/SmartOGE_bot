from aiogram import Router, F
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton
from aiogram.filters import CommandStart, Command, BaseFilter
from bot_handlers.admin.settings import admin_settings
from middlewares.middlewares import AdminStatsMiddleware, IsAdminMiddleware


admin_router = Router()
admin_router.message.middleware(AdminStatsMiddleware())


class IsAdmin(BaseFilter):
    ADMIN_IDS = {1708398974} 

    @classmethod
    def is_admin(cls, user_id: int) -> bool:
        return user_id in cls.ADMIN_IDS
    
    async def __call__(self, message: Message) -> bool:
        return self.is_admin(message.from_user.id)
    
    @classmethod
    def add_admins(cls, new_admin_ids):
        new_admin_ids = cls.ADMIN_IDS.union(new_admin_ids)
        cls.ADMIN_IDS.update(new_admin_ids)

class IsNotAdmin(BaseFilter):
    async def __call__(self, message: Message) -> bool:
        return not IsAdmin.is_admin(message.from_user.id)
    

@admin_router.message(CommandStart(), IsAdmin())
async def admin_start(message: Message) -> None:
    """Handle the /start command for admin users."""
    await message.answer('Вы вошли как администратор.', reply_markup=ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text='📊 Статистика пользователей')],
            [KeyboardButton(text='🏆 Рейтинг')],
            [KeyboardButton(text='❓ Помощь')],
            [KeyboardButton(text='⚙️ Настройки')]
        ],
        resize_keyboard=True
    ))


@admin_router.message(Command("help"), IsAdmin())
@admin_router.message(F.text == '❓ Помощь')
async def admin_help(message: Message) -> None:
    """Provide help information for admin users."""
    help_text = (
        "Доступные команды для администратора:\n"
        "/start - Запуск бота\n"
        "/stats - Просмотр статистики пользователей\n"
        "/raiting - Просмотр рейтинга пользователей\n"
        "/help - Помощь по командам"
    )
    await message.answer(help_text)


@admin_router.message(F.text == '⚙️ Настройки')
async def admin_settings_entry(message: Message):
    """Entry point for admin settings from main admin menu."""
    await admin_settings(message)



