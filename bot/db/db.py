import logging

import aiosqlite

logger = logging.getLogger(__name__)


async def add_to_db(user_id: int, username: str) -> None:
    """
    Функция создания таблицы users и сохранения telegram id и username пользователей
    с генерацией даты добавления.
    """
    async with aiosqlite.connect('slavna.db') as db:
        await db.execute("""
        CREATE TABLE IF NOT EXISTS users (
        user_id BIGINT, 
        username VARCHAR(50), 
        role VARCHAR(5) DEFAULT 'user',
        date TEXT DEFAULT CURRENT_TIMESTAMP
        )
        """)

        # проверка, что пользователя ещё нет в бд
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
        # Уровень ERROR, чтобы пришло оповещение в тг о добавлении нового пользователя
        logger.error(f'User {username} with user id {user_id} has been added to db "users"')
        await db.commit()


async def update_user_role(user_id: int, role: str) -> None:
    """
    Обновляет роль пользователя в базе данных.
    """
    async with aiosqlite.connect('slavna.db') as db:
        await db.execute(
            "UPDATE users SET role = ? WHERE user_id = ?", (role, user_id)
        )
        await db.commit()
        logger.info(f'Updated role for user ID {user_id} to {role}')


async def get_user_role(user_id: int) -> str:
    """Функция для получения роли пользователя из базы данных."""
    async with aiosqlite.connect('slavna.db') as db:
        result = await db.execute("SELECT role FROM users WHERE user_id = ?", (user_id,))
        row = await result.fetchone()
        return row[0] if row else 'user'
