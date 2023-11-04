import crescent
import hikari
import fastapi
import kanade
import uvicorn
import asyncio


plugin = crescent.Plugin[hikari.GatewayBot, None]()
app = fastapi.FastAPI()


from kanade.api import main
main.load(app, plugin)
