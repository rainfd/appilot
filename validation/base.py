import os.path
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import List, Tuple, Any, Dict

import pandas as pd
from colorama import Fore

from autochain.agent.message import UserMessage
from autochain.chain import constants
from autochain.chain.base_chain import BaseChain
from autochain.models.base import Generation
from autochain.models.chat_openai import ChatOpenAI
from autochain.tools.base import Tool
from autochain.utils import print_with_color
from autochain.workflows_evaluation.test_utils import parse_evaluation_response

from autochain.workflows_evaluation.base_test import WorkflowTester, TestCase


class AppilotWorkflowTester(WorkflowTester):

    def run_test(self, test):
        test_results = []
        self.chain = test.chain
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
        df.to_json(
            os.path.join(self.output_dir, f"{test.__class__.__name__}.jsonl"),
            lines=True,
            orient="records",
        )

    def test_each_case(self, test_case: TestCase):
        self.chain.memory.clear()

        conversation_history = []
        user_query = ""
        conversation_end = False
        max_turn = 8
        response = {}
        while not conversation_end and len(conversation_history) < max_turn:
            if not conversation_end:
                user_query = self.get_next_user_query(
                    conversation_history, test_case.user_context
                )
                conversation_history.append(("user", user_query))
                print_with_color(f">> User: {user_query}", Fore.GREEN)

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