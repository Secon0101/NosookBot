import discord
from discord.ext import commands
from utility import log
import time, json, os
from enum import Enum
from datetime import datetime
from pytz import timezone


class ActionType(Enum):
    JOIN = 1
    LEAVE = 0
    UNKNOWN = -1
    OTHER_SERVER = 2


class CallLog(commands.Cog):
    
    CALL_LOG_PATH = 'Data/call_log.json'
    CLOCK_ICONS = "🕧🕜🕝🕞🕟🕠🕡🕢🕣🕤🕥🕦🕧🕜🕝🕞🕟🕠🕡🕢🕣🕤🕥🕦"
    
    
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
    
    
    def get_call_log(self) -> dict[str, list[dict]]:
        """ 통화 기록 파일을 불러온다. """
        with open(self.CALL_LOG_PATH, 'r') as f:
            call_log = json.load(f)
        return call_log
    
    
    def update_call_log(self, id: str, action: ActionType, channel: discord.VoiceChannel):
        """ 통화 기록을 업데이트하고 저장한다. """
        call_log = self.get_call_log()
        
        if id not in call_log:
            call_log[id] = []
        data = {"time": int(time.time()), "action": action.value, "channel": channel.id}
        call_log[id].append(data)
        
        log(f"{CallLog.__name__} - {data}, 저장 중...")
        with open(self.CALL_LOG_PATH, 'w') as f:
            json.dump(call_log, f, indent=4)
        log(f"{CallLog.__name__} - 저장 완료")
    
    
    @commands.Cog.listener()
    async def on_voice_state_update(self, member: discord.Member, before: discord.VoiceState, after: discord.VoiceState):
        # on join
        if before.channel is None and after.channel is not None:
            self.update_call_log(str(member.id), ActionType.JOIN, after.channel)
        # on leave
        if before.channel is not None and after.channel is None:
            self.update_call_log(str(member.id), ActionType.LEAVE, before.channel)
    
    
    @commands.slash_command(name="파일조회", description="(Owner 전용)")
    @commands.is_owner()
    async def slash_view_log_file(self, ctx: discord.ApplicationContext):
        log(f"{CallLog.__name__} - {ctx.author.name}({ctx.author.id})(이)가 /{ctx.command.name} 사용")
        await ctx.respond(file=discord.File(self.CALL_LOG_PATH))
    
    
    @commands.slash_command(name="통계", description="최근 22시간의 모든 유저의 통화방 접속 여부를 조회합니다.")
    async def slash_view_stats(self, ctx: discord.ApplicationContext):
        log(f"{CallLog.__name__} - {ctx.author.name}({ctx.author.id})(이)가 /{ctx.command.name} 사용")
        respond = await ctx.respond("*임베드 생성 중...*")
        call_log = self.get_call_log()
        
        INTERVAL = 60 * 60  # 한 시간 간격
        TIME_COUNT = 22  # 최근 22시간을 계산 (이 이상은 임베드가 짤림)
        current = int(time.time())  # 명령어 실행 시각 (측정 시각)
        timeline = dict(zip(call_log.keys(), [""] * len(call_log)))  # 유저별 통화 여부가 기록된 문자열 (이모지)
        last_state = dict(zip(call_log.keys(), [ActionType.UNKNOWN] * len(call_log)))  # 이전 상태 저장
        
        def add_state(id: str, action: ActionType):
            """ 이번 시간의 통화 상태를 기록하고 t에 INTERVAL을 더한다. """
            match action:
                case ActionType.JOIN:
                    timeline[id] += '🟩'
                case ActionType.OTHER_SERVER:
                    timeline[id] += '🟧'
                case ActionType.LEAVE:
                    timeline[id] += '⬛'
                case ActionType.UNKNOWN:
                    timeline[id] += '▪️'
        
        ## 모든 유저의 시간대별 상태 기록
        for id in call_log.keys():
            
            t = current - (current % INTERVAL) - (TIME_COUNT-1) * INTERVAL  # t ~ t+INTERVAL 사이의 액션(한 칸)을 측정한다
            
            ## 유저의 모든 액션 조회 (시간순으로 정렬됨)
            for action in call_log[id]:
                if t <= action["time"]:  # 측정할 시간보다도 이전에 있는 이벤트는 제외
                    ## 시간 구간 내에 액션이 없을 경우 이전 상태를 전부 채운다
                    if t + INTERVAL <= action["time"]:
                        while t < action["time"] - action["time"] % INTERVAL:
                            add_state(id, last_state[id])
                            t += INTERVAL
                    
                    ## 이벤트가 일어난 전후에는 반드시 JOIN이 존재한다 (예외: 정시에 퇴장)
                    if action["action"] == ActionType.LEAVE and action["time"] % INTERVAL == 0:
                        add_state(id, ActionType.LEAVE)
                        t += INTERVAL
                    else:
                        add_state(id, ActionType.JOIN)
                        t += INTERVAL
                
                ## 이전 상태 저장
                last_state[id] = ActionType(action["action"])
            
            ## 마지막 액션 이후 시간은 이전 상태 유지
            while t <= current:
                add_state(id, last_state[id])
                t += INTERVAL
        
        # // (아래는 이전 코드)
        """
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
        embed = discord.Embed(title=f"최근 {TIME_COUNT}시간의 통화방 접속 기록")
        
        users: list[discord.User] = []
        for id in call_log.keys():
            user = await self.bot.fetch_user(int(id))
            if user is None: continue
            users.append(user)
        user_str = '\n'.join(['ㅤ'] + [user.name for user in users])
        embed.add_field(name="유저", value=user_str)
        
        hour = datetime.fromtimestamp(current, timezone('Asia/Seoul')).hour
        clock, i = "", hour
        for _ in range(TIME_COUNT):
            clock = self.CLOCK_ICONS[i] + clock
            i = (i - 1) % 24
        timeline_str = '\n'.join([clock] + [timeline[id] for id in timeline.keys()])
        embed.add_field(name="타임라인", value=timeline_str)
        
        embed.set_footer(text="🟩 통화 중  ⬛ 나감  ▪️ 알 수 없음", icon_url=self.bot.user.display_avatar.url)
        
        await respond.edit_original_message(content=None, embed=embed)


def setup(bot: discord.Bot):
    try:
        bot.add_cog(CallLog(bot))
        log(f"{CallLog.__name__} 로드")
    except Exception as e:
        log(f"{CallLog.__name__} 로드 실패: \n{e}")
