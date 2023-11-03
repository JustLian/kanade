import asyncio
from kanade.core import bot
from kanade.api import plugin
import kanade
import uvicorn


@plugin.app.on_event('startup')
async def startup_event():
    asyncio.create_task(bot.async_run())


uvicorn.run(plugin.app, host=kanade.cfg['api']['host'], port=kanade.cfg['api']['port'])