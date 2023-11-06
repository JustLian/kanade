import typing
import hikari
import crescent
import fastapi
from pydantic import BaseModel
from kanade.core.bot import Model
import kanade
import hashlib


def generate_key(api_id: str) -> str:
    return hashlib.sha256(
        (kanade.cfg['api']['api_secret'] + api_id).encode('utf8')
    ).hexdigest()


def authenticate_user(apiKey: str = fastapi.Header(None), apiId: str = fastapi.Header(None)):
    if (
        apiKey is None
        or apiId is None
        or generate_key(apiId) != apiKey
    ):
        raise fastapi.HTTPException(status_code=401, detail="Unauthorized")

    return (apiKey, apiId)


class getGuildSettingsPayload(BaseModel):
    guild_id: int


class getGuildChannelsPayload(BaseModel):
    guild_id: int
    channel_type: typing.Literal['text', 'voice', 'both']


class generateTokenPayload(BaseModel):
    user_id: int
    secret: str


class checkAccessPayload(BaseModel):
    guild_id: int


class editGuildDataPayload(BaseModel):
    guild_id: int
    data: dict


def get_icon(guild) -> str:
    if guild.icon_url is None:
        return "https://cdn.prod.website-files.com/6257adef93867e50d84d30e2/636e0a6cc3c481a15a141738_icon_clyde_white_RGB.png"
    else:
        return guild.icon_url.url


def convert_ints_to_str(data):
    if type(data) == int:
        return str(data)
    if isinstance(data, dict):
        return {key: convert_ints_to_str(value) for key, value in data.items()}
    if isinstance(data, list):
        return [convert_ints_to_str(item) for item in data]
    return data


def load(app: fastapi.FastAPI, plugin: crescent.Plugin[hikari.GatewayBot, Model]) -> None:
    async def has_access(user_id, guild_id) -> bool:
        guild = await plugin.model.db_guilds.find_one({'_id': guild_id})
        if guild is None:
            return False

        return (int(user_id) in guild['managers']) or (guild['owner'] == int(user_id))

    @app.get('/')
    async def root():
        return {'message': 'Kanade API v1.0a (restricted access)'}
    

    @app.get('/getGuildData/{guild_id}')
    async def get_guild_data(guild_id: int):
        guild = plugin.app.cache.get_guild(guild_id)
        if guild is None:
            guild = await plugin.app.rest.fetch_guild(guild_id)

        return {"name": guild.name, "img": get_icon(guild)}


    @app.post('/generateToken')
    async def generate_users_token(
        payload: generateTokenPayload
    ):
        if payload.secret != kanade.cfg['api']['api_secret']:
            raise fastapi.HTTPException(status_code=401, detail='Wrong api secret.')

        return {'token': generate_key(str(payload.user_id))}

    
    @app.post('/checkGuilds')
    async def check_user_guilds(
        api_data = fastapi.Depends(authenticate_user)
    ):
        ids = []
        
        async for doc in plugin.model.db_guilds.find(
            {"$or": [
                {"managers": [int(api_data[1])]},
                {"owner": int(api_data[1])}
            ]},
            {'_id': 1}
        ):
            ids.append(doc['_id'])

        result = []
        for guild_id in ids:
            guild = plugin.app.cache.get_guild(guild_id)
            if guild is None or guild.icon_url is None:
                guild = await plugin.app.rest.fetch_guild(guild_id)

            result.append({'id': str(guild.id), 'name': guild.name, 'img': get_icon(guild)})

        return result

    @app.post('/getGuildChannels')
    async def get_guild_channels(
        payload: getGuildChannelsPayload,
        api_data = fastapi.Depends(authenticate_user)
    ):
        if not (await has_access(api_data[1], payload.guild_id)):
            raise fastapi.HTTPException(status_code=401, detail="Unauthorized")
        
        result = []

        for channel in await plugin.app.rest.fetch_guild_channels(payload.guild_id):
            if channel.type != hikari.ChannelType.GUILD_TEXT:
                continue
            result.append((str(channel.id), channel.name))

        return result
    
    @app.post('/getGuildSettings')
    async def get_guild_settings(
        payload: getGuildSettingsPayload,
        api_key: str = fastapi.Depends(authenticate_user)
    ) -> dict:
        settings = await plugin.model.db_guilds.find_one({'_id': int(payload.guild_id)})
        return {'result': convert_ints_to_str(settings)}


    @app.patch('/updateGuildData')
    async def edit_guild_data(
        payload: editGuildDataPayload,
        api_data = fastapi.Depends(authenticate_user)
    ):
        if not (await has_access(api_data[1], payload.guild_id)):
            raise fastapi.HTTPException(status_code=401, detail="Unauthorized")

        result = await plugin.model.db_guilds.update_one(
            {'_id': payload.guild_id},
            {'$set': payload.data}
        )

        return {'modified': result.modified_count}
