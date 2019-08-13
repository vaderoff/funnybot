from bot.bot import executor, dp, session_checker, DELAY
import asyncio


def repeat(coro, loop):
    asyncio.ensure_future(coro(), loop=loop)
    loop.call_later(DELAY, repeat, coro, loop)


if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    repeat(session_checker, loop)
    executor.start_polling(dp, loop=loop)
