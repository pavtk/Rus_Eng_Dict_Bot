from db_methods import ProgressMethods, UserMethods, WordMethods


async def check_user_by_chat_id(user_chat_id: int):
    return await UserMethods.check_user(user_chat_id)


async def add_user(user_chat_id: int):
    return await UserMethods.add(user_chat_id=user_chat_id)


async def get_random_word(user_id, number_of_words: int = 1):
    return await WordMethods.get_random_word(user_id, number_of_words)


async def add_word(word):
    checked_word = await WordMethods.check_word(word=word)
    if checked_word:
        return checked_word
    new_word = await WordMethods.add(word=word)
    return new_word


async def add_user_word(user_id, word, translation):
    user_word = await WordMethods.check_user_word(user_id=user_id, word=word)
    common_word = await WordMethods.check_word(word=word)
    if not user_word and not common_word:
        user_word = await WordMethods.add(user_id=user_id, word=word, translation=translation)
        return user_word
    return user_word


async def get_random_russian_word(user_id):
    word = await WordMethods.get_random_translation(user_id=user_id)
    return word


async def get_word_by_id(word_id):
    word = await WordMethods.get_one_by_id(id=word_id)
    return word


async def delete_word(user_id, word):
    return await WordMethods.delete_word_by_id(user_id=user_id, word=word)


async def check_user_word(user_id, word):
    return await WordMethods.check_user_word(user_id=user_id, word=word)


async def add_common_words(data):
    return await WordMethods.add_all_words(data=data)


async def get_progress(word_id, user_id):
    return await ProgressMethods.get_word_points(word_id=word_id, user_id=user_id)


async def add_progress(word_id, user_id):
    return await ProgressMethods.add(word_id=word_id, user_id=user_id)


async def change_point(word_id, user_id, point):
    return await ProgressMethods.change_point(word_id=word_id, user_id=user_id, point=point)


async def words_count(user_id: int):
    return await WordMethods.count_items(user_id=user_id)


async def drop_progress(user_id: int):
    return await ProgressMethods.drop_user_progress(user_id=user_id)
