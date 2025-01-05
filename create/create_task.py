#тестовое наполнение Tasks
import asyncio
import hashlib
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from dotenv import load_dotenv
from shemas.database import engine, DTask


load_dotenv()


def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()


async def create_task(date_created, date_control, implementer, describe, priority):
    date_created = datetime.strptime(date_created, '%Y-%m-%d')
    date_control = datetime.strptime(date_control, '%Y-%m-%d')
    async with AsyncSession(engine) as session:
        async with session.begin():
            new_task = DTask(
                date_created=date_created,
                date_control=date_control,
                implementer=implementer,
                describe=describe,
                priority=priority
            )
            session.add(new_task)
            await session.commit()


async def main():
    date_created = '2024-12-23'
    date_control = '2024-12-28'
    implementer = 'Bob'
    describe = 'describe'
    priority = 'middle'
    await create_task(date_created, date_control, implementer, describe, priority)


if __name__ == "__main__":
    asyncio.run(main())

