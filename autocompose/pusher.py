from .authenticator import get_authorization_data
from .util import *


def tag_to_ecr(aws_session, docker_client, tag):
    if tag is None or tag is '':
        tag = 'latest'

    service_name = get_service_name()
    repo = __get_docker_repository_name(aws_session, service_name)
    full_tag = service_name + ':' + tag
    image = __get_docker_image(docker_client, full_tag)

    # Tag to the ECR repo
    try:
        docker_client.tag(repository=repo, image=image, tag=tag)
    except BaseException as e:
        print(e)
        raise Exception('An error occurred when tagging the image "' + image + '" with the tag "' + full_tag + '".')


def push_to_ecs(aws_session, docker_client, image_name=None, tag=None):
    """
    Pushes the docker image represented by the current directory up to AWS's ECR.
    :param aws_session: The AWS session.
    :param docker_client: The Docker client
    :param image_name The name of the image.
    :param tag: The tag to apply to the Docker image. Default is latest.
    :return:
    """

    if image_name is None:
        image_name = get_service_name()
        print('image_name: ' + image_name)

    if tag is None:
        tag = 'latest'

    repo = __get_docker_repository_name(aws_session, image_name)
    full_tag = image_name + ':' + tag
    image = __get_docker_image(docker_client, full_tag)

    # Push to the ecs repo
    print('Pushing the image "' + full_tag + '" up to "' + repo + '"...')
    try:
        docker_client.tag(repository=repo, image=image, tag=tag)
    except BaseException as e:
        print(e)
        raise Exception('An error occurred when tagging the image "' + image + '" with the tag "' + full_tag + '".')
    try:
        print_docker_output(docker_client.push(repository=repo, stream=True, tag=tag))
    except BaseException as e:
        print(e)
        raise Exception('An error occurred when pushing "' + full_tag + '" to ECR.')
    print('The image "' + full_tag + '" has now been pushed up to "' + repo + '".')


def __get_docker_image(docker_client, repo_tag):
    images = docker_client.images()
    for image in images:
        tags = image['RepoTags']
        if tags is not None and repo_tag in tags:
            return image

    raise Exception('Could not find image')


def __get_docker_repository_name(aws_session, service_name):
    url = get_authorization_data(aws_session)['proxyEndpoint']
    return url.replace('https://', '') + '/' + service_name
