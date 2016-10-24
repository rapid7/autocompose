import argparse

from autocompose.authenticator import login_to_ecs
from .command import Command

__parser = argparse.ArgumentParser(prog="autocompose login", description='Login to ECR.')

login_command = Command(__parser, login_to_ecs)
