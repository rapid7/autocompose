import argparse

from autocompose.pusher import push_to_ecs
from .command import Command

__parser = argparse.ArgumentParser(prog="autocompose push", description='Push a Docker image to ECR.')
__parser.add_argument('--image-name', default=None, help='Image name. Default is the current directory.')
__parser.add_argument('--tag', default='latest', help='Tag to add to the image.')

push_command = Command(__parser, push_to_ecs)
