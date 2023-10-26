import os.path
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import List, Tuple, Any, Dict
from datetime import datetime

import pandas as pd
from colorama import Fore

from autochain.chain.base_chain import BaseChain
from autochain.utils import print_with_color
from autochain.agent.message import UserMessage
from autochain.models.base import Generation
from autochain.workflows_evaluation.test_utils import parse_evaluation_response
from autochain.models.chat_openai import ChatOpenAI


@dataclass
class TestCase:
    """Standardized data class for each test case for BastTest"""

    test_name: str = ""
    user_context: str = ""
    expected_outcome: str = ""
    max_turn: int = 8


class BaseTest(ABC):
    @property
    @abstractmethod
    def test_cases(self) -> List[TestCase]:
        """"""


class WorkflowTester:
    def __init__(self, tests: List[BaseTest], chain: BaseChain, output_dir: str):
        self.chain = chain
        self.tests = tests
        self.output_dir = output_dir
        self.llm = ChatOpenAI(temperature=0, model_name='gpt-4', top_p=0.9,)

    def run_test(self, test):
        test_results = []
        for i, test_case in enumerate(test.test_cases):
            print(
                f"========== Start running test case: {test_case.test_name} ==========\n"
            )
            conversation_history, is_agent_helpful, last_response = self.test_each_case(
                test_case
            )
            result = {
                "test_name": test_case.test_name,
                "expected_outcome": test_case.expected_outcome,
                "conversation_history": [
                    f"{user_type}: {message}"
                    for user_type, message, in conversation_history
                ],
                "last_response": last_response["message"],
                "num_turns": len(conversation_history),
                "is_agent_helpful": is_agent_helpful,
                # TODO: add intermediate steps
                # "actions_took": [
                #     {
                #         "tool": action.tool,
                #         "tool_input": action.tool_input,
                #         "tool_output": action.tool_output,
                #     }
                #     for action in last_response[constants.INTERMEDIATE_STEPS]
                # ],
                # generation_text = response.generations[0][0].text
                # lines = generation_text.splitlines()
                # action = "Action:"
                # for line in reversed(lines):
                #     if line.startswith("Action:"):
                #     response.
                #     break
            }
            for user_type, message, in conversation_history:
                if user_type == "user":
                    continue
                # else:
                #     if
            test_results.append(result)

        df = pd.DataFrame(test_results)
        os.makedirs(self.output_dir, exist_ok=True)
        time = datetime.now().strftime("%Y%m%d-%H%M%S")
        df.to_json(
            os.path.join(self.output_dir, f"{test.__class__.__name__}-{time}.json"),
            # lines=True,
            orient="records",
            indent=4,
        )

    def test_each_case(self, test_case: TestCase):
        self.chain.memory.clear()

        conversation_history = []
        user_query = ""
        conversation_end = False
        max_turn = test_case.max_turn
        response = {}
        while not conversation_end and len(conversation_history) < max_turn:
            if not conversation_end:
                user_query = self.get_next_user_query(
                    conversation_history, test_case.user_context
                )
                conversation_history.append(("user", user_query))
                print_with_color(f">> User: {user_query}", Fore.GREEN)
                if user_query == "Thank you":
                    break

            response: Dict[str, Any] = self.chain.run(user_query)

            # agent_message = response.get("message")
            agent_message = response
            conversation_history.append(("assistant", agent_message))
            print_with_color(f">> Assistant: {agent_message}", Fore.GREEN)

            conversation_end = self.determine_if_conversation_ends(agent_message)

        is_agent_helpful = self.determine_if_agent_solved_problem(
            conversation_history, test_case.expected_outcome
        )
        return conversation_history, is_agent_helpful, response

    def run_all_tests(self):
        for test in self.tests:
            self.run_test(test)

    def run_interactive(self):
        test = self.tests[0]
        self.chain.memory.clear()

        while True:
            user_query = input(">> User: ")
            response = self.chain.run(user_query)["message"]
            print_with_color(f">> Assistant: {response}", Fore.GREEN)

    def determine_if_conversation_ends(self, last_utterance: str) -> bool:
        messages = [
            UserMessage(
                content=f"""The most recent reply from assistant
assistant: "{last_utterance}"
Has assistant finish assisting the user or tries to hand off to an agent? Answer with yes or no"""
            ),
        ]
        output: Generation = self.llm.generate(messages=messages).generations[0]

        if "yes" in output.message.content.lower():
            # finish assisting; conversation should end
            return True
        else:
            # not yet finished; conversation should continue
            return False

    def get_next_user_query(
        self, conversation_history: List[Tuple[str, str]], user_context: str
    ) -> str:
        messages = []
        conversation = ""

        for user_type, utterance in conversation_history:
            conversation += f"{user_type}: {utterance}\n"

        conversation += "user: "

        messages.append(
            UserMessage(
                content=f"""You are a user with access to the following context information about yourself. 
Based on previous conversation, write the message to assistant to help you with goal described 
in context without asking repetitive questions.
Replies 'Thank you' if the goal is achieved.
If the steps have been given, follow the steps given.
If you are not sure about how to answer, respond with "hand off to agent".
Context:
"{user_context}"

Previous conversation:
{conversation}"""
            )
        )

        output: Generation = self.llm.generate(
            messages=messages, stop=[".", "?"]
        ).generations[0]
        return output.message.content

    def determine_if_agent_solved_problem(
        self, conversation_history: List[Tuple[str, str]], expected_outcome: str
    ) -> Dict[str, str]:
        messages = []
        conversation = ""
        for user_type, utterance in conversation_history:
            conversation += f"{user_type}: {utterance}\n"

        messages.append(
            UserMessage(
                content=f"""You are an admin for assistant and check if assistant meets the expected outcome based on previous conversation.

Previous conversation:
{conversation}

Expected outcome is "{expected_outcome}"
Does conversation reach the expected outcome for user? answer in JSON format
{{
    "reason": "explain step by step if conversation reaches the expected outcome",
    "rating": "rating from 0 to 5; 0 for not meeting the expected outcome at all, 5 for completely meeting the expected outcome",
}}"""
            )
        )

        output: Generation = self.llm.generate(messages=messages).generations[0]
        return parse_evaluation_response(output.message)
