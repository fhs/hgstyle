#!/usr/bin/env python
#
# Extracted and modified from lib/codereview/codereview.py
# in Go source tree.
#
# Copyright 2007-2009 Google Inc.
# Copyright 2009 Fazlul Shahriar
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Hooks for enforcing coding style.

The hooks can be used by putting the following in your .hgrc file:

    [hooks]
    pre-commit.pyindent = python:style.pyindenthook
    pre-commit.gofmt = python:style.gofmthook

. The first hook won't allow you to commit code that doesn't conform to PEP8
recommended 4-space indentation or have unnecessary whitespace. To fix this,
use reindent.py, which comes with CPython and can be obtained from

    http://svn.python.org/projects/python/trunk/Tools/scripts/reindent.py

. The hook assumes reindent.py is saved as "pyindent" in $PATH and
will output commands to fix the offending files.

The second hook enforces Go's standard coding style, as dictated by gofmt.
"""

from __future__ import with_statement

import os
import sys
import subprocess
from mercurial import error, scmutil, util
from os.path import join, relpath

from . import pyindent

def getchanged(ui, repo, args, opts):
    matcher = scmutil.match(repo[None], pats=opts['pats'], opts=opts['opts'])
    modified, added, _, _, _, _, _ = repo.status(match=matcher)
    return sorted(modified + added)

def exceptionDetail():
    s = str(sys.exc_info()[0])
    if s.startswith("<type '") and s.endswith("'>"):
        s = s[7:-2]
    elif s.startswith("<class '") and s.endswith("'>"):
        s = s[8:-2]
    arg = str(sys.exc_info()[1])
    if len(arg) > 0:
        s += ": " + arg
    return s

def gofmthook(ui, repo, *args, **opts):
    """Hook that prevents transaction if modified .go file needs
    be to gofmt'ed.
    """
    files = [relpath(join(repo.root, f))
                for f in getchanged(ui, repo, args, opts)
                    if f.endswith('.go')]
    if not files:
        return False
    try:
        cmd = subprocess.Popen(["gofmt", "-l"] + files,
                shell=False, stdin=subprocess.PIPE,
                stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                close_fds=True)
        cmd.stdin.close()
    except OSError, CalledProcessError:
        ui.warn("gofmt: %s\n" % exceptionDetail())
        return True
    data = cmd.stdout.read()
    errors = cmd.stderr.read()
    cmd.wait()
    if len(errors) > 0:
        ui.warn("gofmt errors:\n" + errors.rstrip() + "\n")
        return True
    if len(data) > 0:
        for f in data.strip().split('\n'):
            ui.status("gofmt -w %s\n" % f)
        return True
    return False

def pyindenthook(ui, repo, *args, **opts):
    """Hook that prevents transaction if modified .py file need
    reindenting.
    """
    files = [relpath(join(repo.root, f))
                for f in getchanged(ui, repo, args, opts)
                    if f.endswith('.py')]
    bad = []
    for f in files:
        with open(f, 'r') as fp:
            pi = pyindent.Reindenter(fp)
            if pi.run():
                bad.append(f)

    if bad:
        for f in bad:
            ui.status("pyindent -n %s\n" % f)
        return True
    return False

# vim:ts=4:sw=4:expandtab
