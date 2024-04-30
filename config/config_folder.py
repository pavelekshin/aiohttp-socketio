import os


def get_config_folder(base_file):
    base_folder = os.path.dirname(__file__)
    return os.path.join(base_folder, base_file)
