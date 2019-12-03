"""Spark Jobs Pipeline

Designed for Airflow DAG. However, this can be run as executable for some tests

Session statuses according to Livy:

not_started	    Session has not been started
starting	    Session is starting
idle	        Session is waiting for input
busy	        Session is executing a statement
shutting_down	Session is shutting down
error	        Session errored out
dead	        Session has exited
killed	        Session has been killed
success	        Session is successfully stopped
"""
from datetime import datetime
import json
import logging
import os
import textwrap
import time

import requests
from requests.exceptions import ConnectionError, HTTPError


LIVY_HOST = os.environ.get("LIVY_HOST", "http://localhost:8998")
REQ_HEADERS = {'Content-Type': 'application/json'}

TERMINAL_STATUS = (
    "success", "error", "dead", "killed", "shutting", "idle")

JOB_TEMPLATE = """
# sc = spark.sparkContext
from jobs.core.base import JobHolder
        
        
Job = JobHolder.get_registry()['{job_key_in_registry}']
job = Job({job_args_kwargs})
result = job.execute()
print(result)
"""


class SparkAppError(Exception):
    """Raise when spark app encounters error"""


def start_session() -> (int, str):
    """Start livy/spark session

    :return: (Session ID, Session URL)
    """
    data = {"kind": "pyspark"}
    req = requests.post(
        LIVY_HOST + '/sessions',
        data=json.dumps(data),
        headers=REQ_HEADERS)
    req.raise_for_status()
    response = req.json()
    return response["id"], req.headers['location']


def execute_code(session_url: str, code: str) -> (int, str):
    """Execute a code in spark

    The job is found in our job registry
    :param job: Job name or job class name
    :param session_url: Livy session url
    :param code: code statements to execute
    :return: (Session ID, Statement URL)
    """
    data = {"code": textwrap.dedent(code)}
    req = requests.post(
        LIVY_HOST + session_url + '/statements',
        data=json.dumps(data),
        headers=REQ_HEADERS)
    try:
        req.raise_for_status()
    except HTTPError:
        response = req.json()
        if "exception" in response.lower():
            response = "".join(response.split(":", maxsplit=1)[1:])
        raise SparkAppError(response)
    response = req.json()
    return response["id"], req.headers['location']


def check_job(session_url: str):
    """Check status of job

    :param session_url: Livy session url
    :return: Session Status
    """
    req = requests.get(LIVY_HOST + session_url + "/state", headers=REQ_HEADERS)
    req.raise_for_status()
    response = req.json()
    return response["state"]


def get_job_output(statement_url: str) -> str:
    """Get job output

    :param statement_url: Session statements URL
    :return: job output
    """
    req = requests.get(LIVY_HOST + statement_url, headers=REQ_HEADERS)
    req.raise_for_status()
    response = req.json()
    if response["state"] == "waiting":
        time.sleep(10)
        return get_job_output(statement_url)
    result = response["output"]
    try:
        if result["status"] == 'error':
            # ename = result["ename"]
            # evalue = result["evalue"]
            trace = "".join(result["traceback"]).strip("\n")
            raise SparkAppError(trace)
    except (TypeError, KeyError):
        raise Exception(response)

    return result["data"]["text/plain"]


def get_session_logs(session_url: str, offset=0, size=1000) -> str:
    """Get session logs

    :param session_url: Livy session url
    :param offset: Offset from start of log
    :param size: Max number of log lines to return
    :return: logs
    :type offset: int
    :type size: int
    """
    req = requests.get(
        "{}{}/log?offset={}&size={}".format(
            LIVY_HOST, session_url, offset, size),
        headers=REQ_HEADERS)
    req.raise_for_status()
    response = req.json()
    return "\n".join(response["log"])


def kill_session(session_url: str) -> None:
    """End session

    :param session_url: Livy session url
    """
    req = requests.delete(LIVY_HOST + session_url)
    req.raise_for_status()


def execute_job_output(
        job: str, sess_url: str, *job_args, **job_kwargs) -> str:
    """Execute a job in our registry and return output

    The job is found in our job registry
    :param job: Job name or job class name
    :param session_url: Livy session url
    :param code: code statements to execute
    :return: job output
    """
    args = ["sc"]  # spark context will be provided by livy
    kwargs = ",".join(["{}={}".format(k, v) for k, v in job_kwargs.items()])
    job_args_kwargs = ",".join(args + list(job_args))
    if kwargs:
        job_args_kwargs += ", "
        job_args_kwargs += kwargs

    code = JOB_TEMPLATE.format(
        job_key_in_registry=job,
        job_args_kwargs=job_args_kwargs
    )
    _, stmnt_url = execute_code(sess_url, code)
    _status = check_job(sess_url)
    while _status not in TERMINAL_STATUS:
        time.sleep(10)
        _status = check_job(sess_url)
    return get_job_output(stmnt_url)


