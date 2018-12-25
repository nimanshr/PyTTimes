import glob
import os
import os.path as op
import platform
import shutil
from subprocess import Popen, PIPE
from tempfile import mkdtemp

import numpy as np

from pyrocko.guts import Object, String, List, Bool
from pyrocko.guts_array import Array

from .grid import *
from .table import read_lookup_table
import util


g_model_name = 'LAYER'
g_model_filename = g_model_name + '.tvel'


g_program_bins = {
    'r': 'remodl',
    's': 'setbrn',
    't': 'lookuptable'}


class PyTTimesError(Exception):
    pass


class TauConfig(Object):
    model = String.T(default='ak135')
    phase_list = List.T(String.T())
    file_stem = String.T(optional=True)
    dist_array = Array.T(shape=(None,), dtype=np.float32)
    depth_array = Array.T(shape=(None,), dtype=np.float32)
    save_grid = Bool.T(default=False)


class TauRunner(Object):

    def __init__(self):
        self.program = g_program_bins['t']
        self.config = None
        self.__tempdir = None
        self.__ttimes_dir = None

    def __set_ttimes_dir(self):
        """Make and export required `TTIMES` directory"""
        ttimes_dir = platform.system()
        if not op.isdir(ttimes_dir):
            os.mkdir(ttimes_dir)
        os.environ['TTIMES'] = ttimes_dir
        self.__ttimes_dir = ttimes_dir

    def __remodl_cleaner(self):
        """Remove redundant files"""
        for ext in ('.hed', '.tbl'):
            fn = 'remodl' + ext
            if op.exists(fn):
                os.remove(fn)

    def __remodl_runner(self):
        proc = Popen(
            [g_program_bins['r'], g_model_name], stdout=PIPE, stderr=PIPE)
        out, err = proc.communicate()
        os.remove(g_model_filename)

    def __setbrn_cleaner(self):
        """Remove redundant files"""
        for fn in glob.glob('setbrn*lis'):
            os.remove(fn)

    def __setbrn_runner(self):
        proc = Popen([g_program_bins['s']], stdout=PIPE, stderr=PIPE)
        out, err = proc.communicate()

    def __check(self):
        c = self.config

        if c.depth_array.size > 200:
            raise PyTTimesError(
                'number of depth samples cannot be greater than 200')

        if c.dist_array.size > 2000:
            raise PyTTimesError(
                'number of distance samples cannot be greater than 2000')

        if not op.exists(c.model) and c.model not in util.builtin_models():
            raise PyTTimesError('not such a model: {}'.format(c.model))

        if c.save_grid:
            if len(set(np.ediff1d(c.dist_array))) != 1:
                raise PyTTimesError(
                    'to save as a grid, distance samples must be '
                    'evenly spaced')

            if len(set(np.ediff1d(c.depth_array))) != 1:
                raise PyTTimesError(
                    'to save as a grid, depth samples must be '
                    'evenly spaced')

    def run(self, config):
        self.config = c = config
        self.__check()

        self.__tempdir = mkdtemp(prefix='taurun_', dir=None)

        model_fn = (
            op.exists(c.model) and c.model or
            util.builtin_model_filename(c.model))

        with open(model_fn, 'r') as f, \
                open(op.join(self.__tempdir, g_model_filename), 'w') as g:
            g.write(f.read())

        old_wd = os.getcwd()
        os.chdir(self.__tempdir)
        self.__set_ttimes_dir()

        # Dump distance and depth values into ascii files
        dfile, zfile = 'dist.txt', 'depth.txt'
        np.savetxt(dfile, c.dist_array, fmt='%.6f')
        np.savetxt(zfile, c.depth_array, fmt='%.6f')

        # Remove redundant old files
        self.__remodl_cleaner()

        # Call binaries
        self.__remodl_runner()
        self.__setbrn_runner()

        # Remove redundant files
        self.__remodl_cleaner()
        self.__setbrn_cleaner()

        # Move ".hed" and ".tbl" files
        for ext in ('.hed', '.tbl'):
            src_tail = g_model_name + ext
            dst_full = op.join(self.__ttimes_dir, src_tail)
            shutil.move(src_tail, dst_full)

        # Create the travel-time lookup table
        for phase in c.phase_list:
            proc = Popen(
                [self.program, zfile, dfile, phase, g_model_name],
                stdout=PIPE, stderr=PIPE)

            out, _ = proc.communicate()

            head, tail = op.split(c.file_stem or c.model.rstrip('.tvel'))
            head = head and op.join(old_wd, head) or old_wd
            stem = op.join(head, tail)

            fn_tbl = '{}.{}.tab'.format(stem, phase)
            util.ensuredirs(fn_tbl)
            if op.exists(fn_tbl):
                os.remove(fn_tbl)

            # Save as plaintext file
            with open(fn_tbl, 'wb') as fid:
                fid.write(out)

            # Save as NonLinLoc grid file, if requested
            if c.save_grid:
                nd = c.dist_array.size
                nz = c.depth_array.size

                d_min = np.min(c.dist_array)
                z_min = np.min(c.depth_array)

                dd = np.ediff1d(c.dist_array)[0]
                dz = np.ediff1d(c.depth_array)[0]

                tbl = read_lookup_table(
                    out.splitlines(), wave_type=phase, nd=nd, nz=nz,
                    getmeta=False)

                nll_grid = NLLGrid(
                    basename=stem,
                    float_type='FLOAT',
                    grid_type='TIME2D',
                    wave_type=phase,
                    station=None,
                    shape=GridShape(nx=1, ny=nd, nz=nz),
                    origin=GridOrigin(x=0., y=d_min, z=z_min),
                    spacing=GridSpacing(dx=0., dy=dd, dz=dz),
                    data_array=tbl.data_array[np.newaxis, :, :])

                nll_grid.write_hdr()
                nll_grid.write_buf()

        os.chdir(old_wd)
        shutil.rmtree(self.__tempdir)
