"""Setup the package."""

from pathlib import Path

from setuptools import setup

reqs = Path(__file__).parent / "requirements.txt"
dev_reqs = Path(__file__).parent / "requirements-dev.txt"

setup(
    install_requires=[
        ln for ln in reqs.read_text().split("\n") if ln and not ln.startswith("#")
    ],
    extras_require={
        "dev": ln
        for ln in dev_reqs.read_text().split("\n")
        if ln and not ln.startswith("#")
    },
)
