"""Testing modules and functions in the common package"""
from contextlib import contextmanager
import unittest
from unittest.mock import patch
import psycopg2

from jobs.core.base import (
    Singleton,
    JobHolder,
    BaseRegistry
)
from jobs.core.util import DB, get_pool_conn


class MockCursor:

    def execute(self):
        return None

    def fetchall(self):
        return []


class MockDBConn:

    def commit(self):
        return None

    @contextmanager
    def cursor(self):
        return MockCursor()


class MockDBPool:

    @contextmanager
    def getconn(self):
        return MockDBConn()

    def putconn(self, *args):
        return None


class CommonTest(unittest.TestCase):

    def test_abstracts(self):

        registry = JobHolder.get_registry()
        bases = (
            "BaseRegistry",
        )
        for b in bases:
            self.assertTrue(b not in registry)

    def test_common_base(self):

        A = type("A", (BaseRegistry,), {})
        for obj in (A(), ):
            try:
                obj.execute()
                raise Exception("Suppossed to raise 'NotImplementedError'")
            except NotImplementedError:
                self.assertTrue(
                    obj.__class__.__name__ in JobHolder.get_registry(),
                    "{} is in {}".format(
                        obj.__class__.__name__,
                        JobHolder.get_registry()
                    )
                )

    def test_base_extra_abstract(self):

        A = type("A", (BaseRegistry,), {})
        obj = A()
        setattr(obj, "_execute", lambda: "")
        with self.assertRaises(NotImplementedError):
            [res for res in obj.execute_extra()]

    def test_base_extra(self):

        A = type("A", (BaseRegistry,), {})
        obj = A()
        setattr(obj, "_execute", lambda: "")
        setattr(obj, "side_effect", lambda: "")
        results = [res for res in obj.execute_extra()]
        self.assertEqual(results[0], "")
        self.assertTrue(obj.execution_time > 0.0000)

    def test_singleton(self):
        class A(metaclass=Singleton):
            """"""
            container = {}
        obj_a = A()
        obj_a.container["key"] = "value"
        setattr(obj_a, "name", "foo")
        obj_b = A()
        self.assertEqual(obj_b.name, "foo")
        self.assertDictEqual(obj_b.container, {"key": "value"})


class UtilTest(unittest.TestCase):

    def setUp(self):
        self.db_host = "hostfoo"
        self.db_port = "5432"
        self.db_name = "dbfoo"
        self.user = "foo"
        self.password = "foobar"
        self.jdbc_url = "jdbc:postgresql://{}:{}/{}".format(
            self.db_host, self.db_port, self.db_name)
        self.db_details = dict(
            user=self.user,
            password=self.password,
            url=self.jdbc_url
        )

    def test_abstract(self):
        with self.assertRaises(NotImplementedError):
            DB.execute("", is_append=True)
        with self.assertRaises(NotImplementedError):
            DB.insert("")

    @patch('jobs.core.util.DB.execute')
    def test_insert(self, exec_mock):
        exec_mock.return_value = []
        statement = "INSERT"
        result = DB.insert_(statement, DB())
        self.assertEqual(result, [])
        exec_mock.assert_called_with(statement)

    @patch('jobs.core.util.DB.execute')
    def test_insert_result(self, exec_mock):
        exec_mock.return_value = [("1",)]
        statement = "INSERT RETURN id"
        result = DB.insert_(statement, DB())
        self.assertEqual(result, [("1",)])
        exec_mock.assert_called_with(statement)

    @patch('jobs.core.util.DB.execute', side_effect=psycopg2.IntegrityError())
    def test_insert_not_unique(self, exec_mock):
        exec_mock.return_value = []
        statement = "INSERT RETURN id"
        result = DB.insert_(statement, DB())
        exec_mock.assert_called_with(statement)
        self.assertEqual(result, [])

    @patch('jobs.core.util.SimpleConnectionPool')
    def test_conn_pool(self, conn_pool_mock):
        conn_pool_mock().return_value = MockDBPool()
        with get_pool_conn(self.db_details):
            pass
        conn_pool_mock.assert_called_with(
            minconn=1,
            maxconn=20,
            user=self.user,
            password=self.password,
            host=self.db_host,
            port=self.db_port,
            database=self.db_name
        )
