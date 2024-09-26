# -*- coding: utf-8 -*-


"""setup.py: setuptools control."""


import re
from setuptools import setup


version = re.search(
    '^__version__\s*=\s*"(.*)"',
    open('startlist/startlist.py').read(),
    re.M
    ).group(1)


with open("README.md", "rb") as f:
    long_descr = f.read().decode("utf-8")


setup(
    name = "startlist",
    packages = ["startlist",],
    install_requires = [ "psycopg2", "yattag", "openpyxl", ],
    entry_points = {
        "console_scripts": ['startlist = startlist.startlist:main'],
        },
    package_data = {
        'qlmux': ['static/*/*'],
        },
    version = version,
    description = "RaceDb Proxy for Brother QL Label Printers and Impinj RFID readers",
    long_description = long_descr,
    author = "Stuart Lynne",
    author_email = "stuart.lynne@gmail.com",
    url = "http://bitbucket.org/stuartlynne/qlmux_proxy",
    )
