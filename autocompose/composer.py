from .authenticator import get_authorization_data
from .constants import *
from .util import *


def print_compose_file(aws_session, scenarios, **kwargs):
    """
    Prints a generated docker-compose file out to stdout.
    :param aws_session: The AWS session.
    :param scenarios: The scenarios and/or services.
    :return: None
    """

    docker_compose_file = build_compose_file(aws_session, scenarios=scenarios)

    # Setting default_flow_style = False prints out multi-line arrays.
    output = yaml.dump(docker_compose_file, default_flow_style=False, Dumper=ExplicitYamlDumper)

    # Fix the array formatting.
    output = output.replace('- ', ' - ')
    print(output)


def build_compose_file(aws_session, scenarios):
    """
    Builds a docker-compose configuration dictionary, given a list of scenarios.
    :param aws_session: The aws_session.
    :param scenarios: a list of autocompose scenarios.
    :return: A docker-compose configuration as a dictionary.
    """

    user_config = get_user_config()

    # Start with an empty configuration.
    docker_compose_config = {}
    template_variables = {}

    # Merge every scenario into the configuration
    for scenario_name in scenarios:
        __merge_scenario(aws_session, docker_compose_config, scenario_name, template_variables)

    # Look for template variables in the user config
    __add_user_config_template_variables(user_config, template_variables)

    __apply_template_variables(docker_compose_config, template_variables)
    docker_compose_config['version'] = '2'

    return docker_compose_config


def __merge_scenario(aws_session, docker_compose_config, scenario_name, template_variables):
    """
    Merge the contents of a scenario into the docker-compose config.
    :param aws_session: The aws_session.
    :param docker_compose_config: The docker-compose config being currently built.
    :param scenario_name: The name of the scenario to merge.
    :param template_variables: The template variables to add to.
    :return:
    """
    scenario_config = __get_scenario_config(scenario_name)
    service_names = __get_service_names(scenario_config)
    deep_merge(template_variables, __get_scenario_template_variables(scenario_config))

    # Merge the configs of all services of the scenario
    for service_name in service_names:
        __merge_service(aws_session, service_name, docker_compose_config)

    # Merge the scenario's docker-compose.yml config
    scenario_compose_config = __get_scenario_compose_config(scenario_name)
    deep_merge(docker_compose_config, scenario_compose_config)


def __get_scenario_config(scenario_name):
    """
    Get a scenarios configuration from the AUTOCOMPOSE_PATH.
    :param scenario_name: The name of the scenario.
    :return: The config of the scenario. {} if the scenario cannot be found.
    """
    all_scenarios = get_from_paths('scenarios', scenario_name)
    if len(all_scenarios) == 0:

        # look for a single service
        all_services = get_from_paths(os.path.join('services', scenario_name), AUTOCOMPOSE_SERVICE_FILE)
        if len(all_services) < 1:
            raise Exception('Could not find the scenario ' + scenario_name)
        scenario_config = {'services': [scenario_name]}

    else:
        scenario_config = yaml.load(open(os.path.join(all_scenarios[0], AUTOCOMPOSE_SCENARIO_FILE)))

    if scenario_config is None:
        scenario_config = {}

    return scenario_config


def __get_service_names(scenario_config):
    """
    Gets the list of services from the scenario config.
    If no services are given, an empty list is returned.
    :param scenario_config: The scenario config.
    :return: A list of services. [] if no service names are found.
    """
    if 'services' in scenario_config:
        service_names = scenario_config['services']
    else:
        service_names = []

    if not isinstance(service_names, list):
        raise Exception('"services" is not a list. It must be a list of services')

    return service_names


def __merge_service(aws_session, service_name, docker_compose_config):
    """
    Merge the contents of a service into the docker-compose config.
    :param aws_session: The aws_session.
    :param service_name: The name of the service to merge.
    :param docker_compose_config: The docker-compose config being currently built.
    :return:
    """
    service_name, version = __parse_version_from_service_name(service_name)

    service_compose_config = __get_docker_compose_config(service_name)
    service_config = __get_service_config(service_name)

    __add_service(service_compose_config, service_name)
    __add_docker_image(aws_session, service_compose_config, service_name, version)

    deep_merge(docker_compose_config, service_compose_config)
    if AUTOCOMPOSE_TEMPLATES_KEY in service_config:
        for template in service_config[AUTOCOMPOSE_TEMPLATES_KEY]:
            __apply_template(docker_compose_config, service_name, template)


def __parse_version_from_service_name(service_name):
    """
    Parse the actual service name and version from a service name in the "services" list of a scenario.
    Scenario services may include their specific version. If no version is specified, 'latest' is the default.
    :param service_name: The name of the service
    :return: The service name, The service version
    """
    if ':' in service_name:
        return service_name.split(':')

    return service_name, 'latest'


