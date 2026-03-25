from datetime import datetime, timezone

from sqlalchemy import Integer, ForeignKey, String, Boolean, DateTime
from sqlalchemy.orm import DeclarativeBase, declared_attr, Mapped, mapped_column, relationship, validates


class Base(DeclarativeBase):

    @declared_attr
    def __tablename__(cls):
        return cls.__name__.lower() + 's'

class WithID:
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)


class User(WithID, Base):
    user_chat_id: Mapped[int] = mapped_column(Integer, unique=True)
    progress: Mapped[list['Progress']] = relationship(back_populates='user', cascade='all, delete-orphan')
    words: Mapped[list['Word']] = relationship(back_populates='user', cascade='all, delete-orphan')

class Word(WithID, Base):
    user_id: Mapped[int | None] = mapped_column(Integer, ForeignKey('users.id'))
    word: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    translation: Mapped[str] = mapped_column(String(255), nullable=False)    
    user: Mapped[list['User']] = relationship(back_populates='words')   
    progress: Mapped[list['Progress']] = relationship(back_populates='word') 




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

    @validates('is_learned')
    def validate_is_learned(self, key, value):
        self.learned_at = datetime.now(timezone.utc) if value else None
        return value
    

    
