from contextlib import asynccontextmanager

from sqlalchemy import and_, delete, func, or_, select, update
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import (AsyncSession, async_sessionmaker,
                                    create_async_engine)

from database import Base, Progress, User, Word
from settings import DBSettings

db_settings = DBSettings()

engine = create_async_engine(
    url=db_settings.db_url,
    echo=db_settings.db_echo
)


async def create_all() -> None:
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


session = async_sessionmaker(engine, expire_on_commit=False)


@asynccontextmanager
async def get_session() -> AsyncSession:
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
    async def get_all(cls) -> list[object]:
        async with get_session() as session:
            result = await session.execute(select(cls.model))
            return result.scalars().all()

    @classmethod
    async def get_one_by_id(cls, id: int) -> object | None:
        async with get_session() as session:
            result = await session.execute(select(cls.model).where(cls.model.id == id))
            return result.scalar_one_or_none()

    @classmethod
    async def add(cls, **kwargs) -> object:
        async with get_session() as session:
            query = insert(cls.model).values(**kwargs).returning(cls.model)
            result = await session.execute(query)
        return result.scalar_one()

    @classmethod
    async def add_common_words(cls, data: list[dict]) -> str:
        async with get_session() as session:
            query = insert(cls.model)
            await session.execute(query, data)
        return 'Data was upload to DB'

    @classmethod
    async def add_user_words(cls, user_id: int, data: list[dict]) -> str:
        async with get_session() as session:
            data = [{**item, 'user_id': user_id} for item in data]
            query = insert(cls.model).on_conflict_do_nothing(
                index_elements=['word'])
            await session.execute(query, data)
        return 'Data was upload to DB'


class UserMethods(BaseMethods):
    model = User

    @classmethod
    async def check_user(cls, user_chat_id: int) -> User | None:
        async with get_session() as session:
            result = await session.execute(
                select(cls.model).where(cls.model.user_chat_id == user_chat_id)
            )
            return result.scalar_one_or_none()


class WordMethods(BaseMethods):
    model = Word

    @classmethod
    async def count_items(cls, user_id: int) -> int:
        async with get_session() as session:
            result = await session.execute(
                select(func.count())
                .select_from(cls.model)
                .where(or_(cls.model.user_id == user_id, cls.model.user_id.is_(None)))
            )
        return result.scalar()

    @classmethod
    async def get_random_word(cls, user_id: int, number_of_words: int) -> Word | list[Word] | None:
        async with get_session() as session:
            result = await session.execute(
                select(cls.model)
                .where(or_(cls.model.user_id == user_id, cls.model.user_id.is_(None)))
                .order_by(func.random())
                .limit(number_of_words)
            )
        if number_of_words == 1:
            return result.scalar_one_or_none()
        return result.scalars().all()

    @classmethod
    async def check_word(cls, word: str) -> Word | None:
        async with get_session() as session:
            result = await session.execute(
                select(cls.model).where(cls.model.word == word)
            )
            return result.scalar_one_or_none()

    @classmethod
    async def check_user_word(cls, user_id: int, word: str) -> Word | None:
        async with get_session() as session:
            result = await session.execute(
                select(cls.model).where(cls.model.user_id ==
                                        user_id, cls.model.word == word)
            )
            return result.scalar_one_or_none()

    @classmethod
    async def get_random_translation(cls, user_id: int) -> Word | None:
        async with get_session() as session:
            result = await session.execute(
                select(cls.model)
                .outerjoin(Progress, and_(
                    Progress.word_id == cls.model.id,
                    Progress.user_id == user_id
                ))
                .where(
                    or_(cls.model.user_id == user_id,
                        cls.model.user_id.is_(None)),
                    or_(Progress.is_learned == False,
                        Progress.is_learned == None)
                )
                .order_by(func.random())
                .limit(1)
            )
        return result.scalar_one_or_none()

    @classmethod
    async def delete_word_by_id(cls, user_id: int, word: str) -> int:
        async with get_session() as session:
            result = await session.execute(
                delete(cls.model)
                .where(
                    cls.model.user_id == user_id,
                    cls.model.word == word
                )
            )
            return result.rowcount


class ProgressMethods(BaseMethods):
    model = Progress

    @classmethod
    async def get_word_points(cls, word_id: int, user_id: int) -> Progress | None:
        async with get_session() as session:
            result = await session.execute(
                select(cls.model)
                .where(
                    cls.model.user_id == user_id,
                    cls.model.word_id == word_id
                )
            )
            progress = result.scalar_one_or_none()
            return progress

    @classmethod
    async def change_point(cls, word_id: int, user_id: int, point: int) -> int:
        async with get_session() as session:
            progress = await session.execute(
                select(cls.model)
                .where(
                    cls.model.user_id == user_id,
                    cls.model.word_id == word_id
                )
            )
            progress = progress.scalar_one_or_none()
            if progress:
                progress.correct_answers += point
                return progress.correct_answers
            new_progress = Progress(
                user_id=user_id,
                word_id=word_id,
                correct_answers=max(0, point)
            )
            session.add(new_progress)
            return new_progress.correct_answers

    @classmethod
    async def drop_user_progress(cls, user_id: int) -> None:
        async with get_session() as session:
            await session.execute(
                update(cls.model)
                .where(cls.model.user_id == user_id)
                .values(is_learned=False)
            )
