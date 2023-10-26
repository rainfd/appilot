from autochain.utils import get_args
from validation.setup.setup import (
    setup_test_agent,
    destroy_walrus_sandbox,
    setup_walrus_sandbox,
    clear_walrus_sandbox,
    setup_k8s_sandbox,
    clear_k8s_sandbox,
    destroy_k8s_sandbox,
    appilot_enviroment,
)
from validation.base import WorkflowTester, BaseTest, TestCase


class TestWalrus(BaseTest):
    test_cases = [
        TestCase(
            test_name="create nginx service",
            user_context="Deploy a nginx service in dev environment."
                         "Wait 10 seconds."
                         "Get the nginx service status."
                         "If the service status is not ready, wait again"
                         "If the status of the service is ready, the nginx service is deployed successfully."
            ,
            expected_outcome="The nginx service is deployed in dev environment.",
            max_turn=15,
        ),
        # TestCase(
        #     test_name="create a spring service",
        #     user_context="Deploy a new service named 'spring-new-feature' in test environment."
        #                  "The source code repository is 'seal-demo/spring-boot-docker-sample' and the branch is 'feature'. "
        #                  "Wait 30 seconds."
        #                  "Get the spring-new-feature service status."
        #     ,
        #     expected_outcome="new spring-demo service is created, the status of the service is ready",
        # ),
        # TestCase(
        #     test_name="modify service",
        #     user_context="The nginx service is already deployed in dev environment."
        #                  "Scale nginx service replicas to 3."
        #                  "Get the nginx service message to confirm it.",
        #     expected_outcome="The replicas of the nginx service is 3."
        # ),
        # TestCase(
        #     test_name="delete service",
        #     user_context="The nginx service is already deployed in dev environment."
        #                  "Delete the nginx service."
        #                  "Get the status of the nginx service."
        #                  "List all services in dev environment.",
        #     expected_outcome="The nginx service is not found or the status of nginx service is deleted. "
        # ),
        # TestCase(
        #     test_name="clone environment",
        #     user_context="Deploy a nginx service in qa environment."
        #                  "Deploy a web service named spring-demo in qa environment, using the image 'ellinj/spring-demo'."
        #                  "Clone qa environment to prod environment."
        #                  "List all services in prod environments."
        #     ,
        #     expected_outcome="Two service are created in prod environment, one is nginx related, one is spring related",
        #     max_turn=15,
        # ),
    ]


class TestKubernetes(BaseTest):
    test_cases = [
        TestCase(
            test_name="deploy deployment",
            user_context="Use k8s yaml to deploy a MySQL and WordPress, expose the WordPress using a NodePort service."
                         "List all deployments."
                         "List all service."
                         "Get wordpress service endpoint."
            ,
            expected_outcome="The mysql and wordpress deployment are created, the type of wordpress service is 'NodePort'.",
        ),
        # TestCase(
        #     test_name="deploy jupyterhub",
        #     user_context="Deploy a juypterhub.",
        #     expected_outcome="The jupyterhub is deployed.",
        # )
    ]
    # use k8s yaml to deploy a mysql and wordpress, use node port service to expose the wordpress

    # deploy a jupyterhub, list service
    # upgrade the jupyterhub, use 3.0.3 image tag, show pods

    # are my apps working good?
    # the image in invalid, can you fix the app?

    # Deploy "feature" branch of the "seal-demo/spring-boot-docker-sample" source code repository, name the service "spring-new-feature"
    # https://github.com/walrus-catalog/deploy-source-code


def test_walrus(model='gpt-4'):
    appilot_enviroment("walrus")
    setup_walrus_sandbox()

    chain = setup_test_agent(model)
    output_dir = f"./test_results/{model}"

    tests = WorkflowTester(
        tests=[TestWalrus()],
        chain=chain,
        output_dir=output_dir,
    )

    tests.run_all_tests()


def test_k8s(model='gpt-4'):
    appilot_enviroment("kubernetes")
    setup_k8s_sandbox()

    chain = setup_test_agent(model)
    output_dir = f"./test_results/{model}"

    tests = WorkflowTester(
        tests=[TestKubernetes()],
        chain=chain,
        output_dir=output_dir,
    )

    tests.run_all_tests()


if __name__ == "__main__":
    import os
    os.environ["OPENAI_API_BASE"] = "http://rainfd.fun:5001/v1"

    model = 'gpt-4'
    # model = 'gpt-3.5-turbo'

    test_walrus(model)
    # test_k8s(model)

    # args = get_args()
    # if args.interact:
    #     tests.run_interactive()
    # else:
    #     tests.run_all_tests()

    # destory_walrus_sandbox()
