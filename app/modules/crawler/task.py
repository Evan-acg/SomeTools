from .action import ActionContext, IAction
import typing as t


class Task:
    def __init__(self, ctx: ActionContext) -> None:
        self.payload: ActionContext = ctx
        self.actions: list[IAction] = []

    def init_actions(self) -> None:
        pass

    def add_action(self, action: IAction) -> None:
        self.actions.append(action)

    def start(self) -> bool:
        self.init_actions()

        for action in self.actions:
            flag = action()
            if not flag:
                return False
        return True
