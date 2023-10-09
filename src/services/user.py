from src.adapters.db.adapters import UserDBAdapter
from src.application.commands import SearchUserCommand
from src.domain.models import User


class UserService:
    def __init__(self) -> None:
        self.user_db = UserDBAdapter()

    async def search(self, command: SearchUserCommand) -> User | None:
        user = None
        if command.user_id:
            user = await self.user_db.get_by_id(command.user_id)
        elif command.slack_user_ref:
            user = await self.user_db.find_by_tenant_id_slack_user_ref(
                command.tenant_id, command.slack_user_ref
            )
        return user
