from datetime import datetime

from sqlalchemy import (Boolean, CheckConstraint, DateTime, ForeignKey,
                        Integer, String, UniqueConstraint)
from sqlalchemy.orm import (DeclarativeBase, Mapped, declared_attr,
                            mapped_column, relationship, validates)


class Base(DeclarativeBase):

    @declared_attr
    def __tablename__(cls):
        return cls.__name__.lower() + 's'


class WithID:
    id: Mapped[int] = mapped_column(
        Integer, primary_key=True, autoincrement=True)


class User(WithID, Base):
    user_chat_id: Mapped[int] = mapped_column(Integer, unique=True)
    progress: Mapped[list['Progress']] = relationship(
        back_populates='user', cascade='all, delete-orphan')
    words: Mapped[list['Word']] = relationship(
        back_populates='user', cascade='all, delete-orphan')
    is_admin: Mapped[bool] = mapped_column(
        Boolean, default=False, server_default='false')


class Word(WithID, Base):
    user_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey('users.id'), index=True)
    word: Mapped[str] = mapped_column(
        String(255), nullable=False)
    translation: Mapped[str] = mapped_column(String(255), nullable=False)
    user: Mapped[list['User']] = relationship(back_populates='words')
    progress: Mapped[list['Progress']] = relationship(back_populates='word')

    __table_args__ = (
        UniqueConstraint('word', 'user_id', name='unique_word_user_id'),
    )


class Progress(Base):
    __tablename__ = 'progress'

    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey('users.id', ondelete='CASCADE'), primary_key=True)
    word_id: Mapped[int] = mapped_column(
        Integer, ForeignKey('words.id', ondelete='CASCADE'), primary_key=True)
    correct_answers: Mapped[int] = mapped_column(
        Integer, default=0, nullable=False)
    is_learned: Mapped[bool] = mapped_column(Boolean, default=False)
    learned_at: Mapped[datetime | None] = mapped_column(
        DateTime, nullable=True, default=None)
    user: Mapped['User'] = relationship(back_populates='progress')
    word: Mapped['Word'] = relationship(back_populates='progress')

    __table_args__ = (
        CheckConstraint('correct_answers >= 0 AND correct_answers <= 5'),
    )

    @validates('correct_answers')
    def validate_correct_answer(self, key, value):
        if value < 0:
            return 0
        if value == 5:
            self.is_learned = True
            return 0
        return value

    @validates('is_learned')
    def validate_is_learned(self, key, value):
        self.learned_at = datetime.now() if value else None
        return value
