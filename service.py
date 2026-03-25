from db_methods import WordMethods


async def get_random_word(user_id, number_of_words: int = 1):
    return await WordMethods.get_random_word(user_id, number_of_words)


async def add_word(word):
    checked_word = await WordMethods.check_word(word=word)
    if checked_word:
        return checked_word.id
    new_word = await WordMethods.add(word=word)
    return new_word.id


async def add_user_word(user_id, word, translation):
    user_word = await WordMethods.check_user_word(user_id=user_id, word=word)
    if not user_word:
        new_translate = await WordMethods.add(word=word, user_id=user_id, translation=translation)
        return new_translate.translation
    return user_word.translation


async def get_random_russian_word(user_id):
    word = await WordMethods.get_random_translation(user_id=user_id)
    return word


async def get_word_by_id(word_id):
    word = await WordMethods.get_one_by_id(id=word_id)
    return word


async def delete_word(user_id, word):
    return await WordMethods.delete_word_by_id(user_id=user_id, word=word)


async def check_word_func(word):
    return await WordMethods.check_word(word=word)


async def add_common_words(data):
    return await WordMethods.add_all_words(data=data)
