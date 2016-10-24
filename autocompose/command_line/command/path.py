import argparse

from autocompose.util import print_paths
from .command import Command

__parser = argparse.ArgumentParser(prog="autocompose path", description='Print the autocompose paths.')

path_command = Command(__parser, print_paths)
