from dataclasses import dataclass

from domain.model.user import User
from domain.services.policy import ActivationPolicy, can_activate


@dataclass(frozen=True)
class ActivateUser:
    actor: str = "system"

    def execute(self, user: User) -> dict[str, str]:
        if not ActivationPolicy().allows(user):
            return {"status": "blocked"}
        return {"status": "activated", "id": user.user_id}


def build_activation_command(user: User) -> User:
    return user


def activation_label(user: User) -> str:
    return "allowed" if can_activate(user) else "blocked"


def nullable_label(value: str | None) -> str:
    return value or "missing"