def __add_service(compose_config, service_name):
    """
    Adds a service to a docker-compose config.
    If the 'services' section does not exist, it is created.
    :param compose_config: The docker-compose config
    :param service_name: The name of the service.
    :return:
    """
    if 'services' not in compose_config:
        compose_config['services'] = {}

    if service_name not in compose_config['services']:
        compose_config['services'][service_name] = {}


def __get_docker_image(aws_session, service_name, tag):
    """
    Gets the 'image' to be applied to a given service.
    :param aws_session: The AWS session.
    :param service_name: The name of the service.
    :param tag: The tag for the service.
    :return: The complete docker image string.
    """
    url = get_authorization_data(aws_session)['proxyEndpoint']
    return url.replace('https://', '') + '/' + service_name + ':' + tag


def __add_docker_image(aws_session, compose_config, service_name, tag):
    """
    Adds the Docker image to a service in a docker-compose config.
    The image is only added if an existing image doesn't exist for the service.
    :param aws_session: The AWS session.
    :param compose_config: The docker-compose config being modified.
    :param service_name: The name of the service.
    :param tag: The tag to give the service.
    :return:
    """
    if 'image' not in compose_config['services'][service_name]:
        url = __get_docker_image(aws_session, service_name, tag)
        __add_service(compose_config, service_name)
        compose_config['services'][service_name]['image'] = url


def __get_scenario_template_variables(scenario_config):
    """
    Gets the template_variables from a scenario.
    :param scenario_config: The scenario.
    :return: A dictionary of template_variables.
    """
    template_variables = {}
    if TEMPLATE_VARIABLES_KEY in scenario_config:
        if isinstance(scenario_config[TEMPLATE_VARIABLES_KEY], dict):
            for key in scenario_config[TEMPLATE_VARIABLES_KEY]:
                template_variables["${" + key + "}"] = scenario_config[TEMPLATE_VARIABLES_KEY][key]
                template_variables["$" + key] = scenario_config[TEMPLATE_VARIABLES_KEY][key]
    return template_variables


def __get_docker_compose_config(service_name):
    """
    Gets the docker-compose config for an autocompose service from the AUTOCOMPOSE_PATH.
    :param service_name: The name of the service
    :return: The docker-compose config for the service.
    """
    return get_config('services', service_name, DOCKER_COMPOSE_FILE)


def __get_scenario_compose_config(scenario_name):
    """
    Gets the docker-compose config for an autocompose scenario from the AUTOCOMPOSE_PATH.
    :param scenario_name: The name of the scenario
    :return: The docker-compose config for the scenario.
    """
    return get_config('scenarios', scenario_name, DOCKER_COMPOSE_FILE)


def __get_service_config(service_name):
    """
    Gets the autocompose config for an autocompose service from the AUTOCOMPOSE_PATH.
    :param service_name: The name of the service.
    :return: The config for the service.
    """
    return get_config('services', service_name, AUTOCOMPOSE_SERVICE_FILE)


def __apply_template(docker_compose_config, service_name, template):
    """
    Applies a template to a given service in a given docker-compose config.
    :param docker_compose_config: The docker-compose config being currently built.
    :param service_name: The name of the service.
    :param template: The template to add to the service in the docker-compose config.
    :return:
    """

    template_global_config = __get_global_template_config(template)
    template_service_config = __get_service_template_config(template)

    __add_service(docker_compose_config, service_name)

    template_config = {'services': {}}
    template_config['services'][service_name] = template_service_config

    deep_merge(docker_compose_config, template_global_config)
    deep_merge(docker_compose_config, template_config)


def __get_global_template_config(template_name):
    """
    Get the global template config from an autocompose template from the AUTOCOMPOSE_PATH.
    :param template_name: The name of the template.
    :return: The global docker-compose config for the template.
    """
    return get_config('templates', template_name, DOCKER_COMPOSE_FILE)


def __get_service_template_config(template_name):
    """
    Get the per-service template config from an autocompose template from the AUTOCOMPOSE_PATH.
    :param template_name: The name of the template.
    :return: The per-service docker-compose config for the template.
    """
    return get_config('templates', template_name, DOCKER_COMPOSE_SERVICES_FILE)


def __apply_template_variables(docker_compose_config, template_variables):
    """
    Apply the given template variables to the given docker-compose config.
    :param docker_compose_config: The docker-compose config being currently built.
    :param template_variables: Key-value pairs to replace keys and values in the docker-compose config.
    :return:
    """
    return replace_template_variables(docker_compose_config, template_variables)


def __add_user_config_template_variables(user_config, template_variables):
    if 'template-variables' in user_config:
        for key, value in user_config['template-variables'].items():
            template_variables["${" + key + "}"] = value
            template_variables["$" + key] = value
