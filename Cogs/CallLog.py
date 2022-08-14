import discord
from discord.ext import commands
from utility import log
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
    
    CLOCK_ICONS = "🕧🕜🕝🕞🕟🕠🕡🕢🕣🕤🕥🕦🕧🕜🕝🕞🕟🕠🕡🕢🕣🕤🕥🕦"
    
    
    def __init__(self, bot: discord.Bot):
        self.bot = bot
    
    
    def get_call_log(self) -> dict[str, dict[str, dict]]:
        """ 통화 기록 파일을 불러온다. """
        call_log = db.reference('call_log').get()
        return call_log
    
    
    def update_call_log(self, user_id: int, action: ActionType, channel: discord.VoiceChannel):
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
    
    
    @commands.slash_command(name="통계", description="모든 유저의 최근 통화방 접속 기록을 조회합니다.")
    async def slash_view_stats(self, ctx: discord.ApplicationContext,
        time_count: discord.Option(int, "최근 n시간의 기록 조회 (수가 클 경우 임베드가 잘릴 수 있음)", min_value=1, max_value=24, default=12)
    ):
        log(f"{CallLog.__name__} - {ctx.author.name}({ctx.author.id})(이)가 /{ctx.command.name} 사용")
        embed = discord.Embed(description="*임베드 생성 중...*", color=0x78b159)
        respond = await ctx.respond(embed=embed)
        call_log = self.get_call_log()
        
        INTERVAL = 60 * 60  # 한 시간 간격
        current = int(time.time())  # 명령어 실행 시각 (측정 시각)
        last_state = dict(zip(call_log.keys(), [ActionType.UNKNOWN] * len(call_log)))  # 이전 상태 저장
        timeline = dict(zip(call_log.keys(), [""] * len(call_log)))  # 유저별 통화 여부가 기록된 문자열 (이모지)
        joined = dict(zip(call_log.keys(), [False] * len(call_log)))  # 시간 구간 내 접속 여부
        
        def add_state(user_id: str, action: ActionType):
            """ 이번 시간의 통화 상태를 기록하고 t에 INTERVAL을 더한다. """
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
        
        ## 모든 유저의 시간대별 상태 기록
        for user_id in call_log.keys():
            
            t = current - (current % INTERVAL) - (time_count-1) * INTERVAL  # t ~ t+INTERVAL 사이의 액션(한 칸)을 측정한다
            
            ## 유저의 모든 액션 조회 (시간순으로 정렬됨)
            actions = call_log[user_id]
            for action_time in actions.keys():
                if t <= int(action_time):  # 측정할 시간보다도 이전에 있는 이벤트는 제외
                    ## 시간 구간 내에 액션이 없을 경우 이전 상태를 전부 채운다
                    if t + INTERVAL <= int(action_time):
                        while t < int(action_time) - int(action_time) % INTERVAL:
                            add_state(user_id, last_state[user_id])
                            t += INTERVAL
                    
                    ## 이벤트가 일어난 전후에는 반드시 JOIN이 존재한다 (예외: 정시에 퇴장)
                    if actions[action_time]["action"] == ActionType.LEAVE and int(action_time) % INTERVAL == 0:
                        add_state(user_id, ActionType.LEAVE)
                    else:
                        add_state(user_id, ActionType.JOIN)
                    t += INTERVAL
                
                ## 이전 상태 저장
                last_state[user_id] = ActionType(actions[action_time]["action"])
            
            ## 마지막 액션 이후 시간은 이전 상태 유지
            while t <= current:
                add_state(user_id, last_state[user_id])
                t += INTERVAL
        
        """ # // (아래는 이전 코드)
        for t in range(current - TIME_COUNT * INTERVAL, current, INTERVAL):
            for id in call_log.keys():  # 유저마다
                
                ## 시간 구간 내에 있는 모든 액션 가져오기
                actions_in_range: list[dict] = []
                for i in range(len(call_log[id])):
                    if t <= call_log[id][i]["time"]:
                        if t + INTERVAL <= call_log[id][i]["time"]:
                            break
                        actions_in_range.append(call_log[id][i])
                    else:
                        last_state[id] = ActionType(call_log[id][i]["action"])
                
                ## 대푯값 산출하기
                if len(actions_in_range) > 0:
                    time_by_action = { ActionType.JOIN: 0, ActionType.LEAVE: 0 }
                    for i in reversed(range(-1, len(actions_in_range))):  # 다음 액션 시각 - 현재 액션 시각 = 현재 액션 지속 시간
                        next_time = actions_in_range[i+1]["time"] if i+1 < len(actions_in_range) else t + INTERVAL
                        current_time = actions_in_range[i]["time"] if i >= 0 else t
                        action = actions_in_range[i]["action"] if i >= 0 else 1 - actions_in_range[i+1]["action"]
                        time_by_action[ActionType(action)] += next_time - current_time
                        
                    state = max(time_by_action, key=time_by_action.get)
                    last_state[id] = ActionType(actions_in_range[-1]["action"])
                else:
                    state = last_state[id]
                
                ## 액션을 타임라인에 저장
                match state:
                    case ActionType.JOIN:
                        timeline[id] += '🟩'
                    case ActionType.OTHER_SERVER:
                        timeline[id] += '🟧'
                    case ActionType.LEAVE:
                        timeline[id] += '⬛'
                    case ActionType.UNKNOWN:
                        timeline[id] += '▪️'
        """
        
        ## 출력
        embed.title = f"최근 {time_count}시간의 통화방 접속 기록"
        embed.description = None
        
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
        embed.add_field(name=clock, value='\n'.join([timeline[id] for id in user_ids]))
        
        embed.set_footer(text="🟩 통화 중  ⬛ 나감  ▪️ 알 수 없음", icon_url=self.bot.user.display_avatar.url, )
        embed.timestamp = datetime.now(timezone('Asia/Seoul'))
        await respond.edit_original_message(embed=embed)


def setup(bot: discord.Bot):
    try:
        bot.add_cog(CallLog(bot))
        log(f"{CallLog.__name__} 로드")
    except Exception as e:
        log(f"{CallLog.__name__} 로드 실패: \n{e}")
