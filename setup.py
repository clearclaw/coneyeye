#! /usr/bin/env python


from setuptools import setup, find_packages
import glob, versioneer

setup (
    name = "coneyeye",
    version = versioneer.get_version (),
    description = "Daemon to map RabbitMQ stats into StatsD",
    long_description = file ("README.rst").read (),
    cmdclass = versioneer.get_cmdclass (),
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