class AirflowDagCallable:

    # initialise pipeline key
    @staticmethod
    def init_key(**kwargs):
        # generate date for job processing
        # persist our date parameter foe retries even a day later
        date_key = datetime.utcnow().strftime("%Y-%m-%d")
        kwargs['ti'].xcom_push(key='date', value=date_key)
        kwargs['ti'].xcom_push(key='days', value=30)

    @staticmethod
    def start_livy_session(**kwargs):
        """Arbitrary callable for our pipeline

        :param func: Function to use in our pipeline
        :param kwargs:
        :return:
        """
        sess_id, sess_url = start_session()
        kwargs['ti'].xcom_push(key="sess_url", value=sess_url)

    @staticmethod
    def check_livy_status(**kwargs):
        """Check if livy session is ready to get our code statements"""
        status = check_job(
            kwargs['ti'].xcom_pull(key="sess_url", task_ids='init_session'))
        logging.info("Session status %s", status)
        if status != "idle":
            time.sleep(5)
            return "livy_status"
        else:
            return "ReactivationPullRecord"

    @staticmethod
    def execute_statement(**kwargs):
        """Arbitrary callable for our pipeline

        :param func: Function to use in our pipeline
        :param kwargs:
        :return:
        """
        sess_url = kwargs['ti'].xcom_pull(key="sess_url",
                                          task_ids="init_session")
        date_ = kwargs['ti'].xcom_pull(key="date", task_ids="init_key")
        days_ = kwargs['ti'].xcom_pull(key="days", task_ids="init_key")
        result = execute_job_output(
            kwargs["job"],
            sess_url,
            days=days_,
            date="'{}'".format(date_)
        )
        logging.info(result)

    @staticmethod
    def spark_logs(**kwargs):
        """Check if livy session is ready to get our code statements"""
        sess_url = kwargs['ti'].xcom_pull(key="sess_url",
                                          task_ids='init_session')
        logging.info(get_session_logs(sess_url))

    @staticmethod
    def end_livy_session(**kwargs):
        """Check if livy session is ready to get our code statements"""
        sess_url = kwargs['ti'].xcom_pull(key="sess_url",
                                          task_ids='init_session')
        kill_session(sess_url)


if __name__ == '__main__':
    import argparse
    import sys

    parser = argparse.ArgumentParser(
        description='Runs demo pipeline. Run `reactivation` or `cancellation`')
    parser.add_argument(
        "-p",
        "--pipeline",
        default="reactivation",
        help="[reactivation|cancellation]"
    )
    pipelines = {
        "reactivation": ("ReactivationPullRecord", "ReactivationUpdateDWH"),
        "cancellation": ("CancellationPullRecord", "CancellationUpdateDWH")
    }
    args = parser.parse_args()
    pipeline = pipelines[args.pipeline.lower()]

    try:
        sess_id, sess_url = start_session()
    except (ConnectionError,):
        print(":Error\n:Spark and Livy not running")
        print(":Maybe you need to run `start.sh` in another terminal first")
        sys.exit(1)

    try:
        job_status = check_job(sess_url)
        while job_status != "idle":
            time.sleep(5)
            job_status = check_job(sess_url)

        print("-----------------")
        print("Job {1}")
        print("Running: {}".format(pipeline[0]))
        print("-----------------\n")
        pull_job = execute_job_output(
            pipeline[0],
            sess_url,
            days=30,
            date="'2019-09-30'"
        )
        print("Job {1} result: ", pull_job)
        print("=================\n")

        print("-----------------")
        print("Job {2}")
        print("Running: {}".format(pipeline[1]))
        print("-----------------\n")
        to_egress_job = execute_job_output(
            pipeline[1],
            sess_url,
            days=30,
            date="'2019-08-30'"
        )
        print("Job {2} result: ", to_egress_job)
        print("=================\n")

    except SparkAppError as serr:
        print("-----------------")
        print("Error encountered")
        print("-----------------\n")
        print(serr)
        print("=================\n")

    finally:
        # print("-----------------")
        # print("Getting session logs")
        # print("-----------------\n")
        # sess_logs = get_session_logs(sess_url)
        # print(sess_logs)
        # print("=================\n")

        print("-----------------")
        print("Killing Session")
        print("-----------------\n")
        kill_session(sess_url)
        print("Spark Session Killed\nBye!\n")
