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
    install_requires = [ "yattag", "openpyxl", "psycopg2", "autopage", "requests", "BeautifulSoup4", ],
    entry_points = {
        "console_scripts": ['startlist = startlist.startlist:main'],
        },
    package_data = {
        'qlmux': ['static/*/*'],
        },
    version = version,
    description = "CLI to generate startlists and CrossMgr files from RaceDB server.",
    long_description = long_descr,
    author = "Stuart Lynne",
    author_email = "stuart.lynne@gmail.com",
    url = "http://github.com/stuartlynne/startlist",
    )
