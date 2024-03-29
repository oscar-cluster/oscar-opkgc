# -*- coding:utf-8 -*-
#################################################################
# Copyright (c) 2007 INRIA-IRISA,
#                    Jean Parpaillon <jean.parpaillon@inria.fr>
#                    All rights reserved
# For license information, see the COPYING file in the top level
# directory of the source
#
# Classes handling description of opkg
#
###################################################################

import re
from time import *
from .XmlTools import *
from .Tools import *

class OpkgDescription(object):
    """ Description of an opkg
    """
    versionRe = re.compile(r'^((?P<epoch>[0-9]):)?(?P<upstream>.*)-(?P<release>.*)')
    opkgdir = None
    configXml = None
    arch = None

    def __init__(self, opkgdir):
        # We parse the config.xml file to get data for the target OPKG
        configfile = os.path.join(opkgdir, "config.xml")
        if not os.path.exists(configfile):
            Logger().error("No config.xml file found. Either:")
            Logger().error("* specify the --input=dir option")
            Logger().error("* run opkgc from the opkg directory")
            raise SystemExit(1)
        self.opkgdir = opkgdir
        self.configXml = ConfigXml(configfile)
        if (self.configXml.getNbArchFilters() >= 1):
            self.arch = "any"
        else:
            self.arch = "all"
        Logger().info("Architecture of the generated package: %s" % self.arch)

    def getPackageName(self):
        return self.configXml['name']

    def checkDist(self, dist):
        """ Check if package is available on given dist (regarding filters on config.xml)
        """
        distFilters = self.configXml.getGlobalDistFilters()
        return len(distFilters) == 0 or dist in [df['name'] for df in distFilters]

    def getScripts(self):
        """ Return list of OpkgScript, listing files in scripts/
        Filename relative to opkg dir
        """
        rel_path = [ os.path.join("scripts", f)
                     for f in Tools.ls(os.path.join(self.opkgdir, "scripts")) ]
        list = [ OpkgScript(self.getPackageName(), path)
                 for path in rel_path ]
        return list

    def getDocFiles(self):
        """ Return list of OpkgDoc, listing files in doc/
        Filename relative to opkg dir
        """
        rel_path = [ os.path.join("doc", f)
                     for f in Tools.ls(os.path.join(self.opkgdir, "doc")) ]
        return [ OpkgDoc(self.getPackageName(), path)
                 for path in rel_path ]

    def getTestingFiles(self):
        """ Return list of OpkgTest, listing files in testing/
        Filename relative to opkg dir
        """
        rel_path = [ os.path.join("testing", f)
                     for f in Tools.ls(os.path.join(self.opkgdir, "testing")) ]
        return [ OpkgTest(self.getPackageName(), path)
                 for path in rel_path ]

    def getSourceFiles(self):
        """ Return list of OpkgFile to package
        Filename relative to opkg dir
        """
        files = []
        files.extend(self.getScripts())
        files.extend(self.getDocFiles())
        files.extend(self.getTestingFiles())

        configFile = OpkgFile(self.getPackageName(), "config.xml")
        configFile['dest'] = os.path.join("usr", "lib", "oscar", "packages", self.getPackageName())
        files.append(configFile)

        # [DIKIM] we need to take care of the following configurator
        # files in the meta package.
        config_files = ["configurator.html","configurator_image.html"]
        for configuratorPath in config_files:
            if os.path.exists(os.path.join(self.opkgdir,configuratorPath)):
                configuratorFile = OpkgFile(self.getPackageName(), configuratorPath)
                configuratorFile['dest'] = os.path.join("usr", "lib", "oscar", "packages", self.getPackageName())
                files.append(configuratorFile)
        return files

    def getVersion(self, part=None):
        version = self.configXml['version']
        if not part:
            return version
        else:
            return self.versionRe.match(version).group(part)
    
