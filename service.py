from database import Progress, User, Word
from db_methods import ProgressMethods, UserMethods, WordMethods


async def check_user_by_chat_id(user_chat_id: int) -> User:
    """
    Check if a user exists by their Telegram chat ID.
    """
    return await UserMethods.check_user(user_chat_id)


async def add_user(user_chat_id: int) -> User:
    """
    Register a new user in the database.
    """
    return await UserMethods.add(user_chat_id=user_chat_id)


async def get_random_word(user_id, number_of_words: int = 1):
    """
    Get random word(s) for a user, user-specific or common words.
    """
    return await WordMethods.get_random_word(user_id, number_of_words)


async def add_user_word(user_id: int, word: str, translation: str) -> Word:
    """
    Add a new word-translation pair for a specific user.
    """
    user_word = await WordMethods.check_user_word(user_id=user_id, word=word)
    common_word = await WordMethods.check_word(word=word)
    if not user_word and not common_word:
        user_word = await WordMethods.add(user_id=user_id, word=word, translation=translation)
        return user_word
    return user_word


async def get_random_russian_word(user_id: int) -> Word:
    """
    Get a random Russian translation for quiz generation.
    """
    word = await WordMethods.get_random_translation(user_id=user_id)
    return word


async def get_word_by_id(word_id: int) -> Word:
    """
    Retrieve a word by its database ID.
    """
    word = await WordMethods.get_one_by_id(id=word_id)
    return word


async def delete_word(user_id: int, word: str) -> int:
    """
    Delete a word from user's vocabulary.
    """
    return await WordMethods.delete_word_by_id(user_id=user_id, word=word)


async def check_user_word(user_id: int, word: str) -> Word | None:
    """
    Check if a specific word exists in user's vocabulary.
    """
    return await WordMethods.check_user_word(user_id=user_id, word=word)


async def add_common_words(user: id, data: list[dict]) -> str:
    """
    Add common shared words to the database. Admin-only operation.
    """
    if not user.is_admin:
        return 'Access denied: admin only'
    return await WordMethods.add_common_words(data=data)


async def add_user_data(user_id: int, data: list[dict]) -> str:
    """
    Add words to user's personal vocabulary from a data list.
    """
    return await WordMethods.add_user_words(user_id=user_id, data=data)


async def get_progress(word_id: int, user_id: int) -> Progress:
    """
    Get learning progress for a specific word.
    """
    return await ProgressMethods.get_word_points(word_id=word_id, user_id=user_id)


async def add_progress(word_id: int, user_id: int) -> Progress:
    """
    Create a new progress record for a word-user pair.
    """
    return await ProgressMethods.add(word_id=word_id, user_id=user_id)


async def change_point(word_id: int, user_id: int, point: int) -> int:
    """
    Update progress points for a word after user answer.
    """
    return await ProgressMethods.change_point(word_id=word_id, user_id=user_id, point=point)


async def words_count(user_id: int) -> int:
    """
    Count total words in user's vocabulary (personal + common).
    """
    return await WordMethods.count_items(user_id=user_id)


async def drop_progress(user_id: int) -> None:
    """
    Reset learning progress for all user's words.
    """
    return await ProgressMethods.drop_user_progress(user_id=user_id)
