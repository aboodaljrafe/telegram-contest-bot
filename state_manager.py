import time

class StateManager:
    def __init__(self):
        self._states = {}

    def set_state(self, user_id: int, state: str, data: dict = None):
        self._states[user_id] = {
            "state": state,
            "data": data or {},
            "updated_at": time.time()
        }

    def get_state(self, user_id: int):
        return self._states.get(user_id)

    def clear_state(self, user_id: int):
        if user_id in self._states:
            del self._states[user_id]

    def cleanup_expired_states(self, max_age_seconds: int = 3600):
        now = time.time()
        expired = [uid for uid, info in self._states.items() if now - info["updated_at"] > max_age_seconds]
        for uid in expired:
            del self._states[uid]

state_manager = StateManager()
