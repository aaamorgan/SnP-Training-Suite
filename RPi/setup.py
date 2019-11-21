from setuptools import setup, find_packages
import os.path
import re

here = os.path.abspath(os.path.dirname(__file__))


def read(*parts):
    with open(os.path.join(here, *parts), 'r') as fp:
        return fp.read()


def find_version(*file_paths):
    version_file = read(*file_paths)
    version_match = re.search(
        r"^__version__ = ['\"]([^'\"]*)['\"]", version_file, re.M)
    if version_match:
        return version_match.group(1)
    raise RuntimeError("Unable to find version string.")


setup(
    name='luci-pysensors',
    packages=find_packages(),
        # exclude=["*.tests", "*.tests.*", "tests.*", "tests"]),
    install_requires=['toml>=0.10', 'pyserial>=3.4', 'pyqtgraph>=0.10',
                      'PyQt5>=5.11.3', 'PyOpenGL>=3.1', 'numpy>=1.17'],
    setup_requires=['pytest-runner', 'flake8'],
    # tests_require=['pytest'],
    # TODO (AAM 10/29/2019): Provide entry points
    # entry_points={
    #     'console_scripts': [],
    #     'gui_scripts': [],
    },
)
