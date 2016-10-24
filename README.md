# Autocompose

Autocompose is a tool for dynamically creating docker-compose files.
It integrates with AWS to allow easy pushing and pulling to and from ECR.
Autocompose can also create Docker images.

## Prerequisites

Autocompose requires Python3.

The Docker engine should also be installed.

The following pip dependencies are required:
 * docker-py
 * docker-compose
 * boto3
 * pipywin32 (windows only)

Although not required, it is highly recommended you also install the aws-cli.

## Installation

My .bashrc has this
```
# Add autocompose to your path
export PATH="$PATH:/some/path/autocompose/bin"

# Add config directories to your autocompose path.
# This is an optional step.
export AUTOCOMPOSE_PATH="foo/bar:another/directory"

# Run the autocompose initialization script.
source autocompose init
```

Then try some `autocompose`

## Documentation

For more information, check out the [wiki](https://github.com/rapid7/docker-autocompose/wiki).

