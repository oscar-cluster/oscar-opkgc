#!/bin/bash
./autogen.sh
./configure
make dist
yum -y install python-devel xmlto

RPMS="$(LC_ALL=C rpmbuild -tb opkgc-1.0.2.tar.gz |grep ^Wrote:|cut -d' ' -f2)"

if test -d "$PKGDEST"
then
	echo "  --> Moving ${RPMS} to ${PKGDEST}/"
	mv -f ${RPMS} ${PKGDEST}/
fi

# remove the Makefile to prevent for a second build attempt (make rpm) that would fail
# as there is no rpm: rule.
make distclean
