#!/bin/sh
# 
# Copyright 2007 INRIA-IRISA
#        Jean Parpaillon <jean.parpaillon@irisa.fr>
#

AUTOGEN_FILES="aclocal.m4 autom4te.cache configure config.guess config.log config.sub config.status depcomp install-sh compile libtool ltmain.sh missing mkinstalldirs src/.deps"

for file in $AUTOGEN_FILES; do
    rm -rf $file
done    
	
for file in `find -name "Makefile" | grep -v '.svn'`; do
    test -f `dirname $file`/Makefile.in && rm -f $file
done
	
for file in `find -name "Makefile.in" | grep -v '.svn'`; do
    test -f `dirname $file`/Makefile.am && rm -f $file
done
