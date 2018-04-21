from os import path
from setuptools import setup, find_packages

def parse_requirements(filename):
    """ load requirements from a pip requirements file """
    lineiter = (line.strip() for line in open(filename))
    return [line for line in lineiter if line and not line.startswith("#")]

install_reqs = parse_requirements(path.join(path.dirname(__file__), 'requirements.txt'))
reqs = [str(ir) for ir in install_reqs]

tests_require = [ ]
setup(
    name='zabor_api',
    version='0.0.1',
    entry_points={
        'console_scripts': [
            'run_zabor_api = api.__main__:main',
        ]
    },
    install_requires=reqs,
    setup_requires=[ ],
    tests_require=tests_require,
    packages=find_packages(),
    long_description=__doc__,
    include_package_data=True,
)
