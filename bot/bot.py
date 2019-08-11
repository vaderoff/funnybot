from aiogram import Bot, Dispatcher, executor, types
import os
import motor.motor_asyncio
import random
import asyncio

bot = Bot(os.environ.get('BOT_TOKEN'))
dp = Dispatcher(bot, run_tasks_by_default=True)

db = motor.motor_asyncio.AsyncIOMotorClient('mongo', 27017).funnybot

CHAT_ID = int(os.environ.get('CHAT_ID'))
PHOTOS = os.environ.get('PUNCH_PHOTOS').split(',')
DELAY = int(os.environ.get('DELAY'))

POWER_POINTS = range(100, 1000)


async def punch_session_start():
    await db.punch_sessions.update_one(
        {'chat_id': CHAT_ID},
        {'$set': {'members': [], 'chat_id': CHAT_ID}},
        upsert=True)
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton('Ударить', callback_data='punch'))
    photo = random.choice(PHOTOS)
    await bot.send_photo(
        CHAT_ID, photo, caption='Ударь меня', reply_markup=markup)


@dp.callback_query_handler(lambda x: x.data == 'punch' and x.message.chat.id == CHAT_ID)
async def punch(callback: types.CallbackQuery):
    punch_session = await db.punch_sessions.find_one({'chat_id': CHAT_ID})
    if callback.from_user.id not in punch_session['members']:
        punch_session['members'].append(callback.from_user.id)
        power = random.choice(POWER_POINTS)
        text = '<a href="tg://user?id={}">{}</a> ударил на <b>{}</b> 😵'.format(
            callback.from_user.id, callback.from_user.first_name, power)
        await db.punch_sessions.update_one(
            {'chat_id': CHAT_ID},
            {'$set': {'members': punch_session['members']}}
        )
        await callback.answer('👅{}👅'.format(power))
        await bot.send_message(
            chat_id, text, reply_to_message_id=callback.message.message_id,
            parse_mode='Html')
