from aiogram import Bot, Dispatcher, executor, types
import os
import motor.motor_asyncio
import random
import asyncio
from bson.objectid import ObjectId

bot = Bot(os.environ.get('BOT_TOKEN'))
dp = Dispatcher(bot, run_tasks_by_default=True)

db = motor.motor_asyncio.AsyncIOMotorClient('mongo', 27017).funnybot

DELAY = int(os.environ.get('DELAY'))


class Casino:
    balls = [[':red_circle:', 0], [':black_circle:', 1]]

    def get_ball(self):
        return random.choice(balls)

    async def new_session(self, chat_id):
        await db.casino_sessions.insert_one({
            'chat_id': chat_id,
            'players': [],
            'active': True
        })
        markup = types.InlineKeyboardMarkup()
        markup.add(
            types.InlineKeyboardButton(self.balls[0][0], callback_data='casino:{}'.format(self.balls[0][1])),
            types.InlineKeyboardButton(self.balls[1][0], callback_data='casino:{}'.format(self.balls[1][1]))
        )
        await bot.send_message(chat_id, 'Выбери шар', reply_markup=markup)

    async def play_session(self, chat_id):
        session = await db.casino_sessions.find_one({'chat_id': chat_id, 'active': True})
        if session:
            ball = self.get_ball()
            winners = [x for x in session['players'] if x['ball'] == ball[1]]
            _winners = []
            for winner in winners:
                await db.casino_winners.update_one(
                    {'user_id': winner['user_id']},
                    {
                        '$inc': {'win_count': 1},
                        '$set': {'user_id': winner['user_id'], 'name': winner['name']}
                    },
                    upsert=True
                )
                _winners.append(await db.casino_winners.find_one({'user_id': winner['user_id']}))
            await db.casino_sessions.update_one({'chat_id': chat_id}, {'$set': {'active': False}})
            text = ['Выпал {} шар'.format(ball[0]), 'Победители:']
            text.extend([' - <a href="tg://user?id={}">{}</a> (побед: {})'.format(x['user_id'], x['name'], x['win_count']) for x in _winners])
            await bot.send_message(chat_id, '\n'.join(text), parse_mode='Html')


casino = Casino()


@dp.message_handler()
async def message_handler(message: types.Message):
    # add chat to db
    update = await db.chats.update_one(
        {'chat_id': message.chat.id},
        {'$set': {'chat_id': message.chat.id}},
        upsert=True)

    if update.upserted_id:
        await casino.new_session(message.chat.id)


@dp.callback_query_handler(lambda x: x.data.startswith('casino:'))
async def casino_pick(callback: types.CallbackQuery):
    chat_id = callback.message.chat.id
    session = await db.casino_sessions.find_one({'chat_id': chat_id, 'active': True})
    if session and callback.from_user.id not in [x['user_id'] for x in session['players']]:
        ball = callback.data.split(':')[1]
        session['players'].append({'user_id': callback.from_user.id, 'name': callback.from_user.first_name, 'ball': ball})
        
        await db.casino_sessions.update_one({'chat_id': chat_id}, {'$set': {'players': session['players']}})

        text = '<a href="tg://user?id={}">{}</a> выбрал {} шар'.format(callback.from_user.id, callback.from_user.first_name, casino.balls[ball][0])
        await bot.send_message(chat_id, text, parse_mode='Html')


async def session_checker():
    sessions = db.casino_sessions.find({'active': True})
    for session in await sessions.to_list(length=100):
        await casino.play_session(session['chat_id'])
        await casino.new_session(session['chat_id'])