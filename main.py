import os, asyncio, logging
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiohttp import web
from agent.agent_core import AgentCore
from dotenv import load_dotenv

load_dotenv()
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
if not TOKEN:
    print('Telegram token not set. Put TELEGRAM_BOT_TOKEN into .env. Exiting.')
    raise RuntimeError("Set TELEGRAM_BOT_TOKEN in env")

bot = Bot(token=TOKEN)
dp = Dispatcher()

agent = AgentCore()

@dp.message(Command('start'))
async def cmd_start(msg: types.Message):
    await msg.reply('Привет! Я — твой личный помощник. /help — список команд.')

@dp.message(Command('help'))
async def cmd_help(msg: types.Message):
    await msg.reply('/help — показать это\n/health — состояние агента\n/seed — добавить демо документы в векторное хранилище\nКоманды: search:<запрос>, weather:<город>, calendar:add:<ISOdatetime>|<duration_minutes>|<title> , calendar:list:<days>')

@dp.message(Command('health'))
async def cmd_health(msg: types.Message):
    await msg.reply(agent.health_check())

@dp.message(Command('seed'))
async def cmd_seed(msg: types.Message):
    added = agent.seed_chroma_demo()
    await msg.reply(f'Векторное хранилище инициализировано. Добавлено документов: {added}.')

@dp.message()
async def handle_message(msg: types.Message):
    user_id = str(msg.from_user.id)
    text = msg.text or ''
    agent.memory.append_message(user_id, 'user', text)
    reply = await agent.handle_message(user_id, text)
    agent.memory.append_message(user_id, 'assistant', reply)
    await msg.reply(reply)

async def start_http_health(app):
    async def healthz(request):
        return web.Response(text='ok')
    app['runner'] = web.AppRunner(app)
    await app['runner'].setup()
    site = web.TCPSite(app['runner'], '0.0.0.0', int(os.getenv('PORT', '8080')))
    await site.start()

async def main_async():
    logging.basicConfig(level=logging.INFO)
    # HTTP health server
    http_app = web.Application()
    http_app.router.add_get('/healthz', lambda request: web.Response(text='ok'))
    await start_http_health(http_app)
    # Telegram polling
    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main_async())
