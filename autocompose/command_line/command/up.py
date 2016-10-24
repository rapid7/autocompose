import argparse

from autocompose.launcher import up
from .command import Command

__parser = argparse.ArgumentParser(prog="autocompose up", description='Create and up a docker-compose.yml file.')
__parser.add_argument(dest='arguments', nargs=argparse.REMAINDER, help='Scenarios and/or services.')

up_command = Command(__parser, up)
