import io

from setuptools import find_packages, setup

# This reads the __version__ variable from cirq/_version.py
__version__ = ""
exec(open("cirq_superstaq/_version.py").read())

name = "cirq-superstaq"

description = "The Cirq module that provides tools and access to SuperstaQ"

# README file as long_description.
long_description = io.open("README.md", encoding="utf-8").read()

# Read in requirements
requirements = open("requirements.txt").readlines()
requirements = [r.strip() for r in requirements]

# Sanity check
assert __version__, "Version string cannot be empty"


cirq_superstaq_packages = ["cirq_superstaq"] + [
    "cirq_superstaq." + package for package in find_packages(where="cirq_superstaq")
]

setup(
    name=name,
    version=__version__,
    url="https://github.com/SupertechLabs/cirq-superstaq",
    author="Super.tech",
    author_email="pranav@super.tech",
    python_requires=(">=3.7.0"),
    install_requires=requirements,
    license="Apache 2",
    description=description,
    long_description=long_description,
    long_description_content_type="text/markdown",
    packages=cirq_superstaq_packages,
    package_data={"cirq_superstaq": ["py.typed"]},
)
