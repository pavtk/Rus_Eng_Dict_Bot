from contextlib import asynccontextmanager

import sqlalchemy.ext.asyncio
from pydantic import with_config
from sqlalchemy import or_, select, result_tuple, insert, func, delete
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import selectinload

from database import User, Base, Word
from settings import DBSettings

db_settings = DBSettings()

engine = create_async_engine(
    url=db_settings.db_url,
    echo=db_settings.db_echo
)


# async def create_all():
#     async with engine.begin() as conn:
#         await conn.run_sync(Base.metadata.drop_all)
#         await conn.run_sync(Base.metadata.create_all)


session = async_sessionmaker(engine, expire_on_commit=False)


@asynccontextmanager
async def get_session():
    async with session() as s:
        try:
            yield s
            await s.commit()
        except Exception as e:
            await s.rollback()
            raise e


class BaseMethods:
    model = None

    @classmethod
    async def get_all(cls):
        async with get_session() as session:
            result = await session.execute(select(cls.model))
            return result.scalars().all()

    @classmethod
    async def get_one_by_id(cls, id: int):
        async with get_session() as session:
            result = await session.execute(select(cls.model).where(cls.model.id == id))
            return result.scalar_one_or_none()

    @classmethod
    async def add(cls, **kwargs):
        async with get_session() as session:
            query = insert(cls.model).values(**kwargs).returning(cls.model)
            result = await session.execute(query)
        return result.scalar_one()

    @classmethod
    async def add_all_words(cls, data):
        async with get_session() as session:
            query = insert(cls.model)
            await session.execute(query, data)
        return 'Data was upload in DB'    



class UserMethods(BaseMethods):
    model = User

    @classmethod
    async def check_user(cls, user_chat_id: int) -> bool:
        async with get_session() as session:
            result = await session.execute(
                select(cls.model).where(cls.model.user_chat_id == user_chat_id)
            )
            return result.scalar_one_or_none()


class WordMethods(BaseMethods):
    model = Word

    @classmethod
    async def get_random_word(cls, user_id, number_of_words):
        async with get_session() as session:
            result = await session.execute(
                select(cls.model)
                .where(cls.model.user_id == user_id, cls.model.user_id == None)
                .order_by(func.random())
                .limit(number_of_words)
            )
        if number_of_words == 1:
            return result.scalar_one_or_none()
        return result.scalars().all()

    @classmethod
    async def check_word(cls, word: str) -> bool:
        async with get_session() as session:
            result = await session.execute(
                select(cls.model).where(cls.model.word == word)
            )
            return result.scalar_one_or_none()

    @classmethod
    async def check_user_word(cls, user_id: int, word: str) -> bool:
        async with get_session() as session:
            result = await session.execute(
                select(cls.model).where(cls.model.user_id ==
                                        user_id, cls.model.word == word)
            )
            return result.scalar_one_or_none()

    @classmethod
    async def get_random_translation(cls, user_id):
        async with get_session() as session:
            result = await session.execute(
                select(cls.model)
                .where(or_(cls.model.user_id == user_id, cls.model.user_id.is_(None)))
                .order_by(func.random())
                .limit(1)
            )
        return result.scalar_one()

    @classmethod
    async def delete_word_by_id(cls, user_id: int, word: str):
        async with get_session() as session:
            result = await session.execute(
                delete(cls.model)
                .where(
                    cls.model.user_id == user_id,
                    cls.model.word == word
                )
            )
            return result.rowcount
