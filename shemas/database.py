from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from dotenv import load_dotenv
import os
load_dotenv()

engine = create_async_engine(f"postgresql+asyncpg://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}@"
                             f"{os.getenv('DB_HOST')}:{os.getenv('DB_PORT')}/{os.getenv('DB_NAME')}")

new_session = async_sessionmaker(engine, expire_on_commit=False)

class Model(DeclarativeBase):
    pass

class DTask(Model):
    __tablename__ = "Tasks"
    id = Column(Integer, primary_key=True, autoincrement=True)
    date_created = Column(DateTime(), nullable=False)
    date_control = Column(DateTime(), nullable=False)
    facilitator = Column(String(length=50), nullable=False)
    implementer = Column(String(length=100), nullable=False)
    describe = Column(String(length=1000), nullable=False)
    priority = Column(String(length=20), nullable=False)
    stat_task = Column(String(length=30), nullable=False)


class DUser(Model):
    __tablename__ = "Users"
    id = Column(Integer, primary_key=True, autoincrement=True)
    date_created = Column(DateTime(), nullable=False)
    login = Column(String(length=100), nullable=False, unique=True)
    name = Column( String(length=100), nullable=False)
    post = Column(String(length=100), nullable=False)
    status = Column(String(length=100), nullable=False)
    describe = Column(String(length=1000), nullable=False)
    password = Column(String(length=200), nullable=False)


class DTutor(Model):
    __tablename__ = "Tutor"
    id = Column(Integer, primary_key=True, autoincrement=True)
    tutor = Column(String(length=20), nullable=False, unique=True)
    name = Column( String(length=100), nullable=False)



