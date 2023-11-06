import hikari
import crescent
from kanade.core.bot import Model


plugin = crescent.Plugin[hikari.GatewayBot, Model]()

title_exceeded = "🔴🔴🔴 Заголовок превысил 256 символов.\n\n"
description_exceeded = "🔴🔴🔴 Описание превысило 4096 символов.\n\n"