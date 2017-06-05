import tempfile

import compose.cli.main as compose_main

from .composer import build_compose_file
from .constants import *
from .util import *


def up(aws_session, arguments, **kwargs):
    """
    Calls 'docker-compose up' with an autocompose scenario.
    First, the scenario is built. (Exactly the same as the 'autocompose compose' command)
    :param aws_session: The AWS session.
    :param arguments: Command-line arguments.
    :return:
    """

    # Ensure the arguments exist
    docker_compose_args = []
    scenarios = []
    for arg in arguments:
        if arg.startswith('-'):
            # Anything that starts with a dash is an argument to be passed to 'docker-compose up'
            docker_compose_args.append(arg)
        else:
            # Otherwise, it's a scenario/service
            scenarios.append(arg)

    # The autocompose scenario is built in a temp folder.

    temp_folder = os.path.join(tempfile.gettempdir(), 'autocompose')
    if not os.path.exists(temp_folder):
        os.mkdir(temp_folder)

    temp_file_name = os.path.join(temp_folder, DOCKER_COMPOSE_FILE)
    if os.path.exists(temp_file_name):
        os.remove(temp_file_name)

    compose_dictionary = build_compose_file(aws_session, scenarios=scenarios)

    file_stream = open(temp_file_name, 'w')
    yaml.dump(compose_dictionary, stream=file_stream, default_flow_style=False, Dumper=ExplicitYamlDumper)
    file_stream.close()

    # Readjust argv and call docker compose up
    sys.argv = [sys.argv[0], '-f', temp_file_name, 'up']
    sys.argv.extend(docker_compose_args)

    compose_main.main()
