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
    help_text = """🤖 Команды бота:
/help — показать это
/health — состояние агента  
/seed — добавить демо документы в векторное хранилище
/sessions — показать активные сессии (только для админов)

💬 Команды сообщений:
search:<запрос> — поиск в интернете
weather:<город> — погода
calendar:add:<ISOdatetime>|<duration_minutes>|<title> — добавить событие
calendar:list:<days> — показать события
calendar:test — проверить настройку Google Calendar

🔄 Бот поддерживает множественные чаты одновременно!"""
    await msg.reply(help_text)

@dp.message(Command('health'))
async def cmd_health(msg: types.Message):
    await msg.reply(agent.health_check())

@dp.message(Command('seed'))
async def cmd_seed(msg: types.Message):
    added = agent.seed_chroma_demo()
    await msg.reply(f'Векторное хранилище инициализировано. Добавлено документов: {added}.')

@dp.message(Command('sessions'))
async def cmd_sessions(msg: types.Message):
    """Show active user sessions (admin only)"""
    user_id = str(msg.from_user.id)
    # Simple admin check - you can improve this
    if user_id in ['1112627045']:  # Replace with your admin user ID
        sessions = list(agent.active_sessions)
        if sessions:
            await msg.reply(f'Активные сессии ({len(sessions)}):\n' + '\n'.join(sessions[:10]))
        else:
            await msg.reply('Нет активных сессий.')
    else:
        await msg.reply('У вас нет прав для просмотра сессий.')

@dp.message()
async def handle_message(msg: types.Message):
    user_id = str(msg.from_user.id)
    text = msg.text or ''
    
    # Log user activity
    logging.info(f"Message from user {user_id}: {text[:50]}...")
    
    # Save user message
    agent.memory.append_message(user_id, 'user', text)
    
    try:
        # Process message asynchronously
        reply = await agent.handle_message(user_id, text)
        
        # Save assistant response
        agent.memory.append_message(user_id, 'assistant', reply)
        
        # Send reply
        await msg.reply(reply)
        
    except Exception as e:
        logging.exception(f"Error handling message from user {user_id}")
        error_msg = f"Произошла ошибка при обработке сообщения: {str(e)}"
        agent.memory.append_message(user_id, 'assistant', error_msg)
        await msg.reply(error_msg)

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
