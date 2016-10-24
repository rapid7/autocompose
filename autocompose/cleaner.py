import docker
from docker import errors


def clean_containers(docker_client, **kwargs):
    """
    Removes all containers from the local machine.
    :param docker_client: The Docker client
    :return: None.
    """

    images = docker_client.containers(all=True)
    print('Killing and removing all Docker containers...')
    for image in images:
        try:
            docker_client.remove_container(image, force=True)
        except docker.errors.NotFound:
            pass
    print('Done.')


def clean_images(docker_client, **kwargs):
    """
    Removes all docker images from the local machine.
    :param docker_client: The Docker client
    :return: None.
    """

    print('Removing all Docker images...')
    empty = False
    while not empty:
        empty = True
        for image in docker_client.images(all=True):
            try:
                docker_client.remove_image(image, force=True)
            except docker.errors.NotFound:
                pass
            except docker.errors.APIError:
                print('Could not remove image "' + image['Id'] + '"')
    print('Done.')


def clean_networks(docker_client, **kwargs):
    """
    Remove all docker networks from the local machine.
    :param docker_client: The Docker client
    :return:
    """

    print('Removing all non-default Docker networks...')
    for network in docker_client.networks():
        if network['Name'] not in ['bridge', 'host', 'none']:
            try:
                docker_client.remove_network(net_id=network['Id'])
            except docker.errors.APIError:
                print('Could not remove network "' + network['Name'] + '"')
    print('Done.')
