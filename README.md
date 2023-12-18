# wikimit

<a href="https://github.com/wikimit-hub">
  <img src="https://github.com/davidtorosyan/wikimit/raw/main/images/wikimit-logo.png" alt="Logo: wikimit-logo.png" width="200px" height="200px">
</a>

## Table of contents

- [Introduction](#introduction)
- [Setup](#setup)
- [Usage](#usage)
- [License](#license)

## Introduction

Wikimit (pronounced **wiki**-com**mit**) is a tool which converts wiki pages to git repositories.

See [wikimit-hub](https://github.com/wikimit-hub) for a collection of repositories already generated.

## Setup

This project is in prototyping stage, so the only setup available is figuring out how to run [proof.py](src/proof/proof.py).

## Usage

Not ready yet!

## Development

Created `wikimit-engine` with [SAM CLI](https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/install-sam-cli.html), version 1.103.0, using this command:
```
sam init --no-interactive --name=wikimit-engine --runtime python3.11 --dependency-manager pip --app-template step-functions-sample-app --tracing --application-insights --structured-logging
```

Some useful commands:
* `sam build`
* `pip install -r functions/revision_sync/requirements.txt --user`

For local commands, you must install and run [Docker](https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/install-docker.html):
* `sam build --use-container`
* `sam local invoke`
* `sam local start-api`

Before running tests, install [python 3.11](https://www.python.org/downloads/release/python-3117/) and [pip](https://pip.pypa.io/en/stable/installation/).

To run unit tests:
```sh
pip install -r tests/requirements.txt --user
python -m pytest tests/unit -v
```

To run integration tests (on Windows):
```sh
$env:AWS_SAM_STACK_NAME="wikimit-engine"
python -m pytest tests/integration -v
```

To run integration tests (on unix/mac):
```sh
AWS_SAM_STACK_NAME="wikimit-engine" python -m pytest tests/integration -v
```

To run a smoke test:
```sh
sam local invoke -e tests/events/smoke.json
```

To send an event to an already running instance:
```sh
aws lambda invoke --function-name "RevisionSyncFunction" --endpoint-url http://127.0.0.1:3001 --no-sign-request --cli-binary-format raw-in-base64-out --payload file://tests/events/smoke.json tmp_output.txt
```

To run the step function locally (on Windows):
```ps1
# prepare
sam build --use-container
sam local start-lambda

# variables
$port="8083"
$endpoint="http://localhost:$port"
$region="us-west-1"
$account="123456789012"
$stateMachineName="RevisionStateMachine"
$stateMachineArn="arn:aws:states:${region}:${account}:stateMachine:${stateMachineName}"
$executionName="test"
$executionArn="arn:aws:states:${region}:${account}:execution:${stateMachineName}:${executionName}"
$functionArnRoot="arn:aws:lambda:${region}:${account}:function"

# setup
docker run -p "${port}:${port}" --env-file tests/config/aws-stepfunctions-local-credentials.txt amazon/aws-stepfunctions-local

# create
$content = Get-Content -Path .\statemachine\revision.asl.json -Raw
$content = $content -replace '\$\{([^}]+)Arn\}', ($functionArnRoot+':$1')
aws stepfunctions --endpoint $endpoint create-state-machine --name "$stateMachineName" --definition "$content" --role-arn "arn:aws:iam::${account}:role/DummyRole"

# start
aws stepfunctions --endpoint $endpoint start-execution --state-machine-arn $stateMachineArn --name $executionName --input '{"title":"Finch"}'

# check
aws stepfunctions --endpoint $endpoint describe-execution --execution-arn $executionArn

# stop
aws stepfunctions --endpoint $endpoint stop-execution --execution-arn $executionArn

# delete
aws stepfunctions --endpoint $endpoint delete-state-machine --state-machine-arn $stateMachineArn

# list
aws stepfunctions --endpoint $endpoint list-executions --state-machine-arn $stateMachineArn --status-filter RUNNING
```

To generate mocks:
```sh
curl -d "&pages=Finch&curonly=true&action=submit" https://en.wikipedia.org/w/index.php?title=Special:Export -o "tests/mock/wiki_smoke_current.xml"
curl -d "&pages=Finch&limit=2&action=submit" https://en.wikipedia.org/w/index.php?title=Special:Export -o "tests/mock/wiki_smoke_history_1.xml"
curl -d "&pages=Finch&limit=2&offset=2002-12-17T03:58:19Z&action=submit" https://en.wikipedia.org/w/index.php?title=Special:Export -o "tests/mock/wiki_smoke_history_2.xml"
```

## License
[MIT](https://choosealicense.com/licenses/mit/)
