from __future__ import annotations

import os
import sys

SOURCE_DIR = os.path.dirname(os.path.abspath(__file__))


def install(path=SOURCE_DIR, prepend=True):
    path = os.path.abspath(path)
    if path in sys.path:
        return path
    if prepend:
        sys.path.insert(0, path)
    else:
        sys.path.append(path)
    return path


def from_blend(filepath=None, subdir="source"):
    base = os.path.dirname(os.path.abspath(filepath)) if filepath else os.getcwd()
    return install(os.path.join(base, subdir))


def paths():
    return list(sys.path)


install()
