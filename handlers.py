import re
import html
import json
import random
from enum import IntEnum

from telegram import (InlineKeyboardMarkup, ReplyKeyboardMarkup,
                      ReplyKeyboardRemove, Update)
from telegram.ext import (CommandHandler, ContextTypes, ConversationHandler,
                          MessageHandler, filters)

from db_methods import UserMethods
from service import (add_common_words, add_progress, add_user, add_user_word,
                     add_word, change_point, check_user_by_chat_id,
                     check_user_word, delete_word, drop_progress, get_progress,
                     get_random_russian_word, get_random_word, get_word_by_id,
                     words_count)


class State(IntEnum):
    CHOOSING = 0
    TYPING_ADD = 1
    TYPING_DEL = 2
    TYPING_NEXT = 3
    ADD_TRANSLATION = 4
    RETRY = 5


async def continue_game(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_id = context.user_data.get('user_id')
    if not user_id:
        user = await check_user_by_chat_id(update.effective_user.id)
        if not user:
            user = await add_user(user_chat_id=update.effective_user.id)
        context.user_data['user_id'] = user.id
        user_id = user.id

    random_word = await get_random_russian_word(user_id)
    if not random_word:
        await update.message.reply_text(
            '📭 В базе пока нет слов для изучения. '
            'Добавьте новое слово командой /add.'
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


async def add_data(update: Update, context: ContextTypes.DEFAULT_TYPE):
    with open('base_words.json', encoding='utf-8') as file:
        data = json.load(file)
    result = await add_common_words(data)
    await update.message.reply_text(
        result
    )


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Обработчик команды /start с приветственным сообщением"""
    user = await check_user_by_chat_id(update.effective_user.id)
    if not user:
        user = await add_user(user_chat_id=update.effective_user.id)
        await update.message.reply_text(
            f'👋 Привет, {html.escape(update.effective_user.first_name)}! '
            f'Добро пожаловать в бота для изучения английских слов! 🇬🇧\n\n'
            f'Здесь вы сможете:\n'
            f'• Учить новые слова\n'
            f'• Проверять свои знания\n'
            f'• Добавлять свои слова\n\n'
            f'Давайте начнем! 🚀'
        )
    else:
        await update.message.reply_text(
            f'👋 С возвращением, {html.escape(update.effective_user.first_name)}! '
            f'Продолжим изучение слов? 🇬🇧'
        )
    drop_progress(user_id=user.id)
    context.user_data['user_id'] = user.id
    return await continue_game(update, context)


async def add_word_typing(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text(
        'Введите английское слово которое хотите добавить: ',
        reply_markup=ReplyKeyboardRemove()
    )
    return State.TYPING_ADD


async def add_new_word(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    new_english_word = update.message.text
    if not re.match(r'^[a-zA-Z]+$', new_english_word):
        update.message.reply_text(
            'Ведите слово на <b>английском языке</b>',
            parse_mode='HTML'
        )
        return State.TYPING_ADD

    context.user_data['new_word'] = new_english_word.strip().lower()
    await update.message.reply_text(
        f"Введите перевод для <b>{html.escape(context.user_data['new_word'])}</b>:   ", parse_mode='HTML'
    )
    return State.ADD_TRANSLATION


async def save_translation(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_id = context.user_data['user_id']
    new_translation = update.message.text
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
    """Запрос слова для удаления"""
    await update.message.reply_text(
        'Введите слово, которое хотите удалить: ',
        reply_markup=ReplyKeyboardRemove()
    )
    return State.TYPING_DEL


async def delete_word_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Удаление слова"""
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


async def update_keyboard(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = await check_user_by_chat_id(update.effective_user.id)
    words = await get_random_word(user_id=user.id, number_of_words=3)
    random_button = [word.word for word in words]

    while context.user_data['word'] in random_button:
        words = words = await get_random_word(user_id=user.id, number_of_words=3)
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
    word_id = context.user_data['word_id']
    user_id = context.user_data['user_id']
    selected_word = update.message.text
    correct_word = context.user_data['word']

    if selected_word == correct_word:
        points = await change_point(word_id=word_id, user_id=user_id, point=1)
        await update.message.reply_text(
            f'✅ Верно!\n'
            f'Правильных ответов: {points}'
        )
        return await continue_game(update, context)
    else:
        points = await change_point(word_id=word_id, user_id=user_id, point=-1)
        await update.message.reply_text(
            f'❌ Неверно. Попробуйте ещё раз! 🔄\n'
            f'Правильных ответов: {points}\n'
            f'Выберите перевод для слова <b>{html.escape(context.user_data["russian_word"])}</b>: ',
            parse_mode='HTML'
        )
        return State.RETRY


async def retry_answer(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Обработка повторной попытки"""
    word_id = context.user_data['word_id']
    user_id = context.user_data['user_id']
    selected_word = update.message.text
    correct_word = context.user_data['word']

    if selected_word == correct_word:
        points = await change_point(word_id=word_id, user_id=user_id, point=1)
        await update.message.reply_text(
            f'✅ Верно!\n'
            f'Правильных ответов: {points}'
        )
        return await continue_game(update, context)
    else:
        points = await change_point(word_id=word_id, user_id=user_id, point=-1)
        await update.message.reply_text(
            f'❌ Неверно. Попробуйте ещё раз! 🔄\n'
            f'Правильных ответов: {points}\n'
            f'Выберите перевод для слова <b>{html.escape(context.user_data["russian_word"])}</b>: ',
            parse_mode='HTML'
        )
        return State.RETRY


conv_handler = ConversationHandler(
    entry_points=[CommandHandler("start", start)],
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
        ],
        State.RETRY: [
            MessageHandler(
                filters.TEXT & ~filters.COMMAND, retry_answer
            )
        ],
    },
    fallbacks=[CommandHandler("start", start)],
)
