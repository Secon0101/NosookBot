import discord
from discord.ext import commands
from utility import get_cogs, log


class System(commands.Cog):
    def __init__(self, bot: discord.Bot):
        self.bot = bot
    
    
    @commands.slash_command(name="리로드", description="(Owner 전용)")
    @commands.is_owner()
    async def slash_reload(self, ctx: discord.ApplicationContext):
        log("리로드 중...")
        for cog in get_cogs():
            self.bot.unload_extension(cog)
            self.bot.load_extension(cog)
        log("리로드 완료", newline=True)
        respond = await ctx.respond("🔄 봇을 리로드하였습니다.")
        await respond.delete_original_message(delay=2)


def setup(bot: discord.Bot):
    try:
        bot.add_cog(System(bot))
        log(f"{System.__name__} 로드")
    except Exception as e:
        log(f"{System.__name__} 로드 실패: \n{e}")
