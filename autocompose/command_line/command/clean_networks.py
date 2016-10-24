import argparse

from autocompose.cleaner import clean_networks
from .command import Command

__parser = argparse.ArgumentParser(prog="autocompose clean-networks", description='Remove all Docker networks.')

clean_networks_command = Command(__parser, clean_networks)
