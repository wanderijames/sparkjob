""""""
from abc import abstractmethod

from pyspark.sql import SQLContext
from jobs.core.base import BaseRegistry


class SparkSQL(BaseRegistry):
    """Get CSV record"""
    abstract = True

    def __init__(self, spark_context, **kwargs):
        """
        :param spark_context: SparkContext
        """
        self.spark_context = spark_context
        self.kwargs = kwargs

    @property
    def temp_table(self):
        """Get temp table name to use"""
        return "{}_data".format(self.__class__.__name__)

    def side_effect(self):
        """Not using side effects for now"""
        pass

    def get_sql_context(self):
        """Get sql context to use"""
        return SQLContext(self.spark_context)

    def df_from_temp_table(self, table_name):
        """Execute a spark sql

        :param table_name: spark temp table name
        :return: pyspark dataframe
        """
        return SQLContext(self.spark_context).sql(
            "SELECT * FROM {}".format(table_name))

    @abstractmethod
    def _execute(self):
        """Job logic"""
        raise NotImplementedError
