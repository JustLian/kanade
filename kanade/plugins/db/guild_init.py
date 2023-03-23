import crescent
from kanade import db
import logging
import hikari


plugin = crescent.Plugin()


@plugin.include
@crescent.event
async def fetch_guilds(_: hikari.ShardReadyEvent):
    async for g in plugin.client.app.rest.fetch_my_guilds():
        data = db.find_document(plugin.model.db_guilds, {'_id': g.id})

        if data is None:
            data = db.defaults('guilds')
            data['_id'] = g.id
            db.insert_document(plugin.model.db_guilds, data)