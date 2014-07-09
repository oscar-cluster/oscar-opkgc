%{!?python_sitelib: %define python_sitelib %(%{__python} -c "from distutils.sysconfig import get_python_lib; print get_python_lib()")}

Name:           opkgc
Version:        2.0.1
Release:        2%{?dist}
Summary:        Compiler for OSCAR package

Group:          Development/Languages
License:        GPL
URL:            http://oscar.openclustergroup.org/comp_opkgc
Source0:        opkgc-%{version}.tar.gz
BuildRoot:      %{_tmppath}/%{name}-%{version}-%{release}-root-%(%{__id_u} -n)

BuildArch:      noarch
BuildRequires:  python-devel, xmlto, automake, autoconf
Requires: 	python, libxslt, python-lxml, python-cheetah

%description
opkgc transform the description of an OSCAR package into a set of native packages (.deb or RPM).
It includes the opkg-convert tool to convert OSCAR packages from old form to current form.

%prep
%setup -q

%build
if test -x ./autogen.sh
then
	./autogen.sh
fi
%configure --disable-doc-pdf --enable-doc-html

%{__make} %{?_smp_mflags}

%install
rm -rf $RPM_BUILD_ROOT
# cannot use makeinstall macro because pkgdatadir= is not part of the macro.
%__make install DESTDIR=$RPM_BUILD_ROOT
 
%clean
rm -rf $RPM_BUILD_ROOT

%files
%defattr(-,root,root,-)
%doc AUTHORS ChangeLog COPYING README INSTALL
%{python_sitelib}/*
%{_bindir}/opkgc
%{_bindir}/opkg-convert
%{_datadir}/%{name}/
%{_docdir}/%{name}/
%{_mandir}/man1/opkgc.1*
%{_mandir}/man5/opkg.5*
%config %{_sysconfdir}/opkgc.conf

%changelog
* Mon Jun 30 2014 Olivier Lahaye <olivier.lahaye@cea.fr> 2.0.1-2
- Add missing BuildRequires (automake).
* Sun Jan 12 2014 Olivier Lahaye <olivier.lahaye@cea.fr> 2.0.1-1
- bugfix release. See ChangeLog.
* Sun Jan 12 2014 Olivier Lahaye <olivier.lahaye@cea.fr> 2.0.0-1
- Major rewrite of the compiler part to match new apitest filesystem
  hierachy. Now use Makefile.tmpl so deb and rpm sides gets the
  exact same packages.
* Mon Dec 02 2013 Olivier Lahaye <olivier.lahaye@cea.fr> 1.0.3-2
- Got ride of AutoReqProv:no
* Mon Dec 02 2013 Olivier Lahaye <olivier.lahaye@cea.fr> 1.0.3-1
- Migration from /var/lib/oscar/{package,testing} to /usr/lib/oscar (FHS)
* Fri Oct 25 2013 Olivier Lahaye <olivier.lahaye@cea.fr> 1.0.2-2
- use _docdir instead of _defaultdocdir (SuSE packaging issue)
* Mon Jun  3 2013 Olivier Lahaye <olivier.lahaye@cea.fr> 1.0.2-1
- New upstream version.
* Sun Mar 10 2013 Olivier Lahaye <olivier.lahaye@cea.fr> 1.0.1-3
- Restored BuildRequires (xmlto is needed to generate mans).
* Thu Dec 13 2012 Olivier Lahaye <olivier.lahaye@cea.fr> 1.0.1-2
- Use macros when possible.
- Fix man packaging.
- Fix doc packaging.
* Wed Nov 14 2012 Geoffroy Vallee <valleegr@ornl.gov> 1.0.1-1
- Update from upstrean (1.0.1).
* Sun Sep 30 2012 Geoffroy Vallee <valleegr@ornl.gov> 1.0.0-2
- Updated build step using autogen
- Updated file section (doc and use macro instead of
  hardcoded paths)
* Tue Aug 07 2012 Geoffroy Vallee <valleegr@ornl.gov> 1.0.0-1
- Update from upstrean (1.0.0).
* Mon May 30 2011 Geoffroy Vallee <valleegr@ornl.gov> 0.6.0-2
- Run autoreconf before configure.
* Fri Mar 04 2011 Geoffroy Vallee <valleegr@ornl.gov> 0.6.0-1
- Update from upstream (0.6.0).
* Tue Feb 08 2011 Geoffroy Vallee <valleegr@ornl.gov> 0.5.0-1
- Update from upstream (0.5.0).
* Sun Aug 22 2010 Geoffroy Vallee <valleegr@ornl.gov> 0.4.5-1
- Update from upstream (0.4.5).
* Tue Jun 08 2010 Geoffroy Vallee <valleegr@ornl.gov> 0.4.4-1
- Update from upstream (0.4.4)
* Fri Oct 02 2009 Geoffroy Vallee <valleegr@ornl.gov> 0.4.3-1
- Update from upstream (0.4.3)
* Mon Jun 29 2009 Geoffroy Vallee <valleegr@ornl.gov> 0.4.2-1
- Update from upstream (0.4.2)
* Thu Dec 04 2008 Geoffroy Vallee <valleegr@ornl.gov> 0.4.1-1
- Update from upstream (0.4.1)
* Tue Nov 13 2007 Jean Parpaillon <jean.parpaillon@kerlabs.com> 0.4-1
- Update from upstrean (0.4)
* Thu Sep 13 2007 Jean Parpaillon <jean.parpaillon@irisa.fr> 0.3.2-1
- Update from upstream (0.3.2)
- Fix dependency (libxslt that provides xsltproc, needed by opkg-convert)
* Mon Aug 6 2007 Jean Parpaillon <jean.parpaillon@irisa.fr> 0.3.1-1
- Update from upstream (0.3.1)
* Wed Jul 18 2007 Jean Parpaillon <jean.parpaillon@irisa.fr> 0.3-1
- Update from upstream (0.3)
* Wed Jun 27 2007 Jean Parpaillon <jean.parpaillon@irisa.fr> 0.2.1-1
- First RPM release
