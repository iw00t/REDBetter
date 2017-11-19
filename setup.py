#!/usr/bin/env python
'''
Installer script for redactedbetter.
'''

from setuptools import setup

import re
VERSIONFILE="_version.py"
verstrline = open(VERSIONFILE, "rt").read()
VSRE = r"^__version__ = ['\"]([^'\"]*)['\"]"
mo = re.search(VSRE, verstrline, re.M)
if mo:
    verstr = mo.group(1)
else:
    raise RuntimeError("Unable to find version string in %s." % (VERSIONFILE,))

setup(
    name = "redactedbetter",
    description = "Automatically transcode and upload FLACs on redacted.ch.",
    version = verstr,
    url = 'https://github.com/Mechazawa/pthbetter-crawler',
    py_modules = [
        '_version',
        'tagging',
        'transcode',
        'redactedapi'
    ],
    scripts = ['redactedbetter'],
    install_requires = [
        'mutagen',
        'mechanize',
        'requests'
    ]
)
