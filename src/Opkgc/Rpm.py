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
        distro_d = {"rhel":"is_rh",
                    "fc":"is_fc",
                    "mdv":"is_mdv",
                    "suse":"is_suse",
                    "sles":"is_suse"}
                    
        for arch in archs:
            deps = []
            deps.extend(self.configXml.getDeps(relation, part, arch, None))
            deps.extend(self.configXml.getDeps(relation, part, arch, self.dist))
            if part == 'serverDeps' or part == 'clientDeps':
                deps.extend(self.configXml.getDeps(relation, 'commonDeps', arch, None))
                deps.extend(self.configXml.getDeps(relation, 'commonDeps', arch, self.dist))

            if len(deps) != 0:
                archout = ""
                if arch != None:
                    archout += "%%if %%{_build_arch} == %s\n" % arch
                archout += "%s: " % self.dependsName[relation]
                pkg_d = {}
                ver_d = {}
                for i, d in enumerate(deps):
                    if len(d) != 0:
                        xs = d['dist']
                        for x in xs:
                            if x['version'] != None: 
                                xx = x['version']
                                if xx not in ver_d:
                                    ver_d[xx] = 1
                                    xx = self.replace_comp_sign(xx)
                                    archout += "\n%%if %%{%s}" % distro_d[x['name']]
                                    archout += "\n%%define is_version %%(test %%{vtag} %s && echo 1 || echo 0)" % xx
                                    archout += "\n%if %{is_version}\n"
                                    archout += "%s: " % self.dependsName[relation]
                    	archout += self.formatPkg(d)
                    if ((len(deps) > 1) and (i < len(deps) - 1)):
                        archout += ', '
                    if self.formatPkg(d) not in pkg_d and len(ver_d) != 0:
                        pkg_d[self.formatPkg(d)] = 1
                        archout += "\n%endif\n"
                        archout += "%endif\n"
                archout += "\n"
                if arch != None:
                    archout += "%endif\n"
                archout += "\n"
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

    def exclusiveArch(self):
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
            return ""

    def getSourceFiles(self):
        return [RpmSourceFile(f) for f in self.opkgDesc.getSourceFiles()]

    def replace_comp_sign(self, str):
        sign_only = str.strip('1234567890')
        num_only = str.strip('<=>')
        sign_hash = { "=":"-eq",
                      ">":"-gt",
                      ">=":"-ge",
                      "<":"-lt",
                      "<=":"-le",
                      "":"-eq"}
        changed_str = sign_hash[sign_only] + " " + num_only
        return changed_str


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
