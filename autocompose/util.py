import os
import re
import sys

import yaml
from compose import progress_stream

__autocompose_service_name = None


class ExplicitYamlDumper(yaml.SafeDumper):
    """
    A yaml dumper that will never emit aliases.
    """

    def ignore_aliases(self, data):
        return True


def replace_template_variables(obj, terms):
    """
    Recursively replaces the values of any keys in obj which are defined in the terms dictionary.
    Terms must be a dictionary.
    :param obj: Any object.
    :param terms: A dictionary of values to replace.
    :return: the given obj, with any terms replaced.
    """
    if not isinstance(terms, dict):
        raise TypeError('Terms must be of type dictionary')
    if isinstance(obj, dict):
        for key, value in obj.items():
            new_key = replace_template_variables(key, terms)
            new_value = replace_template_variables(value, terms)
            if new_key != key:
                obj.pop(key)
            obj[new_key] = new_value
        return obj
    elif isinstance(obj, list):
        return [replace_template_variables(element, terms) for element in obj]
    else:
        for key, value in terms.items():
            if key in obj:
                return obj.replace(key, value)
    return obj


def deep_merge(a, b):
    """
    Merges b into a, recursively.
    This is a special recursive dictionary merge, made specifically for docker compose files.
    If a and b are both dictionaries, their keys are recursively merged. Keys in b write over keys in a.
    If a and b are both lists, the elements of b are added to a. Duplicate values are removed.
    If a and b are any other types, b is returned.
    :param a: Any object.
    :param b: Any object.
    :return: b merged into a.
    """

    if isinstance(a, dict) and isinstance(b, dict):
        for key in b:
            if key in a:
                a[key] = deep_merge(a[key], b[key])
            else:
                a[key] = b[key]
        return a
    elif isinstance(a, list) and isinstance(b, list):
        # Add all elements of b to a
        return list(set(a + b))
    elif b is None:
        return a
    else:
        # Copy b's value into a.
        return b


def get_from_paths(sub_path, file_pattern):
    """
    Search through the AUTOCOMPOSE_PATHs for files in the sub-path which match the given file_pattern
    :param sub_path: The sub-path to look for files in each autocompose path directory.
    :param file_pattern: A pattern to match files.
    :return: A list of files.
    """
    paths = os.environ['AUTOCOMPOSE_PATH'].split(":")
    results = []
    for path in paths:
        try:
            files = os.listdir(path=os.path.join(path, sub_path))
            for file in files:
                if re.fullmatch(file_pattern, file):
                    results.append(os.path.join(path, sub_path, file_pattern))
        except FileNotFoundError:
            pass
    return results


def get_first_from_paths(sub_path, file_pattern):
    results = get_from_paths(sub_path, file_pattern)
    if len(results) == 0:
        raise Exception(
            'No file ' + os.path.join(sub_path, file_pattern) + ' was found in any of the autocompose paths.')
    return results[0]


def get_all_from_paths(sub_path):
    """
    Search through the AUTOCOMPOSE_PATHs for all files in the sub-path.
    :param sub_path: The sub-path to look for files in each autocompose path directory.
    :return: A list of files.
    """
    paths = os.environ['AUTOCOMPOSE_PATH'].split(":")
    results = []
    for path in paths:
        try:
            files = os.listdir(path=os.path.join(path, sub_path))
            files = [os.path.join(path, sub_path, file) for file in files]
            results.extend(files)
        except FileNotFoundError:
            pass
    return results


def print_paths(**kwargs):
    """
    Prints the AUTOCOMPOSE_PATH directories to stdout.
    :return:
    """
    paths = os.environ['AUTOCOMPOSE_PATH'].split(":")
    for path in paths:
        print(path)


def get_current_directory():
    return os.path.basename(os.getcwd())


def get_service_name():
    if __autocompose_service_name is None:
        return get_current_directory()
    return __autocompose_service_name


def set_service_name(autocompose_service_name):
    global __autocompose_service_name
    __autocompose_service_name = autocompose_service_name


def get_config(directory, sub_directory, file_pattern):
    """
    Loads a YAML config from the AUTOCOMPOSE_PATH.
    :param directory: The top-level directory name to search.
    :param sub_directory: The specific sub-directory.
    :param file_pattern: A file pattern to match files in the directory/sub-directory.
    :return: The first found config as a dictionary.
    """
    configs = get_from_paths(os.path.join(directory, sub_directory), file_pattern)
    if len(configs) > 0:
        config = yaml.load(open(configs[0]))
    else:
        config = {}
    if config is None:
        config = {}
    return config


def get_user_config():
    user_config_directory = os.path.join(os.environ['HOME'], '.autocompose')
    user_config_file = os.path.join(user_config_directory, 'config.yml')
    try:
        with open(user_config_file, 'r') as file:
            user_config = yaml.load(file)
    except:
        user_config = {}
    if user_config is None:
        user_config = {}
    return user_config


def print_docker_output(stream):
    progress_stream.stream_output(stream, sys.stdout)
