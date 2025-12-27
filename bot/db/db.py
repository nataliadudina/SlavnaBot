import logging

import aiosqlite
import sqlite3

from config import config

logger = logging.getLogger(__name__)


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
