import traceback
import hikari
import crescent
import kanade
from kanade import db, utils
import toolbox


plugin = crescent.Plugin()
debug = crescent.Group('debug')


s = lambda x: '🟢' if x else '🔴'


@plugin.include
@debug.child
@crescent.command(
    name='status'
)
async def status(ctx: crescent.Context):
    # TODO: add real values
    await ctx.respond(embed=hikari.Embed(
        title='Status',
        description='\n'.join((
            f'Discord: {s(True)}',
            f'MongoDB: {s(plugin.model.db_connection.is_mongos)}',
            f'SAPI: {s(True)}',
            f'SGDB: {s(False)}'
        )), color=kanade.Colors.WARNING
    ))


@plugin.include
@debug.child
@crescent.hook(kanade.hooks.is_bot_admin)
@crescent.command(
    name='document'
)
class InfoCommand:
    coll = crescent.option(str, description='db\'s collection name')
    doc_id = crescent.option(str, description='document\'s id')

    async def callback(self, ctx: crescent.Context):
        self.doc_id = int(self.doc_id)
        if self.coll == 'guilds':
            data = db.find_document(plugin.model.db_guilds, {'_id': self.doc_id})
        else:
            return await ctx.respond(embed=hikari.Embed(
                title='No collection named {}'.format(self.coll),
                color=kanade.Colors.ERROR
            ))

        if data is None:
            return await ctx.respond(embed=hikari.Embed(
                title='None returned (is DB down?)',
                color=kanade.Colors.ERROR
            ))

        await ctx.respond(embed=hikari.Embed(
            title='mongo > kanade > {} > {}'.format(self.coll, self.doc_id),
            description='```' + '\n'.join(utils.readable_dict(data)) + '```',
            color=kanade.Colors.SUCCESS
        ))


async def plugins_autocomplete(
    ctx: crescent.AutocompleteContext, option: hikari.AutocompleteInteractionOption
):    
    return toolbox.as_command_choices(list(ctx.client.plugins.plugins.keys()))


@plugin.include
@debug.child
@crescent.hook(kanade.hooks.is_bot_admin)
@crescent.command(
    name='reload',
    description='Переазугрузить компонент бота'
)
class ReloadCmd:
    plugin = crescent.option(str, description='Компонент, который необходимо перезагрузить', autocomplete=plugins_autocomplete)

    async def callback(self, ctx: crescent.Context) -> None:
        await ctx.respond(embed=hikari.Embed(
            title='Отгружаю {}'.format(self.plugin),
            color=kanade.Colors.WAIT
        ))

        try:
            ctx.client.plugins.unload(self.plugin)
        except Exception as e:
            tb = traceback.format_exc()
            await ctx.app.rest.create_message(ctx.channel_id, embed=hikari.Embed(
                title='Произошла ошибка!',
                description='При отгрузке произошла ошибка: {}. Полный тб ниже'.format(e),
                color=kanade.Colors.ERROR
            ).add_field(
                'Traceback', '```' + tb + '```'
            ))
        
        await ctx.edit(embed=hikari.Embed(
            title='Подгружаю {}'.format(self.plugin),
            color=kanade.Colors.WAIT
        ))

        try:
            ctx.client.plugins.load(self.plugin)
        except Exception as e:
            tb = traceback.format_exc()
            await ctx.app.rest.create_message(ctx.channel_id, embed=hikari.Embed(
                title='Произошла ошибка!',
                description='При подгрузке произошла ошибка: {}. Полный тб ниже'.format(e),
                color=kanade.Colors.ERROR
            ).add_field(
                'Traceback', '```' + tb + '```'
            ))
        
        await ctx.edit(embed=hikari.Embed(
            title='Перезагрузка завершена!',
            color=kanade.Colors.SUCCESS
        ))