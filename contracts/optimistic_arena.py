# { "Depends": "py-genlayer:test" }

from dataclasses import dataclass
from genlayer import *

@allow_storage
@dataclass
class SessionInfo:
    host: Address
    max_players: u256
    member_count: u256
    round_no: u256
    prompt: str


class OptimisticArena(gl.Contract):
    # --- on-chain storage (ВАЖНО: не dict/list/int) ---
    next_session_id: u256
    session_host: TreeMap[u256, Address]
    session_max_players: TreeMap[u256, u256]
    session_member_count: TreeMap[u256, u256]
    session_round_no: TreeMap[u256, u256]
    session_prompt: TreeMap[u256, str]

    season_xp: TreeMap[Address, u256]

    def __init__(self):
        # Конструктор НЕ помечают @write/@view (он "приватный" по смыслу доки).
        # Инициализируем счетчик, потому что по умолчанию storage может быть 0.
        if self.next_session_id == u256(0):
            self.next_session_id = u256(1)

    @write
    def create_session(self, host: Address, max_players: u256) -> u256:
        sid = self.next_session_id
        self.next_session_id = sid + u256(1)

        self.session_host[sid] = host
        self.session_max_players[sid] = max_players
        self.session_member_count[sid] = u256(0)
        self.session_round_no[sid] = u256(0)
        self.session_prompt[sid] = ""

        return sid

    @write
    def join_session(self, session_id: u256) -> None:
        # “Кто вызывает транзакцию” в разных SDK может называться по-разному.
        # Чтобы не упереться в непонятные sender/caller на этом шаге,
        # мы принимаем join как "просто увеличить счетчик участников".
        #
        # На следующем шаге сделаем нормально: ключи вида session_id+address.
        cur = self.session_member_count.get(session_id, u256(0))
        maxp = self.session_max_players[session_id]

        if cur >= maxp:
            raise UserError("Session is full")

        self.session_member_count[session_id] = cur + u256(1)

    @write
    def start_round(self, session_id: u256) -> str:
        r = self.session_round_no.get(session_id, u256(0)) + u256(1)
        self.session_round_no[session_id] = r

        # На первом шаге делаем детерминированно, чтобы 100% завелось.
        # На втором шаге заменим на LLM через nondet (по доке Intelligent Contracts).
        prompt = "Explain GenLayer as if you are a sports commentator. (1 sentence)"

        self.session_prompt[session_id] = prompt
        return prompt

    @write
    def add_xp(self, player: Address, amount: u256) -> None:
        cur = self.season_xp.get(player, u256(0))
        self.season_xp[player] = cur + amount

    @view
    def get_session(self, session_id: u256) -> SessionInfo:
        return SessionInfo(
            host=self.session_host[session_id],
            max_players=self.session_max_players[session_id],
            member_count=self.session_member_count.get(session_id, u256(0)),
            round_no=self.session_round_no.get(session_id, u256(0)),
            prompt=self.session_prompt.get(session_id, ""),
        )

    @view
    def get_xp(self, player: Address) -> u256:
        return self.season_xp.get(player, u256(0))
