#!/bin/sh

set -e

BINDIR=/usr/local/bin

remodl=${BINDIR}/remodl
setbrn=${BINDIR}/setbrn
ttimes=${BINDIR}/ttimes
lookup=${BINDIR}/lookuptable

if [ ! -f ${remodl} ] || [ ! -f ${setbrn} ] || [ ! -f ${ttimes} ] || \
    [ ! -f ${lookup} ]; then

    rm -f ${remodl} ${setbrn} ${ttimes} ${lookup}
    rm -rf iaspei-tau-lookuptable
    tar -xzf iaspei-tau-lookuptable.tar.gz
    cd iaspei-tau-lookuptable
    export BINDIR
    make all
    cd ..
fi
