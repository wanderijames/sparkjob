"""
Base class
Provides common functionalities for other jobs.
"""
# pylint:disable=too-few-public-methods
from abc import abstractmethod


class Singleton(type):
    """Ensure we have on instance of a class"""
    _instance = None

    def __call__(cls, *args, **kwargs):
        """Ensure we have only one instance"""
        if cls._instance is None:
            cls._instance = super().__call__(*args, **kwargs)
        return cls._instance


class JobHolder(type):
    """Will provider a helper to easily access the job needed to run"""

    REGISTRY = {}

    def __new__(cls, name, bases, attrs):
        """`names` will be used tp register the class in our `REGISTRY`"""
        job_cls = type.__new__(cls, name, bases, attrs)
        is_abstract = attrs.get("abstract", False)
        if not is_abstract:
            cls.REGISTRY[job_cls.__name__] = job_cls
        return job_cls

    @classmethod
    def get_registry(cls):
        """Get our registry"""
        return cls.REGISTRY


class BaseRegistry(metaclass=JobHolder):
    """Inherit this to register your job"""
    abstract = True

    @abstractmethod
    def _execute(self):
        """Job logic"""
        raise NotImplementedError

    # Use this entrypoint for monitoring
    # Collect metrics such as execution_time and results.
    # Such metrics can be used for anomaly detection
    # one way to collect metris is by use of a python decorator
    def execute(self):
        """Execute entrypoint"""
        return self._execute()
