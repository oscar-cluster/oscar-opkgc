#!/bin/bash
if test -f /usr/bin/yum
then
    yum -y install python-devel xmlto autoconf automake
else
    yast -i python-devel xmlto autoconf automake
fi

./autogen.sh
./configure
make dist

RPMS="$(LC_ALL=C rpmbuild -tb opkgc-1.0.3.tar.gz |grep ^Wrote:|cut -d' ' -f2)"

if test -d "$PKGDEST"
then
	echo "  --> Moving ${RPMS} to ${PKGDEST}/"
	mv -f ${RPMS} ${PKGDEST}/
fi

# remove the Makefile to prevent for a second build attempt (make rpm) that would fail
# as there is no rpm: rule.
make distclean
