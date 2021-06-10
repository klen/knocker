"""Setup the package."""

from setuptools import setup
from pathlib import Path

reqs = Path(__file__).parent / 'requirements.txt'

setup(
    install_requires=[ln for ln in reqs.read_text().split('\n') if ln and not ln.startswith('#')]
)
