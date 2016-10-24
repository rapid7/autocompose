import argparse

from autocompose.cleaner import clean_images
from .command import Command

__parser = argparse.ArgumentParser(prog="autocompose clean-images", description='Remove all Docker images.')

clean_images_command = Command(__parser, clean_images)
