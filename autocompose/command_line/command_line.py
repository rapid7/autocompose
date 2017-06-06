#!/usr/bin/env python3

import argparse
import os
import sys

import boto3
import docker

from .command.build import build_command
from .command.clean_containers import clean_containers_command
from .command.clean_images import clean_images_command
from .command.clean_networks import clean_networks_command
from .command.compose import compose_command
from .command.login import login_command
from .command.path import path_command
from .command.push import push_command
from .command.update_images import update_images_command
from ..util import set_service_name

commands = {
    'build': build_command,
    'clean-containers': clean_containers_command,
    'clean-images': clean_images_command,
    'clean-networks': clean_networks_command,
    'compose': compose_command,
    'login': login_command,
    'path': path_command,
    'push': push_command,
    'update-images': update_images_command
}

parser = argparse.ArgumentParser(description='Dynamically create docker-compose files.')

parser.add_argument(choices=list(commands.keys()), dest='COMMAND', help='The command to run.')
parser.add_argument('--service-name',
                    help='Explicitly specify the service name instead of assuming it is the name of the current '
                         'directory.')
parser.add_argument('--aws-access-key-id', help='The AWS access key.')
parser.add_argument('--aws-secret-access-key', help='The AWS secret key.')
parser.add_argument('--aws-session-token', help='The AWS session token.')
parser.add_argument('--aws-profile', help='The AWS profile.')
parser.add_argument('--region', default='us-east-1', help='The AWS region.')
parser.add_argument(dest='ARGUMENTS', nargs=argparse.REMAINDER)


def __setup_config_directory():
    # Check that the user config folder exists.
    user_config_directory = os.path.join(os.environ['HOME'], '.autocompose')
    user_config_file = os.path.join(user_config_directory, 'config.yml')
    if not os.path.exists(user_config_directory):
        os.mkdir(user_config_directory)
    elif not os.path.isdir(user_config_directory):
        raise Exception('User config directory "' + user_config_directory + '" is not a directory.')
    if not os.path.exists(user_config_file):
        with open(user_config_file, 'w') as file:
            pass
    elif not os.path.isfile(user_config_file):
        raise Exception('User config file "' + user_config_file + '" is not a file.')


def __require_python_version():
    req_version = (3, 4)
    cur_version = sys.version_info

    if cur_version < req_version:
        print("Your Python interpreter is too old. Autocompose requires Python 3.4 or higher.")
        exit(1)


def main():
    __require_python_version()

    args = parser.parse_args()
    command = args.COMMAND

    # Check that the user config directory and file exists.
    __setup_config_directory()

    if command not in commands.keys():
        print('Not a command: ' + command)
        exit(-1)

    if args.service_name is not None:
        set_service_name(args.service_name)
        print('service-name set to ' + args.service_name)

    aws_session = boto3.Session(aws_access_key_id=args.aws_access_key_id,
                                aws_secret_access_key=args.aws_secret_access_key,
                                aws_session_token=args.aws_session_token,
                                region_name=args.region,
                                profile_name=args.aws_profile)

    docker_client = docker.APIClient()

    try:
        commands[command].parse_and_execute(args=args.ARGUMENTS, aws_session=aws_session, docker_client=docker_client)
    except Exception as e:
        print("Unexpected error:", sys.exc_info()[1])


if __name__ == "__main__":
    main()
