from bot.bot import executor, dp, punch_session_start, DELAY
import asyncio


if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.call_later(DELAY, punch_session_start, loop)
    executor.start_polling(dp, loop=loop)
