import os

import boto3
import json

from langchain.llms.sagemaker_endpoint import LLMContentHandler
from langchain.llms import SagemakerEndpoint

from typing import Dict


class ContentHandler(LLMContentHandler):
    content_type = "application/json"
    accepts = "application/json"

    def transform_input(self, prompt: str, model_kwargs: Dict) -> bytes:
        payload = {
            "inputs": prompt,
            "parameters": model_kwargs,
        }
        return json.dumps(payload).encode("utf-8")

    def transform_output(self, output: bytes) -> str:
        response_json = json.loads(output.read().decode("utf-8"))
        return response_json[0]["generated_text"]


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
        content_handler=content_handler,
        region_name="ap-southeast-1",
        model_kwargs={
            "temperature": 0.1,
        }
    )
    llm.client = boto3.client("runtime.sagemaker")
    return llm