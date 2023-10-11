from typing import Any
from langchain.agents.tools import BaseTool
from callbacks.handlers import ApprovalCallbackHandler
import time


class RequireApprovalTool(BaseTool):
    """Tool that requires human approval."""

    def __init__(self, **data: Any) -> None:
        super().__init__(callbacks=[ApprovalCallbackHandler()], **data)


class WaitTool(BaseTool):
    """Tool that waits for a given amount of time."""

    name = "wait"
    description = "Wait for serval seconds. Input should be a number."

    def _run(self, input: str) -> None:
        seconds = int(input)
        time.sleep(seconds)
