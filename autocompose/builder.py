import shutil
import subprocess

from .constants import *
from .pusher import tag_to_ecr
from .util import *


def build(aws_session, docker_client, image_name=None, tag=None):
    """
    Builds a docker image from the current directory.
    :param aws_session: The AWS session.
    :param docker_client: The Docker client
    :param image_name The name of the image.
    :param tag: The tag to apply to the Docker image. Default is latest.
    :return:
    """

    service_name = get_service_name()
    print('Looking for the location of the service "' + service_name + '" in the AUTOCOMPOSE_PATH...')
    autocompose_config_file = get_first_from_paths(os.path.join('services', service_name), AUTOCOMPOSE_SERVICE_FILE)
    autocompose_config = yaml.load(open(autocompose_config_file, 'r'))

    # Get the name of the image
    if AUTOCOMPOSE_IMAGE_KEY not in autocompose_config:
        raise Exception('No Autocompose image specified')
    image = autocompose_config[AUTOCOMPOSE_IMAGE_KEY]
    print('The service "' + service_name + '" wants to use the image "' + image + '".')

    # Find the directory where the image recipe resides
    print('Looking for the location of the image "' + image + '" in the AUTOCOMPOSE_PATH...')
    image_path = __get_image_path(image)
    if image_path is None:
        raise Exception('Could not find the image ' + image)
    print('Using the path "' + image_path + '"')

    # Copy files from the recipe to the current directory
    print('Copying files from "' + image_path + '" to your current directory...')
    copied_files = __copy_files(image_path)

    # If the Dockerfile.sh file exists, execute it
    if os.path.exists(DOCKERFILE_SH):
        print(DOCKERFILE_SH + ' exists. Executing...')
        try:
            subprocess.call(['bash', DOCKERFILE_SH])
        except BaseException as e:
            print(e)
            __fail(copied_files)
            raise Exception('An error occurred while executing Dockerfile.sh')
    print('Dockerfile.sh executed successfully.')

    # Execute 'docker build .'
    if image_name is None:
        image_name = service_name

    if tag is None:
        repo_tag = image_name
    else:
        repo_tag = image_name + ':' + tag

    print('Calling "docker build ." (and tagging image with "' + repo_tag + '")')
    try:
        __build_docker_image(docker_client, path='.', tag=repo_tag)
    except BaseException as e:
        print(e)
        __fail(copied_files)
        raise Exception('An error occurred when running "docker build .". Make sure the Dockerfile is correct.')

    print('Image built successfully.')

    # Cleanup copied files
    print('Cleaning up copied files...')
    __cleanup(copied_files)

    print('Tagging image with ECR repository...')
    tag_to_ecr(aws_session, docker_client, tag)
    print('Image tagged.')


def __get_image_path(image_name):
    """
    Search for docker image recipes in the autocompose path directories.
    The first path is always the first one returned.
    :param image_name: The name of the image.
    :return: The path to the docker image recipe, None if it wasn't found.
    """
    images = get_from_paths('images', image_name)
    if len(images) < 1:
        return None
    return images[0]


def __copy_files(image_path):
    """
    Copies files from a docker image recipe path to the current path.
    :param image_path: The docker image recipe path.
    :return: A list of the files which were copied. (Absolute file names)
    """
    files = os.listdir(path=image_path)
    copied_files = []
    for file in files:
        if os.path.exists(file):
            print(' - Did not copy "' + file + '" because a file of the same name already exists')
        else:
            print(' - "' + file + '"')
            copied_files.append(file)
            shutil.copy(os.path.join(image_path, file), file)
    return copied_files


def __cleanup(copied_files):
    """
    Clean up any copied files.
    :param copied_files: A list of copied files to be deleted.
    :return: Nothing.
    """
    for file in copied_files:
        print(' - "' + file + '"')
        os.remove(file)


def __build_docker_image(docker_client, path, tag):
    """
    Calls 'docker build' with the given path and tag.
    :param docker_client: The docker client.
    :param path: The path to build.
    :param tag: The tag to give the built docker image.
    :return: Nothing.
    """
    print_docker_output(docker_client.build(path=path, tag=tag, stream=True))


def __fail(copied_files):
    """
    Prints a fail message and calls cleanup.
    :param copied_files:
    :return:
    """
    print('An error has occurred.')
    print('Cleaning up copied files...')
    __cleanup(copied_files)
