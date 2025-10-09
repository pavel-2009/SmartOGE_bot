from aiogram.types import Message
import sqlite3
import os
import datetime
import json
import logging

logger = logging.getLogger(__name__)

db_path = os.path.join(os.path.dirname(
            os.path.abspath(__file__)), 'db.sqlite3')


def connect_to_db(query: str, params=(), fetch=False) -> list | bool | None:
    """Connect to the SQLite database and execute a query."""
    create_db()
    try:
        with sqlite3.connect(db_path, timeout=20) as conn:
            cursor = conn.execute(query, params)
            if fetch:
                return cursor.fetchall()
            else:
                conn.commit()
                return True
    except sqlite3.Error as e:
        logging.error(f"Database error: {e}")
        return None


def is_registered(message: Message) -> bool:
    """Check if a user is registered in the database."""
    data = connect_to_db(
        "SELECT * FROM users WHERE chat_id = ?",
        (message.chat.id,),
        fetch=True
    )
    return bool(data)


def save_new_users(name: str, lastname: str, user_id: int) -> bool | None:
    """Save new user information to the database."""
    try:
        return connect_to_db(
            "INSERT INTO users (name, lastname, chat_id) VALUES (?, ?, ?)",
            (name, lastname, user_id),
            fetch=False
        )
    except Exception as e:
        logging.error(e)
        return None


def get_stats(chat_id: int) -> list | None:
    """Retrieve user statistics from the database."""
    try:
        return connect_to_db(
            "SELECT statistics FROM users WHERE chat_id=?",
            (chat_id,),
            fetch=True
        )
    except Exception as e:
        logging.info(e)
        return None


def save_stats(chat_id: int, score: int, subject: str) -> bool | None:
    """Save user statistics to the database."""
    try:
        stats_row = get_stats(chat_id)
        subject = subject.lower()
        today = datetime.date.today()
        month = str(today.month)
        day = str(today.day)
        time_now = str(datetime.datetime.now().time())

        if stats_row and stats_row[0] and stats_row[0][0]:
            current_stats = json.loads(stats_row[0][0])
        else:
            current_stats = {}

        if subject not in current_stats:
            current_stats[subject] = {}

        subject_stats = current_stats[subject]

        if month not in subject_stats:
            subject_stats[month] = {}
        if day not in subject_stats[month]:
            subject_stats[month][day] = {}

        subject_stats[month][day][time_now] = score
        current_stats[subject] = subject_stats

        update_raiting(chat_id, score)

        return connect_to_db(
            "UPDATE users SET statistics = ? WHERE chat_id = ?",
            (json.dumps(current_stats), chat_id),
            fetch=False
        )
    except Exception as e:
        logging.error(e)
        return None


def create_db() -> None:
    """Create the database and users table if they do not exist."""
    with sqlite3.connect(db_path) as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT,
                lastname TEXT,
                chat_id INTEGER UNIQUE,
                statistics TEXT
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS raiting (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            chat_id INTEGER UNIQUE,
            total_score INTEGER DEFAULT 0,
            attempts INTEGER DEFAULT 0,
            avg_score REAL DEFAULT 0
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS admin_stats (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                chat_id INTEGER UNIQUE,
                commands_used INTEGER DEFAULT 0,
                quizzes_taken INTEGER DEFAULT 0,
                total_score INTEGER DEFAULT 0
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS subjects (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                subject TEXT UNIQUE
            )
        """)
        conn.execute("""
                    INSERT OR IGNORE INTO subjects (subject) VALUES
                    ('математика'),
                    ('русский язык'),
                    ('физика'),
                    ('биология'),
                    ('история'),
                    ('обществознание'),
                    ('география'),
                    ('литература'),
                    ('английский язык')
                    """)
        conn.commit()


def update_raiting(chat_id: int, score: int) -> bool | None:
    try:
        row = connect_to_db("SELECT total_score, attempts FROM raiting WHERE chat_id = ?", (chat_id,), fetch=True)
        if row and len(row) > 0:
            total, attempts = row[0]
            total = (total or 0) + score
            attempts = (attempts or 0) + 1
            avg = total / attempts
            return connect_to_db(
                "UPDATE raiting SET total_score = ?, attempts = ?, avg_score = ? WHERE chat_id = ?",
                (total, attempts, avg, chat_id),
                fetch=False
            )
        else:
            return connect_to_db(
                "INSERT INTO raiting (chat_id, total_score, attempts, avg_score) VALUES (?, ?, ?, ?)",
                (chat_id, score, 1, score),
                fetch=False
            )
    except Exception as e:
        logger.error("Failed to update rating: %s", e)
        return None


def get_raiting() -> list | None:
    """Retrieve the rating list from the database."""
    try:
        return connect_to_db(
            "SELECT chat_id, scores FROM raiting ORDER BY scores DESC LIMIT 10",
            fetch=True
        )
    except Exception as e:
        logging.error(e)
        return None
    
def increment_admin_stat(chat_id: int, stat_field: str, increment: int = 1) -> bool | None:
    """Increment a specific admin statistic field for a given chat_id."""
    valid_fields = {"commands_used", "quizzes_taken", "total_score"}
    if stat_field not in valid_fields:
        logging.error(f"Invalid stat field: {stat_field}")
        return None

    try:
        existing = connect_to_db(
            f"SELECT {stat_field} FROM admin_stats WHERE chat_id = ?",
            (chat_id,),
            fetch=True
        )
        if existing:
            new_value = existing[0][0] + increment
            return connect_to_db(
                f"UPDATE admin_stats SET {stat_field} = ? WHERE chat_id = ?",
                (new_value, chat_id),
                fetch=False
            )
        else:
            initial_values = {field: 0 for field in valid_fields}
            initial_values[stat_field] = increment
            return connect_to_db(
                "INSERT INTO admin_stats (chat_id, commands_used, quizzes_taken, total_score) VALUES (?, ?, ?, ?)",
                (chat_id, initial_values["commands_used"], initial_values["quizzes_taken"], initial_values["total_score"]),
                fetch=False
            )
    except Exception as e:
        logging.error(e)
        return None


def get_all_users() -> list | None:
    """Retrieve all users from the database."""
    try:
        return connect_to_db(
            "SELECT id, name, lastname, chat_id, statistics FROM users",
            fetch=True
        )
    except Exception as e:
        logging.error(e)
        return None
    
def delete_user(user_id: int) -> bool | None:
    """Delete a user from the database by their chat_id."""
    try:
        return connect_to_db(
            "DELETE FROM users WHERE chat_id = ?",
            (user_id,),
            fetch=False
        )
    except Exception as e:
        logging.error(e)
        return None


def get_subjects() -> list | None:
    """Retrieve all quiz subjects from the database."""
    try:
        return connect_to_db(
            "SELECT subject FROM subjects",
            fetch=True
        )
    except Exception as e:
        logging.error(e)
        return None
    
def add_subject(subject: str) -> bool | None:
    """Add a new subject to the database."""
    try:
        return connect_to_db(
            "INSERT INTO subjects (subject) VALUES (?)",
            (subject.lower(),),
            fetch=False
        )
    except Exception as e:
        logging.error(e)
        return None
    
def delete_subject(subject: str) -> bool | None:
    """Delete a subject from the database."""
    try:
        return connect_to_db(
            "DELETE FROM subjects WHERE subject = ?",
            (subject.lower(),),
            fetch=False
        )
    except Exception as e:
        logging.error(e)
        return None
