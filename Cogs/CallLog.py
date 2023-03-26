import discord
from discord.ext import commands
from utility import log, log_print
import time
from enum import Enum
from datetime import datetime
from pytz import timezone
from firebase_admin import db


class ActionType(Enum):
    JOIN = 1
    LEAVE = 0
    UNKNOWN = -1
    OTHER_SERVER = 2


class CallLog(commands.Cog):
    """ 통화 기록 및 타임라인 출력 """
    
    CLOCK_ICONS = "🕧🕜🕝🕞🕟🕠🕡🕢🕣🕤🕥🕦🕧🕜🕝🕞🕟🕠🕡🕢🕣🕤🕥🕦"
    
    
    def __init__(self, bot: discord.Bot):
        self.bot = bot
    
    
    @staticmethod
    def get_call_log() -> dict[str, dict[str, dict]]:
        """ 통화 기록 파일을 불러온다. """
        call_log = db.reference('call_log').get()
        return call_log
    
    
    @staticmethod
    def update_call_log(user_id: int, action: ActionType, channel: discord.VoiceChannel):
        """ 통화 기록을 업데이트하고 저장한다. """
        action_time = int(time.time())
        data = {
            "action": action.value,
            "channel": channel.id
        }
        db.reference(f'call_log/{user_id}').update({ action_time: data })
        log(f"{CallLog.__name__} - {user_id} + {{'{action_time}': {data}}}")
    
    
    @commands.Cog.listener()
    async def on_voice_state_update(self, member: discord.Member, before: discord.VoiceState, after: discord.VoiceState):
        # on join
        if before.channel is None and after.channel is not None:
            self.update_call_log(member.id, ActionType.JOIN, after.channel)
        # on leave
        if before.channel is not None and after.channel is None:
            self.update_call_log(member.id, ActionType.LEAVE, before.channel)
    
    
    async def make_timeline_embed(self, time_count: int) -> discord.Embed:
        """ 통화방 접속 기록 임베드를 생성한다. """
        embed = discord.Embed(title=f"최근 {time_count}시간의 통화방 접속 기록", color=0x78b159)
        call_log = self.get_call_log()
        
        interval = 60 * 60  # 한 시간 간격
        current = int(time.time())  # 명령어 실행 시각 (측정 시각)
        last_state = dict(zip(call_log.keys(), [ActionType.UNKNOWN] * len(call_log)))  # 이전 상태 저장
        timeline = dict(zip(call_log.keys(), [""] * len(call_log)))  # 유저별 통화 여부가 기록된 문자열 (이모지)
        joined = dict(zip(call_log.keys(), [False] * len(call_log)))  # 시간 구간 내 접속 여부
        
        def add_state(user_id: str, action: ActionType):
            """ 이번 시간의 통화 상태를 기록하고 t에 interval을 더한다. """
            nonlocal t
            match action:
                case ActionType.JOIN:
                    timeline[user_id] += '🟩'
                    joined[user_id] = True
                case ActionType.OTHER_SERVER:
                    timeline[user_id] += '🟧'
                    joined[user_id] = True
                case ActionType.LEAVE:
                    timeline[user_id] += '⬛'
                case ActionType.UNKNOWN:
                    timeline[user_id] += '▪️'
            t += interval
        
        ## 모든 유저의 시간대별 상태 기록
        for user_id in call_log.keys():
            
            t = current - (current % interval) - (time_count - 1) * interval  # t ~ t+interval 사이의 액션(한 칸)을 측정한다
            
            ## 유저의 모든 액션 조회 (시간순으로 정렬됨)
            actions = call_log[user_id]
            for action_time in actions.keys():
                if t <= int(action_time):  # 측정할 시간보다도 이전에 있는 이벤트는 제외
                    ## 시간 구간 내에 액션이 없을 경우 이전 상태를 전부 채운다
                    if t + interval <= int(action_time):
                        while t < int(action_time) - int(action_time) % interval:
                            add_state(user_id, last_state[user_id])
                    
                    ## 이벤트가 일어난 전후에는 반드시 JOIN이 존재한다 (예외: 정시에 퇴장)
                    if actions[action_time]["action"] == ActionType.LEAVE and int(action_time) % interval == 0:
                        add_state(user_id, ActionType.LEAVE)
                    else:
                        add_state(user_id, ActionType.JOIN)
                
                ## 이전 상태 저장
                last_state[user_id] = ActionType(actions[action_time]["action"])
            
            ## 마지막 액션 이후 시간은 이전 상태 유지
            while t <= current:
                add_state(user_id, last_state[user_id])
        
        user_ids = [id for id in call_log.keys() if joined[id]]  # 접속했던 유저만 표시
        users = []
        for user_id in user_ids:
            user = await self.bot.fetch_user(int(user_id))
            if user is not None:
                users.append(user.name)
        embed.add_field(name="유저", value='\n'.join(users))
        
        hour = datetime.fromtimestamp(current, timezone('Asia/Seoul')).hour
        clock, i = "", hour
        for _ in range(time_count):
            clock = self.CLOCK_ICONS[i] + clock
            i = (i - 1) % 24
        embed.add_field(name=clock, value='\n'.join(timeline[id] for id in user_ids))
        
        embed.set_footer(text="🟩 통화 중  ⬛ 나감  ▪️ 알 수 없음", icon_url=self.bot.user.display_avatar.url, )
        embed.timestamp = datetime.now(timezone('Asia/Seoul'))
        
        return embed
    
    
    @commands.slash_command(name="통계", description="모든 유저의 최근 통화방 접속 기록을 조회합니다.")
    async def slash_view_stats(self, ctx: discord.ApplicationContext,
        time_count: discord.Option(int, "최근 n시간의 기록 조회 (수가 클 경우 임베드가 잘릴 수 있음)", min_value=1, max_value=24, default=12)
    ):
        await log(f"{CallLog.__name__} - {ctx.author.name}({ctx.author.id}) used /{ctx.command.name}")
        embed = discord.Embed(description="*임베드 생성 중...*", color=0x78b159)
        respond = await ctx.respond(embed=embed)
        embed = await self.make_timeline_embed(time_count)
        await respond.edit_original_response(embed=embed)


def setup(bot: discord.Bot):
    try:
        bot.add_cog(CallLog(bot))
        log_print(f"Module {CallLog.__name__} loaded")
    except Exception as e:
        log_print(f"Failed to load module {CallLog.__name__}: \n{e}")
