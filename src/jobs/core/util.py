"""Common utils"""
from contextlib import contextmanager
import re

import psycopg2
from psycopg2.pool import SimpleConnectionPool


@contextmanager
def get_pool_conn(conn_details: dict):
    """Get connection from a connection pool

    :param conn_details: DB connection details
    """
    pool_ = DB.build_connection_pool(conn_details)
    conn_pool = pool_.getconn()
    try:
        yield conn_pool
        conn_pool.commit()
    finally:
        pool_.putconn(conn_pool)


class DB:
    """Execute SQL statement without the use of spark"""
    # pylint:disable=unsubscriptable-object

    url_regex = re.compile(
        r"^((?P<schema>(.)+)://(?P<host>(.)+):(?P<port>(\d)+)/(?P<db>(.)+$))")

    @staticmethod
    def build_connection_pool(conn_details: dict):
        """Build a conection pool for use

        :param conn_details: DB connection details
        :return:
        """

        # Expecting url to be like jdbc:postgresql://host:port/db
        conn_details.update(
            DB.url_regex.match(conn_details["url"]).groupdict()
        )
        return SimpleConnectionPool(
            minconn=1,
            maxconn=20,
            user=conn_details["user"],
            password=conn_details["password"],
            host=conn_details["host"],
            port=conn_details["port"],
            database=conn_details["db"])

    @staticmethod
    def execute(statement: str, is_append=True):
        """Execute SQL

        :param statement: SQL statement
        :param is_append: if we need to return any results
        :return:
        """
        raise NotImplementedError

    @staticmethod
    def insert_(statement: str, db_conf) -> []:
        """Insert data to a table

        :param statement: SQL statement
        :param db_conf: DB instance
        :type db_conf: DB
        """
        try:
            result = db_conf.execute(statement)
            if result:
                return result
        except psycopg2.IntegrityError:
            pass
        return []

    @staticmethod
    def insert(statement: str) -> []:
        """Insert data to a table

        :param statement: SQL statement
        """
        raise NotImplementedError
