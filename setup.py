"""
Packaging our spark jobs
"""
import os
from setuptools import find_packages, setup


_DIR = os.path.abspath(os.path.dirname(__file__))


def f_content(file_path):
    """Get requirements from a file

    :param file_path: file path relative to this file
    :type file_path: str
    :rtype: str"""
    with open(os.path.join(_DIR, file_path), 'r') as f_obj:
        return f_obj.read()


LONG_DESCRIPTION = f_content('README.md')


setup(
    name='jobs',
    version='0.0.1',
    author='James Wanderi',
    author_email='wanderikinyanjui@gmail.com',
    description='Spark Jobs',
    long_description=LONG_DESCRIPTION,
    zip_safe=False,
    platforms='any',
    packages=find_packages("src", exclude="tests"),
    package_dir={"": "src"},
    classifiers=[
        'Development Status :: 4 - Beta',
        'Environment :: Console',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Operating System :: POSIX',
        'Operating System :: MacOS',
        'Operating System :: Unix',
        'Operating System :: Microsoft :: Windows',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 3',
        'Topic :: Software Development :: Libraries :: Python Modules',
    ]
)
