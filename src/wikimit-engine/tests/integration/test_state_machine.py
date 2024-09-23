import json
import logging
import re
from pathlib import Path
from time import sleep
from unittest import TestCase
from uuid import uuid4

import boto3  # type: ignore
from botocore.client import BaseClient  # type: ignore

PORT = 8083
REGION = "us-west-1"
ACCOUNT = "123456789012"
STATE_MACHINE_NAME = "RevisionStateMachine"
STATE_MACHINE_ARN = (
    f"arn:aws:states:{REGION}:{ACCOUNT}:stateMachine:{STATE_MACHINE_NAME}"
)
INPUT = '{"title":"Finch", "reset": true}'
STATE_MACHINE_ROLE = f"arn:aws:iam::{ACCOUNT}:role/DummyRole"
FUNCTION_ARN_ROOT = f"arn:aws:lambda:{REGION}:{ACCOUNT}:function"

STATE_MACHINE_PATH = Path("statemachine") / "revision.asl.json"


class TestStateMachine(TestCase):
    client: BaseClient

    def setUp(self) -> None:
        self.client = boto3.client(  # type: ignore
            "stepfunctions",
            endpoint_url=f"http://localhost:{PORT}",
            region_name=REGION,
            aws_access_key_id="dummy",
            aws_secret_access_key="dummy",
        )
        self.client.create_state_machine(  # type: ignore
            name=STATE_MACHINE_NAME,
            definition=self._get_state_machine_definition(),
            roleArn=STATE_MACHINE_ROLE,
        )

    def _get_state_machine_definition(self) -> str:
        current_file = Path(__file__)
        state_machine_path = current_file.parent.parent.parent / STATE_MACHINE_PATH
        state_machine_definition = state_machine_path.read_text()
        state_machine_definition = re.sub(
            r"\$\{([^}]+)Arn\}",
            lambda m: f"{FUNCTION_ARN_ROOT}:{m.group(1)}",
            state_machine_definition,
        )
        return state_machine_definition

    def tearDown(self) -> None:
        pass

    def _start_execute(self) -> str:
        """
        Start the state machine execution request and record the execution ARN
        """
        response = self.client.start_execution(  # type: ignore
            stateMachineArn=STATE_MACHINE_ARN,
            name=f"integ-test-{uuid4()}",
            input=INPUT,
        )
        return response["executionArn"]  # type: ignore

    def _wait_execution(self, execution_arn: str) -> str:
        while True:
            response = self.client.describe_execution(executionArn=execution_arn)  # type: ignore
            status = response["status"]  # type: ignore
            if status == "SUCCEEDED":
                logging.info(f"Execution {execution_arn} completely successfully.")
                return response["output"]  # type: ignore
                break
            elif status == "RUNNING":
                logging.info(f"Execution {execution_arn} is still running, waiting")
                sleep(3)
            else:
                self.fail(f"Execution {execution_arn} failed with status {status}")

    def test_state_machine(self):
        execution_arn = self._start_execute()
        output = self._wait_execution(execution_arn)
        output_json = json.loads(output)
        self.assertEqual(
            output_json["synced_revisions"], 15, "Expected 15 synced revisions"
        )
        self.assertTrue(output_json["needs_sync"], "Expected needs_sync to be true")
        self.assertTrue(
            output_json["max_iterations_reached"],
            "Expected max_iterations_reached to be true",
        )
