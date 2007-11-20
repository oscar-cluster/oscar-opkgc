###################################################################
# Copyright (c) 2007 INRIA-IRISA,
#                    Jean Parpaillon <jean.parpaillon@inria.fr>
#                    All rights reserved
# For license information, see the COPYING file in the top level
# directory of the source
###################################################################

from PkgDescription import *
from OpkgDescription import *
from Logger import *

class DebDescription(PkgDescription):
    """ Describe Debian packages
    """
    dependsName = {"requires":"Depends",
                   "conflicts":"Conflicts",
                   "provides":"Provides",
                   "Opkg-conflicts":"XBCS-Opkg-conflicts"}

    licenses = {"GPL":("GNU General Public License",
                       "/usr/share/common-licenses/GPL"),
                "LGPL":("GNU Lesser General Public License",
                        "/usr/share/common-licenses/LGPL"),
                "BSD":("Berkeley Software Distribution License",
                       "/usr/share/common-licenses/BSD")}

    archName = KeyDict({"x86_64":"ia64"})

    relName = KeyDict({"<":"<<",
                       ">":">>"})

    def arch(self):
        return "all"

    def description(self):
        """ Return the description in Debian format:
            each line begin with a space
        """
        desc = ''
        pat = re.compile(r'\n')
        t = self.configXml['description']
        paragraphs = Tools.align_paragraphs(t, 80)
        i = 0
        while i < len(paragraphs):
            desc += pat.sub(r'\n ', paragraphs[i])
            if i != len(paragraphs)-1:
                desc += '\n .\n'
            i += 1
        return desc

    def debAuthors(self):
        m = self.authors('maintainer')
        u = self.authors('uploader')
        out = "Maintainer: %s\n" % m
        if u:
            out += "Uploaders: %s\n" % u
        return out

    def depends(self, part, relation):
        """ Return list of dependencies of type 'relation' for
        the 'part' package part.
        Relation is one of: requires, conflicts, provides, suggests
        Part is one of: apiDeps, serverDeps, clientDeps, opkg-conflicts
        """
        deps = []
        deps.extend(self.configXml.getDeps(relation, part, "*", None))
        deps.extend(self.configXml.getDeps(relation, part, "*", 'debian'))
        # For server and client, add opkg level deps
        if part == 'serverDeps' or part == 'clientDeps':
            deps.extend(self.configXml.getDeps(relation, 'opkg', "*", None))
            deps.extend(self.configXml.getDeps(relation, 'opkg', "*", 'debian'))
        # For api, add opkg conflicts to a user-defined tag: XBCS-Opkg-conflicts
        elif part == 'apiDeps' and relation == 'Opkg-conflicts':
            deps.extend(self.configXml.getDeps('conflicts', 'opkg', "*", None))
            deps.extend(self.configXml.getDeps('conflicts', 'opkg', "*", 'debian'))

        if len(deps) == 0:
            return ""
        else:
            out = "%s: " % self.dependsName[relation]
            for i, d in enumerate(deps):
                if i != 0:
                    out += ', '
                out += self.formatPkg(d)
            out += "\n"

        Logger().debug(out.strip())

        return out

    def formatPkg(self, p):
        """ Return formatted package dep
        """
        out = p['name']
        if p['version']:
            out += ' (%s %s)' % (self.relName[p['op']], p['version'])
        return out

    def license(self):
        """ Return license name.
        If one of listed in 'licenseFiles' variable, add the path
        to the license file on Debian system (required by Debian Policy, 
        section 12.5)
        """
        out = self.configXml['license']
        try:
            (lName, lPath) = self.licenses[out]
            out += ". On Debian GNU/Linux systems, the complete text of the %s can be found in `%s`." % (lName, lPath)
        except KeyError, e:
            pass
        return Tools.align_lines(out, 80)

    def uploader(self, version):
        """ Return the version uploader
        """
        centry = version['centries'][0]
        name = centry['name']
        date = centry['date']
        validAuthor = False
        ret = "%s  %s" % (name, self.date(date, "RFC822"))

    def getSourceFiles(self):
        return [ DebSourceFile(f) for f in self.opkgDesc.getSourceFiles()]

    def getPackageFiles(self, part):
        return [ DebSourceFile(f)
                 for f in self.opkgDesc.getSourceFiles()
                 if not isinstance(f, OpkgScript) and f['part'] == part ]

    def getInstallFile(self, part):
        if part == 'api':
            return "opkg-%s.install" % self.opkgDesc.getPackageName()
        else:
            return "opkg-%s-%s.install" % (part, self.opkgDesc.getPackageName())

    def uri(self):
        """ Not mandatory, return "" if not found
        """ 
        try:
            return " .\n  %s\n" % Tools.rmNewline(self.configXml['uri'])
        except Exception, e:
            return ""

class DebSourceFile(UserDict):

    scriptsOrigDest = {'api-pre-install'      : 'opkg-%s.preinst',
                       'api-post-install'     : 'opkg-%s.postinst',
                       'api-pre-uninstall'    : 'opkg-%s.prerm',
                       'api-post-uninstall'   : 'opkg-%s.postrm',
                       'server-pre-install'   : 'opkg-server-%s.preinst',
                       'server-post-install'  : 'opkg-server-%s.postinst',
                       'server-pre-uninstall' : 'opkg-server-%s.prerm',
                       'server-post-uninstall': 'opkg-server-%s.postrm',
                       'client-pre-install'   : 'opkg-client-%s.preinst',
                       'client-post-install'  : 'opkg-client-%s.postinst',
                       'client-pre-uninstall' : 'opkg-client-%s.prerm',
                       'client-post-uninstall': 'opkg-client-%s.postrm'}

    def __init__(self, opkgfile):
        UserDict.__init__(self, opkgfile)
        basename = opkgfile['basename']

        if isinstance(opkgfile, OpkgScript):
            try:
                self['sourcedest'] = self.scriptsOrigDest[basename] % opkgfile['part']
            except KeyError:
                self['sourcedest'] = os.path.join("scripts", basename)
        elif isinstance(opkgfile, OpkgDoc):
            self['sourcedest'] = os.path.join("doc", basename)
        elif isinstance(opkgfile, OpkgTest):
            self['sourcedest'] = os.path.join("testing", basename)
        else:
            self['sourcedest'] = basename
