"""Setup the package."""

from pathlib import Path

import pkg_resources
from setuptools import setup

reqs = Path(__file__).parent / "requirements.txt"
dev_reqs = Path(__file__).parent / "requirements-dev.txt"


def parse_requirements(path: str) -> "list[str]":
    with Path(path).open() as requirements:
        return [str(req) for req in pkg_resources.parse_requirements(requirements)]


setup(
    install_requires=parse_requirements("requirements.txt"),
    extras_require={"dev": parse_requirements("requirements-dev.txt")},
)
