from .authenticator import get_authorization_data
from .util import print_docker_output


def update_images(aws_session, docker_client, **kwargs):
    """
    Updates any Docker images from ECR.
    :param aws_session:
    :param docker_client:
    :param kwargs:
    :return:
    """
    print('Updating ECR Docker images...')
    authorization_data = get_authorization_data(aws_session)
    repo_tag = authorization_data['proxyEndpoint'].replace('https://', '')
    for image in docker_client.images(all=True):
        if image['RepoTags'] is not None:
            for tag in image['RepoTags']:
                if tag.startswith(repo_tag):
                    print_docker_output(docker_client.pull(tag, stream=True))
    print('Done.')
