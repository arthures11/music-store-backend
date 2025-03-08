from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, declarative_base
from dotenv import load_dotenv
import os

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

engine = create_engine(DATABASE_URL.replace("+aiosqlite", ""), connect_args={"check_same_thread": False})

async_engine = create_async_engine(DATABASE_URL)
async_session = sessionmaker(async_engine, expire_on_commit=False, class_=AsyncSession)


Base = declarative_base()


async def get_db():
    db = async_session()
    try:
        yield db
    finally:
        await db.close()