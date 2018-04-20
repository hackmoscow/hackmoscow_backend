from os import path
from pip.req import parse_requirements
from setuptools import setup, find_packages

install_reqs = parse_requirements(path.join(path.dirname(__file__), 'requirements.txt'), session='')
reqs = [str(ir.req) for ir in install_reqs]

setup(
    name='billing_api',
    version='0.0.1',
    entry_points={
        'console_scripts': [
            'run_api = run_api.__main__:main',
        ]
    },
    install_requires=reqs,
    packages=find_packages(),
    long_description=__doc__,
    include_package_data=True,
)
