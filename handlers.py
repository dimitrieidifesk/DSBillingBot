from init_bot import bot
from core.config import config
import discord
from discord.ui import Button
from discord.ext import commands
from loguru import logger
from db.sqlite import SQLite
from db.init_db import db
from core.yookassa_provider import Yookassa_Provider
import asyncio
from worker import check_payments, take_away_overdue_roles


async def start_worker_proccess():
    await bot.wait_until_ready()
    while True:
        await check_payments(MAIN_GUILD)
        await take_away_overdue_roles(MAIN_GUILD)
        await asyncio.sleep(10)


async def handle_messages(queue):
    while True:
        user_id, message = queue.get()
        logger.info("handle_messages принял команду")
        user = await bot.fetch_user(user_id)
        await user.send(message)


@bot.command()
@commands.has_role(config.ADMIN_ROLE_NAME)
async def add_role_to_sale(ctx, role_tag: discord.Role, cost):
    """Добавление роли в продажу - пользователи смогут купить роль"""
    role_name = ctx.guild.get_role(role_tag.id)
    with SQLite(db) as sqlite:
        sqlite.add_role(role_name=role_name, role_id=role_tag.id, price=cost)
    await ctx.send(f'Роль {role_name} добавлена в продажу за {cost} RUB')


@bot.command()
@commands.has_role(config.ADMIN_ROLE_NAME)
async def remove_role_from_sale(ctx, role_tag: discord.Role):
    """Удаление роли из продажи - пользователи НЕ смогут купить роль"""
    role_name = ctx.guild.get_role(role_tag.id)
    with SQLite(db) as sqlite:
        sqlite.remove_role(role_id=role_tag.id)
    await ctx.send(f'Роль {role_name} удалена из продажи! Её больше не могут купить.')


@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.MissingRequiredArgument):
        parameter_name = error.param.name
        error_message = f"Необходимо передать параметр {parameter_name}."
        await ctx.send(error_message)
    elif isinstance(error, commands.CommandNotFound):
        await ctx.send("Команда не найдена.")
    elif isinstance(error, commands.MissingRole):
        await ctx.send(f'У вас нет доступа к этой команде. Требуется роль {config.ADMIN_ROLE_NAME}.')
    else:
        # Обработка других ошибок
        await ctx.send("Произошла ошибка при выполнении команды.")


@bot.command()
async def roles(ctx):
    "Показать список доступных для покупки ролей"
    embed = discord.Embed(title="Доступные роли",
                          description="Выберите подходящую для вас роль",
                          color=discord.Color.blue())

    with SQLite(db) as sqlite:
        saled_roles = sqlite.get_saled_roles()
    logger.info(saled_roles)
    buttons = []
    for i, saled_role in enumerate(saled_roles):
        embed.add_field(name=f"{i + 1}. @{saled_role['role_name']}", value=f"{saled_role['price_rub']} руб/месяц",
                        inline=False)
        buttons.append(Button(custom_id=f"{saled_role['role_id']}", label=f"{saled_role['role_name']}",
                              style=discord.ButtonStyle.primary))

    async def button_callback(interaction):
        role_id = interaction.data["custom_id"]
        label = "None"
        for component in interaction.message.components:
            for button in component.children:
                if button.custom_id == role_id:
                    label = button.label
                    break
        user_id = interaction.user.id
        user = await bot.fetch_user(user_id)  # Получаем объект пользователя по его ID
        price_rub = None
        for role in saled_roles:
            if role['role_name'] == label:
                price_rub = role['price_rub']
                break
        if not (price_rub):
            await user.send("Произошла внутренняя ошибка. Уже решаем эту проблему. Попробуйте выбрать другую роль.")
            raise Exception(f"Ошибка в указании цены на роль {label}")

        confirmation_url = await Yookassa_Provider().pay_request(user_id, role_id, label, price_rub)

        message = f"Привет {user.mention}! Оплатите роль {label} на 1 месяц. \n Вот ссылка на оплату {confirmation_url} \n Выдача роли произойдет автоматически! 🙏"

        await user.send(message)

    view = discord.ui.View()
    for button in buttons:
        button.callback = button_callback
        view.add_item(button)

    await ctx.send(embed=embed, view=view)


@bot.event
async def on_ready():
    print(f'Logged in as {bot.user.name}')
    global MAIN_GUILD
    MAIN_GUILD = bot.get_guild(config.DISCORD_SERVER_ID)
    bot.loop.create_task(start_worker_proccess())
