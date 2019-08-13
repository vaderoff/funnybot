from bot.bot import executor, dp, punch_session_start, DELAY
import asyncio


def repeat(coro, loop):
    asyncio.ensure_future(coro(), loop=loop)
    loop.call_later(DELAY, repeat, coro, loop)


if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    repeat(punch_session_start, loop)
    executor.start_polling(dp, loop=loop)
