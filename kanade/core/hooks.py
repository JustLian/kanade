import crescent
import hikari
import kanade
import toolbox


async def is_bot_admin(ctx: crescent.Context) -> crescent.HookResult:
    if ctx.user.id not in [
        462223918451916810, 861955483841462292
    ]:
        await ctx.edit(
            embed=hikari.Embed(
                title='Нет прав',
                description='Эту команду могут использовать только жасти лиан и мама',
                color=kanade.Colors.ERROR
            )
        )
        return crescent.HookResult(exit=True)
    return crescent.HookResult()


async def is_server_manager(ctx: crescent.Context) -> crescent.HookResult:
    fetched_member = await ctx.app.rest.fetch_member(ctx.guild, ctx.user)
    permissions = toolbox.calculate_permissions(fetched_member)
    if (permissions & hikari.Permissions.MANAGE_GUILD) == (hikari.Permissions.MANAGE_GUILD):
        return crescent.HookResult()

    await ctx.respond(embed=hikari.Embed(
            title='Нет прав',
            description='Для использования этой команды необходимо быть менеджером сервера',
            color=kanade.Colors.ERROR
        )
    )
    return crescent.HookResult(exit=True)