import argparse

from autocompose.cleaner import clean_containers
from .command import Command

__parser = argparse.ArgumentParser(prog="autocompose clean-containers", description='Remove all Docker containers.')

clean_containers_command = Command(__parser, clean_containers)
