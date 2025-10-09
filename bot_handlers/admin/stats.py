from aiogram import Router, F
from aiogram import types
from aiogram.filters import Command
import pandas as pd
from matplotlib import dates
import matplotlib.pyplot as plt

import json
import os
import logging

from bot_handlers.admin.start import IsAdmin
from middlewares.middlewares import IsAdminMiddleware
import database.db as db
from bot_handlers.stats import preprocess_stats

admin_stats_router = Router()
admin_stats_router.message.middleware(IsAdminMiddleware())


@admin_stats_router.message(Command("stats"), IsAdmin())
@admin_stats_router.message(F.text == '📊 Статистика пользователей')
async def admin_stats(message: types.Message) -> None:
    """Handle the /stats command for admin users."""
    users = db.get_all_users()
    if users is None:
        await message.answer("Ошибка при получении данных из базы.")
        return

    for user in users:
        user_id, name, lastname, chat_id, stats_json = user
        logging.info(user)
        try:
            stats = json.loads(stats_json) if stats_json else {}
        except Exception as e:
            await message.answer("Ошибка при обработке статистики ⚠️")
            logging.error(e)
            return

        stats_table = preprocess_stats(stats)

        if stats_table.empty:
            await message.answer("Статистика пуста 📭")
            return

        fig, ax = plt.subplots(figsize=(10, 5))

        for subject, df_subj in stats_table.groupby("subject"):
            ax.plot(df_subj["date"], df_subj["value"], marker='o', label=subject)

        ax.set_xlim(stats_table["date"].min() - pd.Timedelta(days=1),
                    stats_table["date"].max() + pd.Timedelta(days=10))

        ax.set_title('Статистика по дням')
        ax.set_xlabel('Дата')
        ax.set_ylabel('Результат')
        ax.set_ylim(0, 10)
        ax.grid(True, linestyle="--", alpha=0.7)
        ax.legend()
        ax.xaxis.set_major_locator(dates.DayLocator())
        fig.tight_layout()

        image_path = os.path.join(os.path.dirname(
            __file__), f"stats_{message.chat.id}.png")
        fig.savefig(image_path)
        plt.close(fig)

        await message.answer_photo(types.FSInputFile(image_path), caption=f"Статистика пользователя {name} {lastname} (ID: {chat_id}) 📊")
            
        if os.path.exists(image_path):
            os.remove(image_path)



