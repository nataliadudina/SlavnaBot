import logging
import sqlite3

import aiosqlite

from src.config import config

logger = logging.getLogger(__name__)


# =========================
# USERS
# =========================
def get_users() -> list:
    """Returns a list of user_ids for all users in the database."""
    conn = sqlite3.connect(config.db_path)
    cursor = conn.cursor()
    cursor.execute('SELECT user_id FROM users')
    users = [row[0] for row in cursor.fetchall()]
    conn.close()
    return users


async def add_to_db(user_id: int, username: str) -> None:
    """
    Creates the users table and stores the user's Telegram ID and username
    along with the addition date.
    """
    async with aiosqlite.connect(config.db_path) as db:
        await db.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id BIGINT, 
            username VARCHAR(50), 
            role VARCHAR(5) DEFAULT 'user',
            email VARCHAR(100),
            date TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # check that user hasn't been already added
        check_result = await db.execute(
            "SELECT COUNT(*) FROM users WHERE user_id = ?", (user_id,)
        )
        count_row = await check_result.fetchone()
        count = count_row[0]
        if count > 0:
            return

        await db.execute("INSERT INTO users (user_id, username) VALUES (?, ?)",
                         (user_id, username)
                         )
        # ERROR level to get notification about new user
        logger.error(f'User {username} with user id {user_id} has been added to db "users"')
        await db.commit()


async def update_user_role(user_id: int, role: str) -> None:
    """ Updates a user's role in the database. """
    async with aiosqlite.connect(config.db_path) as db:
        await db.execute(
            "UPDATE users SET role = ? WHERE user_id = ?", (role, user_id)
        )
        await db.commit()
        logger.info(f'Updated role for user ID {user_id} to {role}')


async def get_user_role(user_id: int) -> str:
    """ Retrieves a user's role from the database. """
    async with aiosqlite.connect(config.db_path) as db:
        result = await db.execute("SELECT role FROM users WHERE user_id = ?", (user_id,))
        row = await result.fetchone()
        return row[0] if row else 'user'


async def get_user_email(user_id) -> str | None:
    async with aiosqlite.connect(config.db_path) as db:
        async with db.execute(
            "SELECT email FROM users WHERE user_id = ?", (user_id,)
        ) as cursor:
            row = await cursor.fetchone()
            return row[0] if row and row[0] else None


# =========================
# TOURS
# =========================
async def add_tour_to_db(title: str, description: str, tour_type: str) -> bool:
    """
    Creates the tours table and (if not exists) and adds a new tour.
    """
    async with aiosqlite.connect(config.db_path) as db:
        await db.execute("""
        CREATE TABLE IF NOT EXISTS tours (
            tour_id INTEGER PRIMARY KEY AUTOINCREMENT,
            title VARCHAR(50) UNIQUE,
            description TEXT,
            tour_type VARCHAR(20) NOT NULL
        )
        """)

        try:
            await db.execute(
                "INSERT INTO tours (title, description, tour_type) VALUES (?, ?, ?)",
                (title, description, tour_type)
            )
        except aiosqlite.IntegrityError:
            return False

        # ERROR level to get notification about new excursion added
        logger.error(f'New excursion with title "{title}" has been added to db "tours"')
        await db.commit()
        return True


async def is_tour_title_exists(title: str, tour_type: str) -> bool:
    """ Checks whether a tour with the given title already exists."""
    async with aiosqlite.connect(config.db_path) as db:
        cursor = await db.execute(
            'SELECT 1 FROM tours WHERE title = ? AND tour_type = ? LIMIT 1',
            (title, tour_type),
        )
        row = await cursor.fetchone()
        return row is not None


async def get_all_tours() -> list[tuple[int, str]]:
    """ Returns list of all tours. """
    async with aiosqlite.connect(config.db_path) as db:
        cursor = await db.execute(
            'SELECT tour_id, title FROM tours ORDER BY title',
        )
        return await cursor.fetchall()


async def get_tours_by_type(tour_type: str) -> list[tuple[int, str]]:
    """ Returns list of (tour_id, title) for given tour type. """
    async with aiosqlite.connect(config.db_path) as db:
        cursor = await db.execute(
            'SELECT tour_id, title FROM tours WHERE tour_type = ? ORDER BY title',
            (tour_type,),
        )
        return await cursor.fetchall()


async def get_tour_by_id(tour_id: int) -> dict | None:
    """Returns tour data by id."""
    async with aiosqlite.connect(config.db_path) as db:
        cursor = await db.execute(
            'SELECT title, description FROM tours WHERE tour_id = ?',
            (tour_id,),
        )
        row = await cursor.fetchone()

        if not row:
            return None

        return {
            'title': row[0],
            'description': row[1],
        }


async def update_tour_title(tour_id: int, new_title: str):
    async with aiosqlite.connect(config.db_path) as db:
        await db.execute(
            'UPDATE tours SET title = ? WHERE tour_id = ?',
            (new_title, tour_id),
        )
        await db.commit()


async def update_tour(tour_id: int, new_description: str):
    async with aiosqlite.connect(config.db_path) as db:
        await db.execute(
            'UPDATE tours SET description = ? WHERE tour_id = ?',
            (new_description, tour_id),
        )
        await db.commit()


async def delete_tour_from_db(tour_id: int) -> None:
    async with aiosqlite.connect(config.db_path) as db:
        await db.execute(
            'DELETE FROM tours WHERE tour_id = ?',
            (tour_id,),
        )
        await db.commit()

