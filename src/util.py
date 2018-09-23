# -*- coding: utf-8 -*-

import glob
import os
import os.path as op


class PyTTimesError(Exception):
    pass


def data_file(fn):
    return op.join(op.split(__file__)[0], 'data', fn)


def builtin_model_filename(model_name):
    return data_file(op.join('earth_models', model_name+'.tvel'))


def builtin_models():
    return sorted([
        op.splitext(op.basename(x))[0] for x in
        glob.glob(builtin_model_filename('*'))])


def ensuredirs(dst):
    """
    Create all intermediate path components for a target path.

    Parameters
    ----------
    dst : str
        Target path

    Note
    ----
    The leaf part of the target path is not created.
    """

    d, x = os.path.split(dst)
    dirs = []
    while d and not os.path.exists(d):
        dirs.append(d)
        d, x = os.path.split(d)

    dirs.reverse()

    for d in dirs:
        if not os.path.exists(d):
            os.mkdir(d)
