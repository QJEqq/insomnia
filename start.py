from aiogram import Bot , Dispatcher
import asyncio
from apps.handlers import user_router
from database.models import init_models
from dotenv import load_dotenv
import os


async def main() :
    dp = Dispatcher()
    load_dotenv()
    bot = Bot(token=os.getenv('TOKEN'))
    dp.startup.register(start_up)
    dp.shutdown.register(shutdown)
    dp.include_router(user_router)
    await dp.start_polling(bot)
    
async def start_up( dispatcher : Dispatcher) :
    await init_models()
    print("Starting...")
    
async def shutdown( dispatcher : Dispatcher) :
    print("Closing...")
    
if __name__ == '__main__' :
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print('Exit')
    