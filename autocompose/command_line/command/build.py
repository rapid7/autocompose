import argparse

from autocompose.builder import build
from .command import Command

__parser = argparse.ArgumentParser(prog="autocompose build",
                                   description='Build a Docker image for the current directory.')
__parser.add_argument('--image-name', default=None, help='Image name. Default is the current directory.')
__parser.add_argument('--tag', default='latest', help='Tag to add to the image.')
build_command = Command(__parser, build)
