import crescent
from kanade.core.bot import Model
from kanade import db
import logging
import hikari


plugin = crescent.Plugin[hikari.GatewayBot, Model]()


async def fetch_guild(g: hikari.Guild):
    defaults = db.defaults('guilds')
    data = await plugin.model.db_guilds.find_one({'_id': g.id})

    if data is None:
        data = db.defaults('guilds')
        data['_id'] = g.id
        await plugin.model.db_guilds.insert_one(data)
    else:
        upd = False
        for l1_key in defaults.keys():
            if l1_key not in data:
                upd = True
                data[l1_key] = defaults[l1_key]
            
            elif isinstance(defaults[l1_key], dict):
                for l2_key in defaults[l1_key].keys():
                    if l2_key not in data[l1_key]:
                        upd = True
                        data[l1_key][l2_key] = defaults[l1_key][l2_key]
        if upd:
            await plugin.model.db_guilds.update_one(
                {'_id': data['_id']},
                {'$set': data}
            )
    
    await plugin.model.db_guilds.update_one(
        {'_id': g.id},
        {'$set': {'owner': g.owner_id if hasattr(g, 'owner_id') else (await g.fetch_self()).owner_id}}
    )


@plugin.include
@crescent.event
async def fetch_guilds(_: hikari.ShardReadyEvent):
    async for g in plugin.client.app.rest.fetch_my_guilds():
        await fetch_guild(g)


@plugin.include
@crescent.event
async def new_guild_added(event: hikari.GuildJoinEvent):
    await fetch_guild(await event.fetch_guild())


@plugin.include
@crescent.event
async def user_left(event: hikari.MemberDeleteEvent):
    prev_managers = (await plugin.model.db_guilds.find_one({'_id': event.guild_id}, {'managers': 1}))['managers']
    if event.user_id in prev_managers:
        prev_managers.remove(event.user_id)
        await plugin.model.db_guilds.update_one({'_id': event.guild_id}, {'$set': {'managers': prev_managers}})