import hikari
import crescent
from kanade import cfg
from kanade import db
import motor.motor_asyncio


class Model:
    def __init__(self) -> None:
        self.db_connection = db.connect()
        self.db = self.db_connection[cfg['mongo']['db']]
        self.db_users = self.db['users']
        self.db_guilds = self.db['guilds']
    
    async def on_ready(self, _) -> None:
        ...


bot = hikari.GatewayBot(
    cfg['discord']['token'],
    intents=hikari.Intents.ALL
)

model = Model()
bot.event_manager.subscribe(hikari.StartedEvent, model.on_ready)
client = crescent.Client(bot, model=model, default_guild=cfg['discord']['guild'])

client.plugins.load_folder('kanade.plugins')
client.plugins.load('kanade.api.plugin')

def run() -> None:
    bot.run(activity=hikari.Activity(name='リアンさんはかっこいい'))


async def async_run() -> None:
    await bot.start(activity=hikari.Activity(name='リアンさんはかっこいい'))