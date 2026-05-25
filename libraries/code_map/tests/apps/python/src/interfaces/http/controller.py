import json as json_lib

from application.use_cases.activate import ActivateUser, build_activation_command
from domain.model.user import User as DomainUser


class ActivationController:
    def __init__(self, use_case: ActivateUser) -> None:
        self._use_case = use_case

    def handle(self, user_id: str) -> dict[str, str]:
        payload = json_lib.loads('{"active": true}')
        command = build_activation_command(DomainUser(user_id, payload["active"]))
        return self._use_case.execute(command)
