from domain.model.user import User


class ActivationPolicy:
    def allows(self, user: User) -> bool:
        return can_activate(user)


def can_activate(user: User) -> bool:
    return not user.active
