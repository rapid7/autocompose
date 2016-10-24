import subprocess
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

    __run_before_scripts(scenarios)

    # Readjust argv and call docker compose up
    sys.argv = [sys.argv[0], '-f', temp_file_name, 'up']
    sys.argv.extend(docker_compose_args)

    pid = os.fork()
    if pid != 0:
        compose_main.main()
    else:
        __run_after_scripts(scenarios)


def __run_before_scripts(scenarios):
    """
    Runs each scenarios 'before-scripts' scripts.
    Each script is executed in the foreground.
    Scripts must be successful for the scenario to begin.
    :param scenarios: A list of scenarios.
    :return:
    """

    for scenario_name in scenarios:
        scenario_config = get_config('scenarios', scenario_name, AUTOCOMPOSE_SCENARIO_FILE)
        if 'before-scripts' in scenario_config:
            before_scripts = scenario_config['before-scripts']
        else:
            before_scripts = []

        for script_name in before_scripts:
            try:
                script_file = get_first_from_paths(os.path.join('scripts', script_name), 'script.sh')
            except Exception:
                script_file = None
            if script_file is not None:
                __run_script_in_foreground(script_name, script_file)


def __run_after_scripts(scenarios):
    """
    Runs each scenarios 'before-scripts' scripts.
    Each script is executed in parallel in the background.
    Scripts do not need to be successful; script return codes are ignored.
    :param scenarios: A list of scenarios.
    :return:
    """

    for scenario_name in scenarios:
        scenario_config = get_config('scenarios', scenario_name, AUTOCOMPOSE_SCENARIO_FILE)

        if 'after-scripts' in scenario_config:
            after_scripts = scenario_config['after-scripts']
        else:
            after_scripts = []

        for script_name in after_scripts:
            script_file = get_first_from_paths(os.path.join('scripts', script_name), 'script.sh')
            __run_script_in_background(script_name, script_file)


def __run_script_in_foreground(script_name, script_file):
    """
    Runs a script. Blocks until the script is complete.
    :param script_name: A script name.
    :param script_file: The filename of the script.
    :return:
    """
    try:
        print('Executing script "' + script_name + '"...')
        subprocess.check_call(['bash', script_file])
    except BaseException as e:
        print(e)
        raise Exception("Error running before-script " + script_name)


def __run_script_in_background(script_name, script_file):
    """
    Runs a script as a background process.
    :param script_name: A script name.
    :param script_file: The filename of the script.
    :return:
    """
    try:
        print('Executing script "' + script_name + '"...')

        pid = os.fork()
        if pid == 0:
            subprocess.call(['bash', script_file])

    except subprocess.SubprocessError:
        print("Error running after-script " + script_name)
    except KeyboardInterrupt:
        print("Stopped after-script " + script_name)
