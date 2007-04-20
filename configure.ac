dnl configure.in for opkgc
dnl Copyright 2007 IRISA/INRIA
dnl	      Jean Parpaillon <jean.parpaillon@irisa.fr>
dnl 
dnl Process this file with autoconf to produce a configure script.

dnl autoconf version
AC_PREREQ(2.59)

dnl mandatory stuff
AC_INIT([opkgc], [0.1], [oscar-users@lists.sourceforge.net])

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

AC_MSG_CHECKING([python])
if which python > /dev/null; then
  AC_MSG_RESULT([yes])
else
  AC_MSG_RESULT([not found])
  AC_MSG_ERROR([ *** Please install python ***])
fi

dnl check documentation tools and options
dnl AC_ARG_ENABLE([doc-pdf],
dnl 	      [AS_HELP_STRING([--disable-doc-pdf],
dnl 			      [Do not build pdf doc @<:@default: enable@:>@])],
dnl 	      [],
dnl 	      [enable_doc_pdf="yes"])
dnl if test "$enable_doc_pdf" = "yes"; then
dnl    AC_CHECK_PROG([PDFDOC], [db2pdf], [yes], [no])
dnl else
dnl    PDFDOC="no"
dnl fi
PDFDOC="no"
AC_SUBST(PDFDOC)

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
AC_CHECK_PROG([DB2HTML], [xmlto], [yes], [no])
if test "$enable_doc_html" = "yes" -a "$DB2HTML" = "yes"; then
   HTMLDOC="yes"
else
   HTMLDOC="no"
fi
if test "$enable_doc_one_html" = "yes" -a "$DB2HTML" = "yes"; then
   ONEHTMLDOC="yes"
else
   ONEHTMLDOC="no"
fi
AC_SUBST(HTMLDOC)
AC_SUBST(ONEHTMLDOC)

AC_CHECK_PROG([MANDOC], [xmlto], [yes], [no])
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
