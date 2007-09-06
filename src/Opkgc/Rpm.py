###################################################################
# Copyright (c) 2007 INRIA-IRISA,
#                    Jean Parpaillon <jean.parpaillon@inria.fr>
#                    All rights reserved
# For license information, see the COPYING file in the top level
# directory of the source
###################################################################

from PkgDescription import *
from OpkgDescription import *

class RpmSpec(PkgDescription):
    """ Describe RPM packages
    """
    dependsName = {"requires":"Requires",
                   "conflicts":"Conflicts",
                   "provides":"Provides"}

    def license(self):
        return self.configXml['license']

    def description(self):
        """ Return the description formatted as lines of 80 columns
        """
        t = self.configXml['description']
        desc = ''
        for p in Tools.align_paragraphs(t, 80):
            desc += "%s\n" % p
        return desc
        
    def depends(self, part, relation):
        """ Return list of dependencies of type 'relation' for
        the 'part' package part.
        Relation is one of: requires, conflicts, provides
        Part is one of: apiDeps, serverDeps, clientDeps
        """
        cs = ConfigSchema()
        archs = cs.getArchs()
        archs.append(None)

        out = ""
        for arch in archs:
            deps = []
            deps.extend(self.configXml.getDeps(relation, part, arch, None))
            deps.extend(self.configXml.getDeps(relation, part, arch, self.dist))

            if len(deps) != 0:
                archout = ""
                if arch != None:
                    archout += "%%ifarch %s\n" % arch
                archout += "%s: " % self.dependsName[relation]
                for i, d in enumerate(deps):
                    if i != 0:
                        archout += ', '
                    archout += self.formatPkg(d)
                archout += "\n"
                if arch != None:
                    archout += "%endif\n"
                out += archout

        return out

    def formatPkg(self, p):
        """ Return formatted package dep
        """
        out = p['name']
        if p['version']:
            out += ' %s %s' % (p['op'], p['version'])
        return out

    def filelist(self, part='api'):
        return [ "/%s" % f['dest']
                 for f in self.opkgDesc.getSourceFiles()
                 if f['part'] == part ]

    def scripts(self):
        """ Return scripts pre|post (un)install scripts
        """
        out = ""
        sl = self.opkgDesc.getScripts()
        for s in sl:
            if s['native']:
                rpmscript = RpmScript(s)
                out += "%s\n" % rpmscript['header']
                out += "%s\n" % rpmscript['content']
        
        return out

    def archFilters(self):
        """ Return an ExclusiveArch tag if package-wide filter on arch
        """
        afl = self.configXml.getGlobalArchFilters()
        if len(afl) > 0:
            out = "ExclusiveArch: "
            for af in afl:
                out += " %s" % af
            out += "\n"
            return out
        else:
            return "BuildArch: noarch\n"

    def getSourceFiles(self):
        return [RpmSourceFile(f) for f in self.opkgDesc.getSourceFiles()]

class RpmScript(UserDict):

    def __init__(self, opkgscript):
        UserDict.__init__(self)
        self['header'] = self.__getHeader__(opkgscript)
        self['content'] = self.__getWrapper__(opkgscript)

    def __getHeader__(self, opkgscript):
        res = "%%%s" % opkgscript['time']
        if opkgscript['action']:
            res = "%s%s" % (res, opkgscript['action'])
        if not opkgscript['part'] == "api":
            res = "%s %s" % (res, opkgscript['part'])
        return res

    def __getWrapper__(self, opkgscript):
        wrapper = "#!/bin/sh\n"
        wrapper += "%s $*\n" % os.path.join("/", opkgscript['dest'])
        
        return wrapper

class RpmSourceFile(UserDict):

    def __init__(self, opkgfile):
        UserDict.__init__(self, opkgfile)
        self['sourcedest'] = opkgfile['dest']
