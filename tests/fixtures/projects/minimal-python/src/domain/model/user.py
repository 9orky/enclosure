from uuid import UUID


class User:
    def __init__(self, user_id: str, active: bool = False) -> None:
        self.user_id = str(UUID(user_id))
        self.active = active
        self.nickname = None

    def activate(self) -> None:
        self.active = True
