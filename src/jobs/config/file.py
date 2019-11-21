"""Accessing configs from files"""
import json
import os

__all__ = ["FromFile"]


THIS_DIR = os.path.abspath(os.path.dirname(__file__))


class FromFile:
    """Configs entrypoint"""
    # pylint:disable=too-few-public-methods

    file_extension = ""

    def __init__(self, base_conf_dir: str):
        """
        :param base_conf_dir: Path with all the configurations
        """
        self.base_conf_dir = base_conf_dir

    @staticmethod
    def load_file(filename: str) -> str:
        """Read file contents

        :param filename: file with config to read=
        """
        with open(filename) as f_conf:
            return f_conf.read(-1)

    def __getitem__(self, item):
        path = item.split(".")
        file_path = os.path.join(self.base_conf_dir, *path)
        file_path_with_extension = file_path + self.file_extension
        try:
            return self.load_file(file_path_with_extension)
        except FileNotFoundError:
            raise AttributeError("%s cannot be found" % item)


class FromJson(FromFile):
    """Configs entrypoint"""
    # pylint:disable=too-few-public-methods

    file_extension = ".json"

    def __getitem__(self, item):
        path = item.split(".")
        key = path.pop()
        file_path = os.path.join(self.base_conf_dir, *path)
        file_path_with_extension = file_path + self.file_extension

        conf = self.load_file(file_path_with_extension)
        json_conf = json.loads(conf)

        try:
            return json_conf[key]
        except KeyError:
            raise AttributeError("%s cannot be found" % item)
