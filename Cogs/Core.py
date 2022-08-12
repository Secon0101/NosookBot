import discord
from discord.ext import commands
from utility import get_cogs, log


class Core(commands.Cog):
    """ 노숙봇 핵심 기능들 """
    def __init__(self, bot: discord.Bot):
        self.bot = bot
        self.version = "0.1"
    
    
    @commands.Cog.listener()
    async def on_ready(self):
        log(f"{self.bot.user}(으)로 로그인 (서버 {len(self.bot.guilds)}개)\n")
        await self.bot.change_presence(activity=discord.Game(name="노숙"))
    
    
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
    
    
    @commands.slash_command(name="노숙봇", description="노숙 하는 중")
    async def slash_info(self, ctx: discord.ApplicationContext):
        log(f"{Core.__name__} - {ctx.author.name}({ctx.author.id})(이)가 /{ctx.command.name} 사용")
        embed = discord.Embed(title="노숙봇", description=f"v{self.version}")
        embed.set_thumbnail(url=self.bot.user.display_avatar.url)
        await ctx.respond(embed=embed)


def setup(bot: discord.Bot):
    try:
        bot.add_cog(Core(bot))
        log(f"{Core.__name__} 로드")
    except Exception as e:
        log(f"{Core.__name__} 로드 실패: \n{e}")
