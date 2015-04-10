#!/usr/bin/env python2

from __future__ import unicode_literals
from __future__ import with_statement

import os
import tempfile
import json
import subprocess
import sys

CMD_GET_BRANCH = ['git', 'rev-parse', '--abbrev-ref', 'HEAD']
CMD_ADD_ALL = ['git', 'add', '--all']
CMD_AMEND_COMMIT = ['git', 'commit', '--amend', '--no-edit']
CMD_PUSH_REVIEW = ['git', 'push', 'review']


def cmd_get_diffbase(branch):
    return ['git', 'merge-base', 'master', branch]


def cmd_get_sha(ref):
    return ['git', 'rev-parse', ref]


def cmd_get_diff(base, target):
    return ['git', 'diff', base, target]


def cmd_change_branch(branch, new=False):
    cmd = ['git', 'checkout']

    if new:
        cmd.append('-b')

    cmd.append(branch)

    return cmd


def cmd_apply_patch(patchfile):
    return ['git', 'apply', patchfile]


def cmd_commit(message):
    return ['git', 'commit', '-m', message]


def main():
    try:
        with open(os.path.realpath(__file__)[:-3] + '.json') as fh:
            reviews = json.load(fh)
    except IOError as _:
        reviews = {}

    branch = subprocess.check_output(CMD_GET_BRANCH).strip()

    if branch == 'HEAD':
        sys.stderr.write('Cannot review a non-branch\n')
        sis.exit(1)

    if branch in reviews:
        diffbase = reviews[branch]
    else:
        diffbase = subprocess.check_output(cmd_get_diffbase(branch)).strip()

    temp = tempfile.NamedTemporaryFile(delete=False)

    temp.write(subprocess.check_output(cmd_get_diff(diffbase, branch)))

    temp.close()

    review_branch = 'review_' + branch

    if branch in reviews:
        subprocess.call(cmd_change_branch(review_branch))
    else:
        subprocess.call(cmd_change_branch(diffbase))
        subprocess.call(cmd_change_branch(review_branch, True))

    subprocess.call(cmd_apply_patch(temp.name))
    subprocess.call(CMD_ADD_ALL)

    if branch in reviews:
        subprocess.call(CMD_AMEND_COMMIT)
    else:
        subprocess.call(cmd_commit(raw_input("Change description: ")))

    subprocess.call(CMD_PUSH_REVIEW)

    os.unlink(temp.name)

    reviews[branch] = subprocess.check_output(cmd_get_sha(branch)).strip()

    with open(os.path.realpath(__file__)[:-3] + '.json', 'w+') as fh:
        json.dump(reviews, fh)

    subprocess.call(cmd_change_branch(branch))

if __name__ == '__main__':
    main()
