from aiogram import Router, F, types
from aiogram.types import Message
from aiogram.filters import Command
from database.db import get_stats
import json
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib import dates
import os
import datetime
import logging

from .admin.start import IsNotAdmin

stats_router = Router()


@stats_router.message(Command('stats'), IsNotAdmin())
@stats_router.message(F.text == '📈 Моя статистика')
async def show_stats(message: Message) -> None:
    """Show user statistics as a graph with separate lines for each subject."""
    stats = get_stats(message.chat.id)

    logging.info(f"Retrieved stats: {stats}")

    if not stats or not stats[0] or not stats[0][0]:
        await message.answer("У тебя пока нет сохранённой статистики 📭")
        return

    try:
        stats = json.loads(stats[0][0])
    except Exception:
        await message.answer("Ошибка при обработке статистики ⚠️")
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

    await message.answer_photo(types.FSInputFile(image_path), caption="Вот твоя статистика 📊")

    os.remove(image_path)


def preprocess_stats(stats: dict) -> pd.DataFrame:
    """Preprocess the stats dictionary into a DataFrame with subjects."""
    records = []
    current_year = datetime.date.today().year

    for subject, subject_stats in stats.items():
        for month, days in subject_stats.items():
            for day, times in days.items():
                if not times:
                    continue
                date_str = f"{current_year}-{str(month).zfill(2)}-{str(day).zfill(2)}"
                avg_score = sum(times.values()) / len(times)
                records.append({
                    "subject": subject,
                    "date": pd.to_datetime(date_str),
                    "value": avg_score
                })

    if not records:
        return pd.DataFrame(columns=["subject", "date", "value"])

    df = pd.DataFrame(records)
    df.sort_values(by=["subject", "date"], inplace=True)
    return df

