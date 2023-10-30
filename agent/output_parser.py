import re
from typing import Union

from langchain.agents.agent import AgentOutputParser
from langchain.agents.conversational.prompt import FORMAT_INSTRUCTIONS
from langchain.schema import AgentAction, AgentFinish, OutputParserException


class OutputParser(AgentOutputParser):
    """Output parser for the agent. It extends the convoAgent parser to support multiline observation."""

    ai_prefix: str = "AI"
    """Prefix to use before AI output."""

    def get_format_instructions(self) -> str:
        return FORMAT_INSTRUCTIONS

    def parse(self, text: str) -> Union[AgentAction, AgentFinish]:
        if f"{self.ai_prefix}:" in text:
            return AgentFinish(
                {"output": text.split(f"{self.ai_prefix}:")[-1].strip()}, text
            )
        regex = r"Action: (?P<Action>.*?)([\s]*)(?:Action Input:([\s]*)(?P<Action_Input>.*?)([\s]*))?Reason: (?P<Reason>.*)"
        match = re.search(regex, text, re.DOTALL)
        if not match:
            raise OutputParserException(
                f"Could not parse LLM output: \n`{text}`"
            )
        action = match.group("Action").strip()
        action_input = match.group("Action_Input").strip() if match.group("Action_Input") else ''
        # reason = match.group("Reason").strip()
        return AgentAction(
            action, action_input, text
        )

    @property
    def _type(self) -> str:
        return "conversational"
