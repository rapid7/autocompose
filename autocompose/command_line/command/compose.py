import argparse

from autocompose.composer import print_compose_file
from .command import Command

__parser = argparse.ArgumentParser(prog="autocompose compose", description='Create a docker-compose.yml file.')
__parser.add_argument(dest='scenarios', nargs='*', help='Scenarios and/or services.')

compose_command = Command(__parser, print_compose_file)
