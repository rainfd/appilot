from autochain.workflows_evaluation.base_test import BaseTest, TestCase, WorkflowTester
from autochain.utils import get_args
from validation.setup.setup import setup_test_agent, destory_walrus_sandbox
from validation.base import AppilotWorkflowTester

import monk


class TestListEnv(BaseTest):
    test_cases = [
        TestCase(
            test_name="create services",
            user_context="Deploy a nginx service in dev environment."
                         "Deploy a web service named spring-demo in test environment, using the 'ellinj/spring-demo' "
                         "image."
                         "Wait serval seconds."
            ,
            expected_outcome="two service are ready, one is nginx related, one is spring related",
        ),
        #                  "Finally, list all services in all environments."
        # TestCase(
        #     test_name="modify and delete services",
        #     user_context="Scale nginx service to 3 in dev environment."
        #                  "Delete spring-demo service in test environment.",
        #     expected_outcome="nginx service is scaled to 3 in dev environment."
        # )
        # TestCase(
        #     test_name="clone environment",
        #     user_context="Switch to qa environment."
        #                  "Deploy a nginx service."
        #                  "Deploy a web service named spring-demo, using the 'ellinj/spring-demo' "
        #                  "Clone qa environment to prod environment."
        #                  "Finally, list all services in prod environments."
        #     ,
        #     expected_outcome="two service are created in prod environment, one is nginx related, one is spring related",
        # ),
        # TestCase(
        #     test_name="modify and delete service",
        #     user_context="Deploy a nginx service name nginx-1 in dev environment."
        # )
    ]

    chain = setup_test_agent()

    tools = []


if __name__ == "__main__":
    tests = AppilotWorkflowTester(
        tests=[TestListEnv()], output_dir="./test_results"
    )

    args = get_args()
    if args.interact:
        tests.run_interactive()
    else:
        tests.run_all_tests()

    destory_walrus_sandbox()

