# -*- coding:utf-8 -*-
###################################################################
# Copyright (c) 2007 INRIA-IRISA,
#                    Jean Parpaillon <jean.parpaillon@inria.fr>
#                    All rights reserved
# Copyright (c) 2008 The Trustees of Indiana University.
#                    All rights reserved
# For license information, see the COPYING file in the top level
# directory of the source
###################################################################

import copy
from .PkgDescription import *
from .OpkgDescription import *

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
        Part is one of: apiDeps, serverDeps, clientDeps, opkg
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
            # For server and client, add opkg level deps
            if part == 'serverDeps' or part == 'clientDeps':
                deps.extend(self.configXml.getDeps(relation, 'opkg', arch, None))
                deps.extend(self.configXml.getDeps(relation, 'opkg', arch, self.dist))
            # For api, add opkg conflicts changing name from <name> to OPKG::<name>
            elif part == 'apiDeps' and relation == 'conflicts':
                opkgConflicts = self.configXml.getDeps(relation, 'opkg', arch, None)
                opkgConflicts.extend(self.configXml.getDeps(relation, 'opkg', arch, self.dist))
                for c in opkgConflicts:
                    nc = copy.deepcopy(c)
                    nc['name'] = "OPKG::%s" % c['name']
                    deps.append(nc)

            if len(deps) != 0: # if there are some dependencies
                archout = ""
                if arch != None: # if there is a specific arch, report it
                    archout += "%%if \"%%{_build_arch}\" == \"%s\"\n" % arch
                pkg_d = {} # memory for processed deps
                ver_d = {} # flags for each filters. (if not in: create section)
                version=-1 # no version for generic requirements.
                for i, d in enumerate(deps):
                    if len(d) != 0: # non empty deps
                        xs = d['dist'] # dependancy filter (os, version, ...)
                        for x in xs:   # scann all filters for this "requires"
                            if x['version'] != None:  # filter exists
                                xx = x['version']
                                if xx != version and version != -1:
                                    archout += "\n%endif\n"
                                    archout += "%endif\n"
                                version = xx # keep version tracking so we can add endif when changing.
                                if xx not in ver_d:   # 1st time we see this version => create section
                                    ver_d[xx] = 1     # remember section created
                                    xx = self.replace_comp_sign(xx) # convert comparison sign
                                    archout += "\n%%if \"%%{%s}\"" % distro_d[x['name']]
                                    archout += "\n%%define is_version %%(test %%{vtag} %s && echo 1 || echo 0)" % xx
                                    archout += "\n%if %{is_version}\n"
                                    archout += "%s: " % self.dependsName[relation]
                                else:
                                    archout += ', ' # section exists, just add a ","
                        if len(pkg_d) == 0: # 1st relation:
                            archout += "%s: " % self.dependsName[relation]
                        elif version == -1: # still processing generic requirements
                            archout += ', ' # section exists, jsut add a ","
                        pkg_d[self.formatPkg(d)] = 1 # package processed
                        archout += self.formatPkg(d)
                if version != -1:
                    archout += "\n%endif\n"
                    archout += "%endif\n"
                archout += "\n"
                if arch != None: # OL: Still usefull?
                    archout += "%endif\n"
                archout += "\n"
                out += archout
        return out

    def formatPkg(self, p):
        """ Return formatted package dep
            Note:   p['version'] contains the version for the dependency
                    p['op'] contains the operator regarding the dependency (e.g., "<")
                    So typically, with this two, you know that a dep is for instance < 1.0
        """
        out = p['name']
        if p['version']:
            sign_only = p['version'].strip('1234567890.')
            if (p['op'] == None and sign_only == ""):
                """ Special case: a version is specified but no operator
                """
                p['op'] = "="
            else:
                """ Normal case: we get the version and the operator to create the dependency string
                """
                p['version'] = p['version'].strip('<=>')
            out += ' %s %s' % (p['op'], p['version'])
        return out

    def filelist(self, part=None):
        filelist = self.opkgDesc.getSourceFiles()
        if part:
            return [ f for f in filelist if f['part'] == part ]
        else:
            return filelist

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
        sign_only = str.strip('1234567890.')
        num_only = str.strip('<=>')
        sign_hash = { "=":"-eq",
                      ">":"-gt",
                      ">=":"-ge",
                      "<":"-lt",
                      "<=":"-le",
                      "":"-eq"}
        changed_str = sign_hash[sign_only] + " " + num_only
        return changed_str

    def formatCEntry(self, centry):
        name = centry['name']
        date = centry['date']
        return "%s %s" % (self.date(date, "RPM"), name)

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
