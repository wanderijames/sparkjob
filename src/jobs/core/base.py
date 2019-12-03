"""
Base class
Provides common functionalities for other jobs.
"""
# pylint:disable=too-few-public-methods
from abc import abstractmethod
from time import time


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
    execution_time: float = 0.000

    @abstractmethod
    def _execute(self):
        """Job logic"""
        raise NotImplementedError

    def side_effect(self):
        """Any processes that works on artifacts

        artifacts could be:
        - metrics
        - pickled model
        """
        raise NotImplementedError

    def execute(self):
        """Execute entrypoint"""
        return self._execute()

    def get_metrics(self):
        """Collect metrics in `self`.`metrics`"""
        metrics = getattr(self, "metrics", {})
        if self.execution_time != 0.0000:
            metrics["execution_time"] = self.execution_time
        return metrics

    # Use this entrypoint for monitoring
    # Collect metrics such as execution_time and results.
    # Such metrics can be used for anomaly detection
    # one way to collect metris is by use of a python decorator
    def execute_extra(self):
        """Execute entrypoint

        # An example
        >>> job = BaseRegistry()
        >>> [_ for _ in obj.execute_extra()]


        """
        start_time = float(time())
        yield self.execute()
        self.execution_time = time() - start_time
        self.side_effect()
