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
sam init --no-interactive --name=wikimit-engine --runtime python3.11 --dependency-manager pip --app-template hello-world --tracing --application-insights --structured-logging
```

Some useful commands:
* `sam build`

For local commands, you must install and run [Docker](https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/install-docker.html):
* `sam build --use-container`
* `sam local invoke`
* `sam local start-api`

## License
[MIT](https://choosealicense.com/licenses/mit/)
