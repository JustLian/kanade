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