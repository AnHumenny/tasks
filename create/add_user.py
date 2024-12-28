#первичнное наполнение Users
import asyncio
import hashlib
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from dotenv import load_dotenv
from shemas.database import engine, DUser


load_dotenv()


def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()


async def create_user(date_created, login, name, post, status, describe, password):
    date_created = datetime.strptime(date_created, '%Y-%m-%d')
    hashed_password = hash_password(password)  # Hash the password
    async with AsyncSession(engine) as session:
        async with session.begin():

            result = await session.execute(select(DUser).where(DUser.login == login))
            existing_user = result.scalars().first()
            if existing_user:
                print(f"User  with login '{login}' already exists.")
                return

            new_user = DUser(
                date_created=date_created,
                login=login,
                name=name,
                post=post,
                status=status,
                describe=describe,
                password=hashed_password
            )
            session.add(new_user)
            await session.commit()


async def main():
    date_created = '2024-12-22'
    login = '2'
    name = '2'
    post = 'post'
    status = 'user'
    describe = 'describe'
    password = '123'
    await create_user(date_created, login, name, post, status, describe, password)


if __name__ == "__main__":
    asyncio.run(main())

