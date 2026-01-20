# { "Depends": "py-genlayer:test" }

from genlayer import gl, write, view, u256, Address, TreeMap, UserError


class OptimisticArena(gl.Contract):
    next_session_id: u256
    session_host: TreeMap[u256, Address]
    session_max_players: TreeMap[u256, u256]
    session_member_count: TreeMap[u256, u256]
    session_round_no: TreeMap[u256, u256]
    session_prompt: TreeMap[u256, str]
    season_xp: TreeMap[Address, u256]

    @write
    def create_session(self, host: Address, max_players: u256) -> u256:
        sid = self.next_session_id
        if sid == u256(0):
            sid = u256(1)
        self.next_session_id = sid + u256(1)

        self.session_host[sid] = host
        self.session_max_players[sid] = max_players
        self.session_member_count[sid] = u256(0)
        self.session_round_no[sid] = u256(0)
        self.session_prompt[sid] = ""
        return sid

    @write
    def join_session(self, session_id: u256) -> None:
        cur = self.session_member_count.get(session_id, u256(0))
        maxp = self.session_max_players[session_id]
        if cur >= maxp:
            raise UserError("Session is full")
        self.session_member_count[session_id] = cur + u256(1)

    @view
    def get_prompt(self, session_id: u256) -> str:
        return self.session_prompt.get(session_id, "")

    @view
    def get_member_count(self, session_id: u256) -> u256:
        return self.session_member_count.get(session_id, u256(0))

    @view
    def get_round_no(self, session_id: u256) -> u256:
        return self.session_round_no.get(session_id, u256(0))

    @write
    def add_xp(self, player: Address, amount: u256) -> None:
        cur = self.season_xp.get(player, u256(0))
        self.season_xp[player] = cur + amount

    @view
    def get_xp(self, player: Address) -> u256:
        return self.season_xp.get(player, u256(0))
