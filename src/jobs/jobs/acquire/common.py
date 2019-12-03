"""Abstract clasess for sourcing data"""
from abc import abstractmethod

from pyspark.sql import SQLContext, DataFrame
from jobs.jobs.common import SparkSQL


class CSVRecord(SparkSQL):
    """Get CSV record"""
    abstract = True

    def load_file(self):
        """Load CSV to dataframe"""
        filename = self.kwargs["filename"]
        header = self.kwargs.get("header", True)
        infer_schema = self.kwargs.get("inferSchema", True)
        return self.get_sql_context().read.csv(
            filename, header=header, inferSchema=infer_schema)

    @abstractmethod
    def _execute(self) -> str:
        """Run this job"""
        raise NotImplementedError


class DBRecord(SparkSQL):
    """Get DB record
    """
    abstract = True

    @staticmethod
    def get_source_details() -> dict:
        """Get source connection details.

        Return JDBC connection details:
        - url
        - user
        - password
        """
        raise NotImplementedError

    @staticmethod
    def run_spark_jdbc_sql_query(
            sql_context: SQLContext,
            query: str,
            connection_details: dict
    ) -> DataFrame:
        """Run SQL query using spark

        :param sql_context: spark SQLContext
        :param query: sql selectable query
        :param connection_details: Connection details
        :return: Dataframe with our data
        """
        return sql_context.read.format('jdbc') \
            .option("url", connection_details["url"]) \
            .option("user", connection_details["user"]) \
            .option("password", connection_details["password"]) \
            .option("query", query) \
            .load()

    @abstractmethod
    def _execute(self) -> str:
        """Run this job"""
        raise NotImplementedError

