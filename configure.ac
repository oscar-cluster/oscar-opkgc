dnl configure.in for opkgc
dnl Copyright 2007 IRISA/INRIA
dnl	      Jean Parpaillon <jean.parpaillon@irisa.fr>
dnl 
dnl Process this file with autoconf to produce a configure script.

dnl autoconf version
AC_PREREQ(2.59)

dnl mandatory stuff
AC_INIT([opkgc], [0.5.0], [oscar-devel@lists.sourceforge.net])

dnl check host and target
AC_CANONICAL_BUILD
AC_CANONICAL_HOST
AC_CANONICAL_TARGET

AM_INIT_AUTOMAKE
AM_MAINTAINER_MODE

dnl check tools
AC_PROG_MAKE_SET
AC_PROG_LN_S
AC_PROG_INSTALL
AC_CHECK_PROG([RSYNC], [rsync], [yes], [no])
if test "$RSYNC" = "no"; then
   AC_MSG_ERROR([
***
*** rsync was not found, but is required
***
])
fi

AM_PATH_PYTHON([2.3])

dnl check documentation tools and options
AC_ARG_ENABLE([doc-pdf],
	      [AS_HELP_STRING([--enable-doc-pdf],
 			      [Do not build pdf doc @<:@default: disable@:>@])],
 	      [],
 	      [enable_doc_pdf="no"])
if test "$enable_doc_pdf" = "yes"; then
   AC_CHECK_PROG([PDFDOC], [dblatex], [yes], [no])
else
   PDFDOC="no"
fi
AC_SUBST(PDFDOC)

AC_CHECK_PROG([XMLTO], [xmlto], [yes], [no])
AC_ARG_ENABLE([doc-html],
	      [AS_HELP_STRING([--enable-doc-html],
			      [Build html doc (splitted pages) @<:@default: disable@:>@])],
	      [],
	      [enable_doc_html="no"])
AC_ARG_ENABLE([doc-one-html],
	      [AS_HELP_STRING([--disable-doc-one-html],
			      [Build html doc (one page) @<:@default: enable@:>@])],
	      [],
	      [enable_doc_one_html="yes"])
if test "$enable_doc_html" = "yes" -a "$XMLTO" = "yes"; then
   HTMLDOC="yes"
else
   HTMLDOC="no"
fi
if test "$enable_doc_one_html" = "yes" -a "$XMLTO" = "yes"; then
   ONEHTMLDOC="yes"
else
   ONEHTMLDOC="no"
fi
AC_SUBST(HTMLDOC)
AC_SUBST(ONEHTMLDOC)

dnl AC_CHECK_PROG([MANDOC], [xmlto], [yes], [no])
if test "$XMLTO" = "yes"; then
   MANDOC="yes"
else
   MANDOC="no"
fi
AC_SUBST(MANDOC)

dnl files to generate with automake
AC_CONFIG_FILES([Makefile])
AC_CONFIG_FILES([src/Makefile])
AC_CONFIG_FILES([src/setup.py])
AC_CONFIG_FILES([doc/Makefile])
AC_CONFIG_FILES([conf/Makefile])
AC_CONFIG_FILES([templates/Makefile])

dnl write all stuff
AC_OUTPUT
