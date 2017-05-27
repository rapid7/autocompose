import argparse

from autocompose.updater import update_images
from .command import Command

__parser = argparse.ArgumentParser(prog="autocompose update-images", description='Update images.')

update_images_command = Command(__parser, update_images)