class ConfigXml(UserDict):
# Implementation of the config.xml parser.

    xmldoc = None
    depsFactory = None
    dist = None

    nameRe = re.compile(r'^[a-z0-9][a-z0-9+-\.]+$')

    def __init__(self, configfile):
        UserDict.__init__(self)
        XmlTools().init(configfile)
        self.xmldoc = XmlTools().getXmlDoc()
        self.depsFactory = DependsFactory(self.xmldoc)

        #print self.xmldoc.findall("class")

        self.__validate__()

    def __validate__(self):
        XmlTools().validate()
        if not self.nameRe.match(self['name']):
            raise OpkgSyntaxException('Incorrect package name syntax (pattern: [a-z0-9][a-z0-9+-\.]+)')

    def __getitem__(self, key):
        if key == 'version':
            return self.xmldoc.find('changelog/versionEntry').get('version').strip()
        else:
            return self.xmldoc.findtext('/%s' % key).strip()

    def getAuthors(self, cat=None):
        al = [ Author(e) for e in self.xmldoc.findall("authors/author")]
        if cat:
            al = [ a for a in al if a['cat'] == cat ]
        return al

    def getDeps(self, relation, part, arch, dist):
        return self.depsFactory.getDeps(relation, part, arch, dist)

    def getChangelog(self):
        return [ ChangelogVEntry(e) for e in self.xmldoc.findall('/changelog/versionEntry') ]

    def getGlobalDistFilters(self):
        (dists, arch) = self.depsFactory.getFilters(self.xmldoc.find('/filters'))
        return dists

    def getNbArchFilters(self):
        (dists, arch) = self.depsFactory.getFilters(self.xmldoc.find('/filters'))
        l = self.xmldoc.findall('serverDeps/requires/filters/arch')
        return len(l)

    def getGlobalArchFilters(self):
        (dists, arch) = self.depsFactory.getFilters(self.xmldoc.find('/filters'))
        for a in arch:
            Logger().debug ("-> Arch " + a)
        for d in dists:
            Logger().debug ("-> Dist " + d['name'])
        l = self.xmldoc.findall('serverDeps/requires/filters/arch')
        Logger().info("Number of arch filters: %d" % len(l))
        return arch

class ConfigSchema(object):

    schemaTree = None

    def __init__(self):
        self.schemaTree = XmlTools().getXsdDoc()        
    
    def getArchs(self):
        """ Return list of authorized arch filters
        """
        complexType = [x for x in self.schemaTree.findall("{%s}simpleType" % XmlTools.xsd_uri) if x.get("name") == "archType"][0]
        archs = [e.get("value")
                 for e in complexType.find("{%s}restriction" % XmlTools.xsd_uri).findall("{%s}enumeration" % XmlTools.xsd_uri)]

        return archs

class Author(UserDict):
    etree = None

    def __init__(self, etree):
        UserDict.__init__(self)
        self.etree = etree

    def __getitem__(self, key):
        if key == 'cat':
            return self.etree.get(key)
        else:
            s = self.etree.findtext(key)
            if s:
                return Tools.rmNewline(s)
            else:
                return None

class ChangelogVEntry(UserDict):
    """ Contains all changelog infos for a version
    """

    def __init__(self, etree):
        UserDict.__init__(self)
        self['version'] = etree.get('version')
        self['centries'] = [ ChangelogCEntry(e) for e in etree.findall('changelogEntry') ]

class ChangelogCEntry(UserDict):
    """ Contains all changelog infos for an author in a version
    """
    def __init__(self, etree):
        UserDict.__init__(self)
        self['items'] = [ e.text.strip() for e in etree.findall('item')]
        closes = etree.get('closes')
        if closes:
            self['closes'] = closes.split()
        else:
            self['closes'] = []
        self['name'] = etree.get('authorName').strip()
        self['date'] = etree.get('date')

class DependsFactory(object):
    """ Store an retrieve package dependancy informations
    """
    partsReqs = {"clientDeps":"liboscar-client",
                 "apiDeps":"oscar-data",
                 "serverDeps":"liboscar-server"}

    packageDeps = None
    filters = None

    def __init__(self, xmldoc):
        self.packageDeps = []
        self.filters = []
        self.__loadFromXml__(xmldoc)

        # Add OSCAR automatic deps
        for part in list(self.partsReqs.keys()):
            p = PackageDeps(name=self.partsReqs[part],
                            relation='requires',
                            part=part)
            self.packageDeps.append(p)

    def __loadFromXml__(self, xmldoc):
        """ Load packageDeps from xmldoc
        """
        # load deps for api, server, client
        for pn in self.getPartNames():
            part = xmldoc.find("/%s" % pn)
            if part is not None:
                self.__loadPartDeps__(pn, part)

        # load deps at opkg level
        self.__loadPartDeps__('opkg', xmldoc.find("/"))

    def __loadPartDeps__(self, partName, part):
        for rn in self.getRelationNames():
            relations = part.findall('%s' % rn)
            for r in relations:
                (dists, archs) = self.getFilters(r.find('filters'))
                self.filters.extend(dists)
                self.filters.extend(archs)
                    
                pkgList = r.findall("pkg")
                for pkg in pkgList:
                    p = PackageDeps(name=pkg.text,
                                    op=pkg.get("rel"),
                                    version=pkg.get("version"),
                                    arch=archs,
                                    dist=dists,
                                    relation=rn,
                                    part=partName)
                    self.packageDeps.append(p)

    def getFilters(self, e):
        """ Return 2 lists: dist and arch filters of
        an filters element
        """
        dists = []
        archs = []

        if e is not None:
            for df in e.findall('dist'):
                d = DistFilter(name=df.text,
                               op=df.get("rel"),
                               version=df.get("version"))
                dists.append(d)
            for af in e.findall('arch'):
                archs.append(af.text)

        return (dists, archs)
        

    def getPartNames(self):
        schema = XmlTools().getXsdDoc()
        return [e.get("name")
                for e in [x for x in schema.findall('/{%s}element' % XmlTools.xsd_uri) if x.get("type") == "depsListType"]]

    def getRelationNames(self):
        schema = XmlTools().getXsdDoc()
        complexType = [x for x in schema.findall('{%s}complexType' % XmlTools.xsd_uri) if x.get("name") == "depsListType"][0]
        return [e.get("ref")
                for e in complexType.find('{%s}sequence' % XmlTools.xsd_uri).findall('{%s}element' % XmlTools.xsd_uri)]

    def getDeps(self, relation, part, arch=None, dist=None):
        """ Return list of PackageDeps matching the given criteria
        arch can be '*' and return all archs
        """
        ret = []

        for p in self.packageDeps:
            if p['relation'] !=  relation:
                continue
            if p['part'] != part:
                continue
            if arch != '*':
                if (arch and not arch in p['arch']) \
                       or (not arch and len(p['arch']) > 0):
                    continue
            if (dist and dist not in [d['name'] for d in p['dist']]) \
                   or (not dist and len(p['dist']) > 0):
                continue

            ret.append(p)
                        
        return ret

