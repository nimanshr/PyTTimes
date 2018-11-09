# -*- coding: utf-8 -*-

import numpy as np

from pyrocko.guts import Object, Int, String
from pyrocko.guts_array import Array


class TableShape(Object):
    nd = Int.T(help='number of distance samples')
    nz = Int.T(help='number of depth samples')


class LookupTable(Object):
    basename = String.T(optional=True)
    wave_type = String.T()
    shape = TableShape.T()
    dist_array = Array.T(shape=(None,), dtype=np.float32, optional=True)
    depth_array = Array.T(shape=(None,), dtype=np.float32, optional=True)
    data_array = Array.T(shape=(None, None), dtype=np.float32)


def read_lookup_table(
        path_or_linelist, wave_type, nd=None, nz=None, getmeta=True):

    if isinstance(path_or_linelist, str):
        with open(path_or_linelist, 'r') as fid:
            lines = fid.read().splitlines()
    else:
        lines = path_or_linelist

    nz = nz or int(lines[1].split()[0])
    nline_z = (nz // 10) + int(nz % 10 != 0)

    nd = nd or int(lines[2+nline_z].split()[0])
    nline_d = (nd // 10) + int(nd % 10 != 0)

    if getmeta:
        # Read depth block
        depths = []
        i1 = 2   # now there are two comment lines
        i2 = i1 + nline_z
        for line in lines[i1:i2]:
            depths.extend(map(float, line.split()))
        depth_array = np.array(depths, dtype=np.float32)

        # Read distance block
        dists = []
        i1 = 3 + nline_z   # now there are three comment lines
        i2 = i1 + nline_d
        for line in lines[i1:i2]:
            dists.extend(map(float, line.split()))
        dist_array = np.array(dists, dtype=np.float32)
    else:
        depth_array, dist_array = None, None

    # Read travel-time block
    nline_top = 3 + nline_z + nline_d   # now there are three comment lines
    data_array = np.zeros((nd, nz), dtype=np.float)
    for iz in range(nz):
        # there is one block per depth value
        start = nline_top + iz*(nd+1)
        end = start + nd
        # first line of each block is a comment
        # now it supports LOCSAT style ascii table (line style: 'time phase')
        data_array[:, iz] = [
            x[0] for x in map(str.split, lines[start+1:end+1])]

    return LookupTable(
        wave_type=wave_type,
        shape=TableShape(nd=nd, nz=nz),
        dist_array=dist_array,
        depth_array=depth_array,
        data_array=data_array)


__all__ = ['TableShape', 'LookupTable', 'read_lookup_table']
