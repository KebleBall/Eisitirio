#!/usr/bin/env python2
# coding: utf-8
"""Creates a canonical requirements.txt file

Checks what has been installed with pip, and filters it down to the list of
packages in requirements-unversioned.txt - these being the packages which we
need directly
"""

from __future__ import unicode_literals

import subprocess

def main():
    """Run the script."""
    major_packages = []

    with open('requirements-unversioned.txt') as file_handle:
        for line in file_handle:
            major_packages.append(line.strip())

    with open('requirements.txt', 'w') as file_handle:
        for line in subprocess.check_output(['pip', 'freeze']).split('\n'):
            if line.split('==')[0] in major_packages:
                file_handle.write(line + '\n')

if __name__ == '__main__':
    main()
