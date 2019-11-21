"""Test config module and configs available"""
import os
import unittest
from unittest.mock import patch

from jobs.config.file import FromFile, FromJson, THIS_DIR
from jobs.config.secret import Secret


DB_HOST = "hostfoo"
DB_PORT = "5432"
DB_NAME = "dbfoo"
DB_USER = "userfoo"
DB_PASSWORD = "password_foo"
ENV = {
    "SOURCE_JDBC_URL": "jdbc:postgresql://{}:{}/{}".format(
        DB_HOST, DB_PORT, DB_NAME
    ),
    "SOURCE_JDBC_USER": DB_USER,
    "SOURCE_JDBC_PASSWORD": DB_PASSWORD
}


class ConfigTest(unittest.TestCase):

    @patch('jobs.config.file.FromFile.load_file')
    def test_get_config_in_testing_environment(self, lf_mock):
        content = "{}"
        lf_mock.return_value = content
        conf = FromFile(".")
        exp_content = conf["sql.queries.dummy_query"]
        self.assertEqual(exp_content, content)

    def test_config_file_contents(self):
        conf = FromFile(THIS_DIR)
        conf.file_extension = ".json"
        exp_content = conf["conf.sample"]
        self.assertEqual(exp_content, """{"sample_key": "sample_value"}""")

    def test_config_json_key_value(self):
        conf = FromJson(THIS_DIR)
        exp_content = conf["conf.sample.sample_key"]
        self.assertEqual(exp_content, "sample_value")

    def test_config_json_not_key(self):
        conf = FromJson(THIS_DIR)
        with self.assertRaises(AttributeError):
            conf["conf.sample.no_key"]

    def test_file_not_found(self):
        conf = FromFile(".")
        with self.assertRaises(AttributeError):
            conf["sql.queries.dummy_query"]


class TestSecrets(unittest.TestCase):

    def test_common(self):
        with patch.dict(os.environ, ENV):
            sec = Secret()
            self.assertEqual(
                sec["SOURCE_JDBC_URL"], ENV["SOURCE_JDBC_URL"])
            self.assertEqual(
                sec.env("SOURCE_JDBC_URL"), ENV["SOURCE_JDBC_URL"])
            self.assertEqual(
                sec.aws_secret("SOURCE_JDBC_URL"), "")
            self.assertEqual(
                sec.aws_ssm("SOURCE_JDBC_URL"), "")
            self.assertEqual(
                sec["NOT_SET"], "")
