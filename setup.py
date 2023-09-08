""" Minimalistic setup.py """

from setuptools import find_packages, setup

setup(
    name="unsplash-photo-trends",
    version="0.1",
    packages=find_packages(),
    author="Marc-Philipp Esser",
    author_email="m-esser@mail.de",
    url="https://github.com/m-p-esser/unsplash_photo_trends",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.10",
)
