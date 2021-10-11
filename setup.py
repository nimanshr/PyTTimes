# -*- coding: utf-8 -*-

import sys
from subprocess import check_call

from setuptools import setup
from setuptools.command.build_py import build_py


packname = 'pyttimes'


def make_prerequisites():
    try:
        check_call(['sh', 'prerequisites/prerequisites.sh'])
    except Exception:
        sys.exit(
            'error: failed to build the included prerequisites with '
            '"sh prerequisites/prerequisites.sh"')


class CustomBuildPyCommand(build_py):
    def run(self):
        make_prerequisites()
        build_py.run(self)


setup(
    cmdclass={'build_py': CustomBuildPyCommand},
    name=packname,
    version='0.1.0',
    description='Python wrapper to create seismic travel-time '
                'lookup-tables and/or NonLinLoc binary grid files '
                'through 1-D layered velocity models',
    author='Nima Nooshiri',
    author_email='nima.nooshiri@gmail.com',
    keywords='seismology seismic-travel-times',
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Science/Research',
        'Operating System :: POSIX :: Linux',
        'Programming Language :: Python :: 2.7',
        'Topic :: Scientific/Engineering'],
    python_requires='>=3.8',
    install_requires=['numpy>=1.21.2', 'guts>=0.2'],
    packages=[packname],
    package_dir={packname: 'src'},
    scripts=['apps/{}'.format(packname)],
    package_data={packname: ['data/earth_models/*.tvel']}
)