class DistFilter(NoneDict):

    def __init__(self, name, op=None, version=None):
        NoneDict.__init__(self)
        self['name'] = name
        self['op'] = op
        self['version'] = version

class PackageDeps(NoneDict):

    def __init__(self, name, relation, part, op=None, version=None, arch=[], dist=[]):
        NoneDict.__init__(self)
        self['name'] = name
        self['arch'] = arch
        self['dist'] = dist
        self['relation'] = relation
        self['op'] = op
        self['version'] = version
        self['part'] = part

class OpkgFile(UserDict):

    def __init__(self, pkg, filename):
        UserDict.__init__(self)
        self['pkg'] = pkg
        self['part'] = 'api' # By default: part = api
        # path relative to opkg
        self['orig'] = filename
        self['basename'] = os.path.basename(filename)

class OpkgDoc(OpkgFile):

    def __init__(self, pkg, filename):
        OpkgFile.__init__(self, pkg, filename)
        self['dest'] = os.path.join("usr", "share", "doc", "opkg-%s" % pkg)

class OpkgTest(OpkgFile):

    def __init__(self, pkg, filename):
        OpkgFile.__init__(self, pkg, filename)
        test_d_re = re.compile('.*tests\.d')
        # Testing contains only directories.
        # If it ends with test.d, the directory is already owned by oscar-base: we add /* to work only on its content.
        if os.path.isdir (filename):
            if test_d_re.match(filename):
                self['orig'] = os.path.join(self['orig'],"*")
                self['dest'] = os.path.join("usr", "lib", "oscar", "testing", self['basename'])
                self['basename'] = "*" # When packaged, f.dest/f.basename becomes f.dest/* => we don't own the package.
            else: # This is the "data/<pkg> dir" We need to own it.
                self['orig'] = os.path.join(self['orig'],"*") # We work on files to reparent
                self['dest'] = os.path.join("usr", "lib", "oscar", "testing", "data" ,"%s" % pkg) # New Path
                self['basename'] = "" # When packaged, f.dest/f.basename becomes f.dest/ => we own the package.
        else:
            Logger().debug("Not a directory: (%s) => Moved into data. Please migrate to new apitest" % filename)
            self['dest'] = os.path.join("usr", "lib", "oscar", "testing", "data" ,"%s" % pkg) # Moved into data dir.

class OpkgScript(OpkgFile):

    scriptRe = re.compile(r'(?P<part>api|client|server)-(?P<time>pre|post)-(?P<action>un)?install')

    def __init__(self, pkg, filename):
        # filename = os.path.basename (filename)
        OpkgFile.__init__(self, pkg, filename)
        self['native'] = self.__isNative__()

        part = self.__extract__('part') # api|client|server
        self['part'] = part
        self['time'] = self.__extract__('time') # pre|post
        self['action'] = self.__extract__('action') # install|uninstall
        self['dest'] = os.path.join("usr", "lib", "oscar", "packages", pkg)

    def __isNative__(self):
        """ True if script is one of scripts included as
        {pre|post}{inst|rm} scripts
        name: basename of the script
        """
        return self.scriptRe.match(self['basename']) # Matches pkg name at the beginning of the script name or None

    def __extract__(self, group): # group = part|time|action
        m = self.scriptRe.match(self['basename'])
        if m:
            return m.group(group)
        else:
            return 'api'
        
