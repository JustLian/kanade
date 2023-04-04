import crescent
from kanade import db
import logging
import hikari


plugin = crescent.Plugin()


@plugin.include
@crescent.event
async def fetch_guilds(_: hikari.ShardReadyEvent):
    defaults = db.defaults('guilds')
    async for g in plugin.client.app.rest.fetch_my_guilds():
        data = db.find_document(plugin.model.db_guilds, {'_id': g.id})

        if data is None:
            data = db.defaults('guilds')
            data['_id'] = g.id
            db.insert_document(plugin.model.db_guilds, data)

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
                db.update_document(
                    plugin.model.db_guilds,
                    {'_id': data['_id']},
                    data
                )