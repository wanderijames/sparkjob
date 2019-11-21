"""Accessing secrets from different sources"""
from abc import abstractmethod
import os

from jobs.core.base import Singleton


__all__ = ["Secret"]


class Secret(metaclass=Singleton):
    """Provides necessary credentials for our jobs"""

    # Will store recently accessed keys
    secrets = {}

    @staticmethod
    def env(key: str) -> str:
        """Get credentials from the environment variables

        :param key: secret key
        :return: The secret key value
        """
        return os.environ.get(key, "")

    @abstractmethod
    def aws_ssm(self, key: str) -> str:
        """Get credentials from AWS SSM

        :param key: secret key
        :return: The secret key value
        """
        return ""

    @abstractmethod
    def aws_secret(self, key: str) -> str:
        """Get credentials from AWS Secret Store

        :param key: secret key
        :return: The secret key value
        """
        return ""

    @abstractmethod
    def get_value(self, key) -> str:
        """Get needed key"""
        stores = (self.env, self.aws_ssm, self.aws_secret)
        for store in stores:
            val = store(key)
            if val:
                return val
        return ""

    def __getitem__(self, key) -> str:
        """Get credentials for use

        :param key: secret key
        :return: The secret key value
        """
        value = self.secrets.get(
            key, self.get_value(key))
        if value:
            self.secrets[key] = value
            return value
        return ""
