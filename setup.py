from setuptools import setup, find_packages

setup(
    name="proratio",
    version="0.1.0",
    packages=find_packages(),
    entry_points={
        'console_scripts': [
            'proratio = proratio_cli.main:app',
        ],
    },
)
