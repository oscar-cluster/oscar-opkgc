#!/bin/sh
# Copyright 2007 INRIA-IRISA
#		Jean Parpaillon <jean.parpaillon@irisa.fr>
# 

SCRIPT_DIR=`dirname $0`
SCRIPT_DIR=`cd $SCRIPT_DIR && pwd`

$SCRIPT_DIR/clean.sh

#
# check tools version number -- we require >= 1.9
#
find_tools() {
    tool=$1

    if `which $tool-1.9 > /dev/null 2>&1`; then
	TOOL=$tool-1.9
    elif `$tool --version | sed -e '1s/[^9]*//' -e q | grep -v '^$'`; then
	TOOL=$tool
    else
	echo "Required: $tool version 1.9"
	exit 1;
    fi
    
    echo "$TOOL"
}

ACLOCAL=$(find_tools aclocal)
AUTOMAKE=$(find_tools automake)

$ACLOCAL \
    && $AUTOMAKE --add-missing --foreign \
    && autoconf
