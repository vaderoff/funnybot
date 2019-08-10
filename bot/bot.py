from aiogram import Bot, Dispatcher, executor, types
import os
import motor.motor_asyncio
import random

bot = Bot(os.environ.get('BOT_TOKEN'))
dp = Dispatcher(bot)

db = motor.motor_asyncio.AsyncIOMotorClient('mongo', 27017).funnybot


@dp.message_handler(content_types=types.ContentTypes.TEXT)
async def message_handler(message: types.Message):
    words = message.text.split()
    await db.words.insert_many([{'word': x} for x in words])

    await db.message_counters.update_one(
        {'chat_id': message.chat.id},
        {
            '$inc': {'count': 1},
            '$set': {'chat_id': message.chat.id}
        },
        upsert=True)

    counter = await db.message_counters.find_one({'chat_id': message.chat.id})
    if counter.get('count') >= int(os.environ.get('COUNT_TO_RESET')):
        await db.message_counters.update_one(
            {'_id': counter.get('_id')},
            {'$set': {'count': 0}}
        )

        words_cursor = db.words.find()
        words = await words_cursor.to_list()
        random_words_count = random.choice(range(10))
        random_words = random.choices(words, k=random_words_count)
        sentence = ' '.join([x['word'] for x in random_words])

        await message.reply(sentence)
