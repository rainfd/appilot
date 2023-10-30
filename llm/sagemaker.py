import os

import boto3
import json

from langchain.llms.sagemaker_endpoint import LLMContentHandler
from langchain.llms import SagemakerEndpoint

from typing import Dict


class ContentHandler(LLMContentHandler):
    content_type = "application/json"
    accepts = "application/json"

    def transform_input(self, prompt: str, model_kwargs: dict) -> bytes:
        payload = {
            "inputs": [
                [
                    {"role": "user", "content": prompt},
                ],
            ],
            "parameters": {"max_new_tokens": 4097, "top_p": 0.6, "temperature": 0.1},
        }

        input_str = json.dumps(
            payload,
        )

        return input_str.encode("utf-8")

    def transform_output(self, output: bytes) -> str:
        response_json = json.loads(output.read().decode("utf-8"))
        content = response_json[0]["generation"]["content"]
        return content

# class ContentHandler(LLMContentHandler):
#     content_type = "application/json"
#     accepts = "application/json"
#
#     def transform_input(self, prompt: str, model_kwargs: Dict) -> bytes:
#         input_dict = {"inputs": prompt, "parameters": model_kwargs}
#         return json.dumps(input_dict).encode('utf-8')
#
#     def transform_output(self, output: bytes) -> str:
#         response_json = json.loads(output.read().decode("utf-8"))
#         print("output: ", response_json[0])
#         return response_json[0]["generation"]
# class ContentHandler(LLMContentHandler):
#     content_type = "application/json"
#     accepts = "application/json"
#
#     def transform_input(self, prompt: str, model_kwargs: Dict) -> bytes:
#         payload = {
#             "inputs": prompt,
#             "parameters": model_kwargs,
#         }
#         return json.dumps(payload).encode("utf-8")
#
#     def transform_output(self, output: bytes) -> str:
#         response_json = json.loads(output.read().decode("utf-8"))
#         return response_json[0]["generated_text"]


content_handler = ContentHandler()


def get_sagemaker(*args, **kwargs):
    endpoint_name = os.environ.get("SAGEMAKER_ENDPOINT_NAME", "")
    if not endpoint_name:
        raise ValueError("SAGEMAKER_ENDPOINT_NAME is not set")
    region_name = os.environ.get("SAGEMAKER_REGION", "")
    if not region_name:
        raise ValueError("SAGEMAKER_REGION is not set")
    llm = SagemakerEndpoint(
        endpoint_name=endpoint_name,
        credentials_profile_name="default",
        content_handler=content_handler,
        region_name=region_name,
        model_kwargs={
            "temperature": 0.1,
        },
        endpoint_kwargs={
            "CustomAttributes": "accept_eula=true"
        },
        callbacks=kwargs.get("callbacks", None),
    )
    # payload = {'inputs': [[{'role': 'user', 'content': 'what is the recipe of mayonnaise?'}]],
    #            'parameters': {'max_new_tokens': 256, 'top_p': 0.9, 'temperature': 0.6}}
    # encoded_payload = json.dumps(payload)
    # # body =
    # # llm.client = boto3.client("runtime.sagemaker")
    # # test
    # response = llm.client.invoke_endpoint(
    #     EndpointName=endpoint_name,
    #     Body=encoded_payload,
    #     ContentType="application/json",
    #     Accept="application/json",
    #     CustomAttributes="accept_eula=true",
    #     # **_endpoint_kwargs,
    # )
    return llm