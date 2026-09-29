import os
import discord
from discord import app_commands
from discord.ext import commands
from typing import Optional

# Настройка интентов. 
# voice_states нужен для отслеживания входа в каналы (для декор-войса)
# members нужен для поиска пользователей по @упоминанию
intents = discord.Intents.default()
intents.members = True
intents.voice_states = True 

class VoiceBot(commands.Bot):
    def __init__(self):
        super().__init__(command_prefix="!", intents=intents)
        # Переменная для хранения ID декоративного канала в памяти
        self.decor_voice_id: Optional[int] = None

    async def setup_hook(self):
        # Автоматическая синхронизация слеш-команд при запуске
        await self.tree.sync()
        print("Слеш-команды успешно синхронизированы.")

bot = VoiceBot()

@bot.event
async def on_ready():
    print(f"Бот {bot.user} успешно запущен и готов к работе!")

# Событие: автоматический кик при заходе в декоративный канал
@bot.event
async def on_voice_state_update(member: discord.Member, before: discord.VoiceState, after: discord.VoiceState):
    if bot.decor_voice_id and after.channel and after.channel.id == bot.decor_voice_id:
        if member.id == bot.user.id:
            return  # Бот не кикает сам себя
            
        try:
            # Кикаем из войса (перемещаем в None)
            await member.move_to(None, reason="Вход в декоративный голосовой канал.")
            print(f"Пользователь {member.name} был исключен из декоративного канала.")
        except discord.Forbidden:
            print(f"Ошибка прав: у бота нет разрешения 'Перемещать участников' (Move Members).")
        except discord.HTTPException:
            pass

# 1. КОМАНДА: Настройка декоративного войса
@bot.tree.command(name="декор-войс", description="Сделать голосовой канал исключительно декоративным (вход запрещен)")
@app_commands.describe(channel="Выберите голосовой канал")
@app_commands.checks.has_permissions(manage_channels=True)
async def set_decor_voice(interaction: discord.Interaction, channel: discord.VoiceChannel):
    bot.decor_voice_id = channel.id
    await interaction.response.send_message(
        f"🖼️ Канал {channel.mention} теперь **декоративный**. Бот будет автоматически исключать всех входящих."
    )

# 2. КОМАНДА: Мут в голосовом канале
@bot.tree.command(name="мут-войс", description="Заглушить пользователя в голосовом канале")
@app_commands.describe(user="Пользователь, которого нужно заглушить")
@app_commands.checks.has_permissions(mute_members=True)
async def mute_voice(interaction: discord.Interaction, user: discord.Member):
    if not user.voice or not user.voice.channel:
        await interaction.response.send_message(f"❌ {user.mention} не находится в голосовом канале.", ephemeral=True)
        return

    try:
        await user.edit(mute=True)
        await interaction.response.send_message(f"🤫 {user.mention} был заглушен в голосовом канале.")
    except discord.Forbidden:
        await interaction.response.send_message("❌ У бота недостаточно прав (Mute Members).", ephemeral=True)
    except discord.HTTPException:
        await interaction.response.send_message("❌ Ошибка при выполнении команды.", ephemeral=True)

# 3. КОМАНДА: Размут в голосовом канале
@bot.tree.command(name="размут-войс", description="Снять заглушение с пользователя в голосовом канале")
@app_commands.describe(user="Пользователь, с которого нужно снять заглушение")
@app_commands.checks.has_permissions(mute_members=True)
async def unmute_voice(interaction: discord.Interaction, user: discord.Member):
    if not user.voice or not user.voice.channel:
        await interaction.response.send_message(f"❌ {user.mention} не находится в голосовом канале.", ephemeral=True)
        return

    try:
        await user.edit(mute=False)
        await interaction.response.send_message(f"🔊 С {user.mention} снято заглушение в голосовом канале.")
    except discord.Forbidden:
        await interaction.response.send_message("❌ У бота недостаточно прав (Mute Members).", ephemeral=True)
    except discord.HTTPException:
        await interaction.response.send_message("❌ Ошибка при выполнении команды.", ephemeral=True)

# Обработка ошибок прав доступа для всех команд
@set_decor_voice.error
@mute_voice.error
@unmute_voice.error
async def permissions_error_handler(interaction: discord.Interaction, error: app_commands.AppCommandError):
    if isinstance(error, app_commands.MissingPermissions):
        await interaction.response.send_message(
            "❌ У вас недостаточно прав для использования этой команды.", 
            ephemeral=True
        )

# Безопасный запуск: берет токен из переменной окружения хостинга
TOKEN = os.environ.get('DISCORD_TOKEN')
if TOKEN:
    bot.run(TOKEN)
else:
    print("КРИТИЧЕСКАЯ ОШИБКА: Переменная окружения 'DISCORD_TOKEN' не найдена!")

