#!/usr/bin/env python2
# coding: utf-8
"""Creates a canonical requirements.txt file

Checks what has been installed with pip, and filters it down to the list of
packages in requirements-unversioned.txt - these being the packages which we
need directly
"""

import subprocess

packages = []

with open('requirements-unversioned.txt') as fh:
    for line in fh:
        packages.append(line.strip())

with open('requirements.txt', 'w') as fh:
    for line in subprocess.check_output(['pip', 'freeze']).split('\n'):
        if line.split('==')[0] in packages:
            fh.write(line + '\n')
