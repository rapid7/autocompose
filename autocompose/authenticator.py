import base64
import json

from botocore.exceptions import ClientError as BotoClientError

from .util import *

# Config directory for Docker
__docker_config_directory = os.path.join(os.environ['HOME'], '.docker')

# Docker config file
__docker_config_file = os.path.join(__docker_config_directory, 'config.json')


def login_to_ecs(aws_session, docker_client, **kwargs):
    """
    Logs in to AWS's Docker Registry.
    :param aws_session: The AWS session.
    :param docker_client: The Docker client
    :return: None
    """

    print('Getting authorization data from AWS...')
    try:
        authorization_data = get_authorization_data(aws_session)
    except Exception as e:
        raise Exception('Unable to login to ECR. Make sure AWS credentials are set and valid.')
    # Get the authorization token. It contains the username and password for the ECR registry.
    if 'authorizationToken' not in authorization_data:
        raise Exception('Authorization data is missing an "authorizationToken" (docker registry password)')
    authorization_token = authorization_data['authorizationToken']

    # Get the proxy endpoint. It's the URL for the ECR registry.
    if 'proxyEndpoint' not in authorization_data:
        raise Exception('Authorization data is missing a "proxyEndpoint" (docker registry url)')
    registry = authorization_data['proxyEndpoint']

    # Get the username and password from the authorization token.
    decoded = base64.b64decode(authorization_token).decode('utf-8')
    username, password = decoded.split(':')

    # Log in to the registry
    print('Logging into ECR Registry "' + registry + '"...')
    try:
        result = docker_client.login(username=username, password=password, registry=registry, reauth=True)
    except BaseException as e:
        print(e)
        raise Exception('Error logging into ECR')
    if 'Status' not in result or not result['Status'] == 'Login Succeeded':
        raise Exception('Error logging into ECR')

    # The boto3 login function does not save the authorization token.
    # So here we save it manually. to ${HOME}/.docker/config.json
    print('Saving Docker login to "' + __docker_config_file + '"...')
    __save_docker_login(registry, authorization_token)

    if registry.startswith("https://"):
        __save_docker_login(registry[len("https://"):], authorization_token)

    print('Login Succeeded. You can can push to and pull from "' + registry + '".')


def get_authorization_data(aws_session):
    """
    Retrieve authorization data for ECR from AWS.
    See http://boto3.readthedocs.io/en/latest/reference/services/ecr.html#ECR.Client.get_authorization_token
    :param aws_session: The AWS session.
    :return: The first element in the authorizationData array.
    """
    aws_client = aws_session.client('ecr')
    try:
        response = aws_client.get_authorization_token()
    except BotoClientError:
        raise Exception('Unable to get a login via the AWS client. Have you ran \'autocompose login\' ?')

    if 'authorizationData' not in response:
        raise Exception('Unable to get a login via the AWS client. Have you ran \'autocompose login\' ?')

    authorization_data = response['authorizationData']

    if len(authorization_data) == 0:
        raise Exception('Authorization data was empty. ')

    return authorization_data[0]


def __save_docker_login(registry, authorization_token):
    """
    Persist authorization for a Docker registry to the Docker config file.
    :param registry: The name of the Docker registry
    :param authorization_token: The authorization token which contains the username and password.
    :return: None
    """

    if os.path.exists(__docker_config_file):
        with open(__docker_config_file, 'r') as fd:
            config = json.load(fd)
    else:
        config = {}

    if 'auths' not in config:
        config['auths'] = {}

    if not os.path.exists(__docker_config_directory):
        os.mkdir(__docker_config_directory)

    config['auths'][registry] = {'auth': authorization_token}
    with open(__docker_config_file, 'w+') as fd:
        json.dump(config, fd)
