from setuptools import setup, find_packages

with open("requirements.txt") as f:
    install_requires = f.read().strip().split("\n")

# get version from __version__ variable in salla_client/__init__.py
from salla_client import __version__ as version

setup(
    name="salla_client",
    version=version,
    description="Salla Client",
    author="Golive-Solutions",
    author_email="info@golive-solutions.com",
    packages=find_packages(),
    zip_safe=False,
    include_package_data=True,
    install_requires=install_requires
) 