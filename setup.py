from setuptools import setup, find_packages

setup(
    name="ltlf_merger",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "pytest==7.4.3",
        "flake8==6.1.0",
    ],
    python_requires=">=3.7",
)
