#! /usr/bin/env python

try:
  import pyver
except ImportError:
  import pip
  pip.main (['install', 'pyver'])
  import pyver # pylint: disable=W0611

from setuptools import setup, find_packages
import glob

__version__, __version_info__ = pyver.get_version (pkg = "coneyeye",
                                                   public = True)

setup (
    name = "coneyeye",
    version = __version__,
    description = "Daemon to map RabbitMQ stats into StatsD",
    long_description = file ("README.rst").read (),
    classifiers = [],
    keywords = "RabbitMQ, StatsD, daemon",
    author = "J C Lawrence",
    author_email = "claw@kanga.nu",
    url = "git@github.com:clearclaw/coneyeye.git",
    license = "GPL v3.0",
    packages = find_packages (exclude = ["tests"]),
    package_data = {"coneyeye": ["_cfgtool/coneyeye",
                                 "_cfgtool/*.templ",
                                 "_cfgtool/install",],
    },
    data_files = [
        ("/etc/cfgtool/module.d/", ["coneyeye/_cfgtool/coneyeye",]),
        ("/etc/coneyeye", glob.glob ("coneyeye/_cfgtool/*.templ")),
    ],
    zip_safe = False,
    install_requires = [line.strip ()
                        for line in file ("requirements.txt").readlines ()],
    entry_points = {
        "console_scripts": [
            "coneyeye = coneyeye.main:main",
        ],
    },
)
