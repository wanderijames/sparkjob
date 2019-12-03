"""
Packaging our airflow jobs
"""
from setuptools import setup


setup(
    name='airflow_contrib',
    py_modules=["livy"],
    version='0.0.1',
    author='James Wanderi',
    author_email='wanderikinyanjui@gmail.com',
    description='Livy Operators',
    platforms='any',
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
