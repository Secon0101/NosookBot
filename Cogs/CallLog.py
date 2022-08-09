import discord
from discord.ext import commands
from utility import log
import time
import json
import os
from enum import Enum


class ActionType(Enum):
    JOIN = 1
    LEAVE = 0

class CallLog(commands.Cog):
    
    CALL_LOG_PATH = 'Data/call_log.json'
    
    def __init__(self, bot: discord.Bot):
        self.bot = bot
        
        # 파일 검사
        if not os.path.exists("Data"):
            log("Data 폴더가 없습니다. 생성 중...")
            os.mkdir("Data")
            log("생성 완료")
        if not os.path.exists(self.CALL_LOG_PATH):
            log("call_log.json 파일이 없습니다. 생성 중...")
            with open(self.CALL_LOG_PATH, 'w') as f:
                json.dump({}, f)
            log("생성 완료")
    
    
    @commands.Cog.listener()
    async def on_voice_state_update(self, member: discord.Member, before: discord.VoiceState, after: discord.VoiceState):
        
        def save_call_log(id: str, action: ActionType):
            with open(self.CALL_LOG_PATH, 'r') as f:
                call_log: dict[str, list] = json.load(f)
            
            if id not in call_log:
                call_log[id] = []
            data = {"time": int(time.time()), "action": action.value}
            call_log[id].append(data)
            
            log(f"{CallLog.__name__} - {data}, 저장 중...")
            with open(self.CALL_LOG_PATH, 'w') as f:
                json.dump(call_log, f, indent=4)
            log(f"{CallLog.__name__} - 저장 완료")
        
        # on join
        if before.channel is None and after.channel is not None:
            save_call_log(str(member.id), ActionType.JOIN)
        
        # on leave
        if before.channel is not None and after.channel is None:
            save_call_log(str(member.id), ActionType.LEAVE)
    
    
    @commands.slash_command(name="기록조회", description="(Owner 전용)")
    @commands.is_owner()
    async def slash_ppap(self, ctx: discord.ApplicationContext):
        log(f"{CallLog.__name__} - {ctx.author.name}({ctx.author.id})(이)가 /{ctx.command.name} 사용")
        await ctx.respond(file=discord.File(self.CALL_LOG_PATH))


def setup(bot: discord.Bot):
    try:
        bot.add_cog(CallLog(bot))
        log(f"{CallLog.__name__} 로드")
    except Exception as e:
        log(f"{CallLog.__name__} 로드 실패: \n{e}")
