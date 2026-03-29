import html
import json
import random
import re
from enum import IntEnum

from telegram import ReplyKeyboardMarkup, ReplyKeyboardRemove, Update
from telegram.ext import (CommandHandler, ContextTypes, ConversationHandler,
                          MessageHandler, filters)

from db_methods import create_all
from service import (add_common_words, add_user, add_user_data, add_user_word,
                     change_point, check_user_by_chat_id, check_user_word,
                     delete_word, drop_progress, get_random_russian_word,
                     get_random_word, words_count)

KEY_COUNT = 3
RIGHT_ANSWER = 1
BAD_ANSWER = -1


class State(IntEnum):
    CHOOSING = 0
    TYPING_ADD = 1
    TYPING_DEL = 2
    ADD_TRANSLATION = 3


async def continue_game(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Continue the vocabulary quiz game.
    Retrieves a random Russian word for translation, checks if user has enough
    words in their vocabulary, and displays the quiz keyboard.
    """
    user_id = context.user_data.get('user_id')
    if not user_id:
        user = await check_user_by_chat_id(update.effective_user.id)
        if not user:
            user = await add_user(user_chat_id=update.effective_user.id)
        context.user_data['user_id'] = user.id
        user_id = user.id

    random_word = await get_random_russian_word(user_id)
    words_quantity = await words_count(user_id=user_id)
    if words_quantity < 4:
        await update.message.reply_text(
            '✨ Чтобы начать изучение, нам нужно чуть больше слов!\n'
            'Добавьте ещё пару слов и можно стартовать! 😊'
        )
        return State.TYPING_ADD

    context.user_data['russian_word'] = random_word.translation
    context.user_data['word'] = random_word.word
    context.user_data['word_id'] = random_word.id

    reply_keyboard = await update_keyboard(update, context)
    await update.message.reply_text(
        f'Выберите перевод для слова <b>{html.escape(context.user_data["russian_word"])}</b>: ',
        reply_markup=ReplyKeyboardMarkup(reply_keyboard, resize_keyboard=True),
        parse_mode='HTML'
    )
    return State.CHOOSING


async def add_data(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Load common words from base_words.json file.
    Admin-only command that adds shared vocabulary words to the database.
    Handles file not found and JSON parsing errors gracefully.
    """
    user = await check_user_by_chat_id(update.effective_user.id)
    try:
        with open('base_words.json', encoding='utf-8') as file:
            data = json.load(file)
        result = await add_common_words(user, data)
        await update.message.reply_text(
            result
        )
    except FileNotFoundError:
        await update.message.reply_text('❌ Файл не найден')
    except json.JSONDecodeError:
        await update.message.reply_text('❌ Неверный формат JSON')


async def add_user_dict(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Load user-specific words from user_words.json file.
    Adds personal vocabulary words to the user's learning list.
    Handles file not found and JSON parsing errors gracefully.
    """
    try:
        with open('user_words.json', encoding='utf-8') as file:
            data = json.load(file)
        result = await add_user_data(context.user_data['user_id'], data)
        await update.message.reply_text(
            result
        )
    except FileNotFoundError:
        await update.message.reply_text('❌ Файл не найден')
    except json.JSONDecodeError:
        await update.message.reply_text('❌ Неверный формат JSON')


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Handle /start and /cards commands with welcome message.
    Registers new users, resets progress for returning users,
    and initiates the quiz game.
    """
    await create_all()
    user = await check_user_by_chat_id(update.effective_user.id)
    if not user:
        user = await add_user(user_chat_id=update.effective_user.id)
        await update.message.reply_text(
            f'Привет, {html.escape(update.effective_user.first_name)}! 👋\n\n'
            f'Я помогу тебе запомнить английские слова — быстро и без скуки 🇬🇧\n\n'
            f'Принцип простой: я показываю слово, ты вводишь перевод.\n'
            f'Ответил верно 5 раз — слово в копилку ✅\n\n'
            f'Свои слова можно добавлять 📝 и удалять 🚫\n'
            f'Сбросить прогресс — /start или /cards\n\n'
            f'Начнём! 🚀'
        )
    else:
        await update.message.reply_text(
            f'👋 С возвращением, {html.escape(update.effective_user.first_name)}! '
            f'Продолжим изучение слов? 🇬🇧'
        )
    await drop_progress(user_id=user.id)
    context.user_data['user_id'] = user.id
    return await continue_game(update, context)


async def add_word_typing(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Prompt user to enter a new English word to add.
    """
    await update.message.reply_text(
        'Введите английское слово которое хотите добавить: ',
        reply_markup=ReplyKeyboardRemove()
    )
    return State.TYPING_ADD


async def add_new_word(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Validate and store the new English word.
    """
    new_english_word = update.message.text
    if not re.match(r'^[a-zA-Z ]+$', new_english_word):
        await update.message.reply_text(
            '⚠️ Добавляемое слово должно быть на <b>английском языке</b>:',
            parse_mode='HTML'
        )
        return State.TYPING_ADD

    context.user_data['new_word'] = new_english_word.strip().lower()
    await update.message.reply_text(
        f"Введите перевод для <b>{html.escape(context.user_data['new_word'])}</b>:   ", parse_mode='HTML'
    )
    return State.ADD_TRANSLATION


async def save_translation(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Validate and save the Russian translation for a new word.
    Checks that the input contains only Russian letters and spaces,
    then saves the word-translation pair to the database.
    """
    user_id = context.user_data['user_id']
    new_translation = update.message.text
    if not re.match(r'^[а-яА-ЯёЁ ]+$', new_translation):
        await update.message.reply_text(
            '⚠️ Перевод должен быть на <b>русском языке</b>',
            parse_mode='HTML'
        )
        return State.ADD_TRANSLATION

    new_word = await add_user_word(
        user_id=user_id,
        word=context.user_data['new_word'],
        translation=new_translation
    )
    words_quantity = await words_count(user_id=user_id)
    if new_word:
        await update.message.reply_text(
            f'Добавлено слово <b>{html.escape(new_word.word)}</b> - <b>{html.escape(new_translation)}</b>\n'
            f'На данный момент вы изучаете <b>{words_quantity}</b> слов',
            parse_mode='HTML'
        )
    else:
        await update.message.reply_text(
            f'Слово <b>{html.escape(context.user_data["new_word"])}</b> уже есть в вашем списке ❌',
            parse_mode='HTML'
        )
    return await continue_game(update, context)


async def delete_word_typing(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Prompt user to enter a word for deletion.
    """
    await update.message.reply_text(
        'Введите слово, которое хотите удалить: ',
        reply_markup=ReplyKeyboardRemove()
    )
    return State.TYPING_DEL


async def delete_word_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Delete a word from user's vocabulary.
    Checks if the word exists in user's vocabulary or database,
    then removes it and provides feedback.
    """
    word_to_delete = update.message.text.strip().lower()
    user_id = context.user_data['user_id']
    word = await check_user_word(user_id=user_id, word=word_to_delete)

    if word:
        deleted = await delete_word(user_id=user_id, word=word.word)
        if deleted > 0:
            await update.message.reply_text(f'Слово "{html.escape(word_to_delete)}" удалено ✅')
        else:
            await update.message.reply_text(f'Слово "{html.escape(word_to_delete)}" не найдено в вашем списке ❌')
    else:
        await update.message.reply_text(f'Слово "{html.escape(word_to_delete)}" не найдено в базе ❌')

    return await continue_game(update, context)


async def update_keyboard(update: Update, context: ContextTypes.DEFAULT_TYPE) -> list:
    """
    Generate keyboard with answer options for the quiz.
    """
    user_id = context.user_data['user_id']
    words = await get_random_word(user_id=user_id, number_of_words=KEY_COUNT)
    random_button = [word.word for word in words]

    while context.user_data['word'] in random_button:
        words = await get_random_word(user_id=user_id, number_of_words=KEY_COUNT)
        random_button = [word.word for word in words]
    words_buttons = [context.user_data['word']] + random_button
    random.shuffle(words_buttons)
    reply_keyboard = [
        words_buttons,
        ['➡️ Дальше', '📝 Добавить слово'],
        ['🚫 Удалить слово']
    ]
    return reply_keyboard


async def check_answer(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Check user's answer and update progress.
    Compares selected word with correct answer, updates progress points
    and continues the game or asks for retry.

    """
    word_id = context.user_data['word_id']
    user_id = context.user_data['user_id']
    selected_word = update.message.text
    correct_word = context.user_data['word']

    if selected_word == correct_word:
        points = await change_point(word_id=word_id, user_id=user_id, point=RIGHT_ANSWER)
        await update.message.reply_text(
            f'✅ Верно!\n'
            f'Правильных ответов: {points}'
        )
        return await continue_game(update, context)
    else:
        points = await change_point(word_id=word_id, user_id=user_id, point=BAD_ANSWER)
        await update.message.reply_text(
            f'❌ Неверно. Попробуйте ещё раз! 🔄\n'
            f'Правильных ответов: {points}\n'
            f'Выберите перевод для слова <b>{html.escape(context.user_data["russian_word"])}</b>: ',
            parse_mode='HTML'
        )
        return State.CHOOSING


conv_handler = ConversationHandler(
    entry_points=[
        CommandHandler('start', start),
        CommandHandler('cards', start),

    ],
    states={
        State.CHOOSING: [
            MessageHandler(
                filters.Regex('^📝 Добавить слово$'), add_word_typing),
            MessageHandler(
                filters.Regex('^➡️ Дальше$'), continue_game
            ),
            MessageHandler(
                filters.Regex('^🚫 Удалить слово$'), delete_word_typing
            ),
            MessageHandler(
                filters.TEXT & ~filters.COMMAND, check_answer
            ),
        ],
        State.TYPING_ADD: [
            MessageHandler(
                filters.TEXT & ~filters.COMMAND, add_new_word
            )
        ],
        State.TYPING_DEL: [
            MessageHandler(
                filters.TEXT & ~filters.COMMAND, delete_word_handler
            )
        ],
        State.ADD_TRANSLATION: [
            MessageHandler(
                filters.TEXT & ~filters.COMMAND, save_translation
            )
        ]
    },
    fallbacks=[
        CommandHandler('start', start),
        CommandHandler('cards', start)
    ],
)
