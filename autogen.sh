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
    else
	major=`$tool --version | grep $tool | awk {'print \$4'} | awk -F '.' {'print \$1'}`
	minor=`$tool --version | grep $tool | awk {'print \$4'} | awk -F '.' {'print \$2'}`
	if [ "$major" -gt 1 ]; then
		TOOL=$tool
	elif [ "$major" -eq 1 ] && [ "$minor" -ge 9 ]; then
		TOOL=$tool
	else
		echo "Required: $tool version >= 1.9"
		exit 1;
	fi
    fi
    
    echo "$TOOL"
}

ACLOCAL=$(find_tools aclocal)
AUTOMAKE=$(find_tools automake)

$ACLOCAL \
    && $AUTOMAKE --add-missing --foreign \
    && autoconf
