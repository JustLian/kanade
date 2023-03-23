import hikari
import crescent
import miru
from kanade import cfg
from kanade import db
from osu import AsynchronousClient


class Model:
    def __init__(self) -> None:
        self.db_connection = db.connect()
        self.db_users = self.db_connection.get_database(cfg['mongo']['db']).get_collection('users')
        self.db_guilds = self.db_connection.get_database(cfg['mongo']['db']).get_collection('guilds')
    
    async def on_ready(self, _) -> None:
        ...


bot = hikari.GatewayBot(
    cfg['discord']['token'],
    intents=hikari.Intents.ALL
)

miru.install(bot)
model = Model()
bot.event_manager.subscribe(hikari.StartedEvent, model.on_ready)
client = crescent.Client(bot, model=model, default_guild=cfg['discord']['guild'])

client.plugins.load_folder('kanade.plugins')

def run() -> None:
    bot.run(activity=hikari.Activity(name='リアンさんはかっこいい'))