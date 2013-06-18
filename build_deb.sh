#!/bin/bash
apt-get install autotools-dev python-all-dev xmlto dblatex
./autogen.sh
./configure
make dist

dpkg-buildpackage -b -rfakeroot -uc -us
DEBS=../opkgc*.deb

if test -d "$PKGDEST"
then
	echo "  --> Moving ${DEBS} to ${PKGDEST}/"
	mv -f ${DEBS} ${PKGDEST}/
fi

# remove the Makefile to prevent for a second build attempt (make rpm) that would fail
# as there is no rpm: rule.
make distclean
