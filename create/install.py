
import asyncio
import hashlib
from datetime import datetime
import asyncpg
import pytz
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlalchemy import text
from shemas.database import DUser, DTutor, DPost, DTask
from dotenv import load_dotenv
import os
load_dotenv()

DB_HOST = os.getenv('DB_HOST')
DB_USER = os.getenv('DB_USER')
DB_PASSWORD = os.getenv('DB_PASSWORD')
DB_NAME = os.getenv('DB_NAME')
DB_PORT = os.getenv('DB_PORT')


engine_base = create_async_engine(
    f"postgresql+asyncpg://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/postgres",
    echo=True
)

engine = create_async_engine(f"postgresql+asyncpg://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}")


engine_table = create_async_engine(
    f"postgresql+asyncpg://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}",
    echo=True
)


start_session = async_sessionmaker(engine_base, expire_on_commit=False)
user_session = async_sessionmaker(engine_table, expire_on_commit=False)


async def check_database():
    async with start_session() as session:
        async with session.begin():
            result = await session.execute(text(f"""
                SELECT 1 FROM pg_database WHERE datname = :db_name
            """), {"db_name": DB_NAME})
            if result.scalar() is not None:
                print("какая то проблема")
            else:
                await create_database()


async def create_database():
    conn = await asyncpg.connect(user=DB_USER, password=DB_PASSWORD, host=DB_HOST, port=DB_PORT, database='postgres')
    try:
        await conn.execute(f"CREATE DATABASE {DB_NAME}")
    finally:
        await conn.close()
        await create_tables()


async def create_tables():
    async with engine_table.begin() as conn:
        await conn.run_sync(DTask.metadata.create_all)
        await conn.run_sync(DUser.metadata.create_all)
        await conn.run_sync(DPost.metadata.create_all)
        await conn.run_sync(DTutor.metadata.create_all)


def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()


async def create_user():
    async with user_session() as session:
        login = "admin"
        name = "Василий Пупкин"
        position = "Главный перец"
        describe = "рано обалдевший пупс"
        password = str("qwerty")
        date_time = datetime.now()
        date_time_str = date_time.strftime('%Y-%m-%dT%H:%M')
        naive_datetime_created = datetime.strptime(date_time_str, '%Y-%m-%dT%H:%M')
        local_tz = pytz.timezone('Europe/Moscow')
        date_created = local_tz.localize(naive_datetime_created)
        date_created_naive = date_created.replace(tzinfo=None)
        hashed_password = hash_password(password)
        superuser = DUser(
            date_created=date_created_naive,
            login=login,
            status='admin',
            name=name,
            post=position,
            describe=describe,
            password=hashed_password
        )
        session.add(superuser)
        await session.commit()


async def main():
    await check_database()
    await create_user()


asyncio.run(main())

