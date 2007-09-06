###################################################################
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
from XmlTools import *
from Tools import *

class OpkgDescription(object):
    """ Description of an opkg
    """
    opkgdir = None
    configXml = None

    def __init__(self, opkgdir):
        self.opkgdir = opkgdir
        self.configXml = ConfigXml(self.getConfigFile())

    def getPackageName(self):
        return self.configXml['name']

    def getConfigFile(self):
        """ Return path of config.xml file
        Raise exception if not found
        """
        path = os.path.join(self.opkgdir, "config.xml")
        if not os.path.exists(path):
            Logger().error("No config.xml file found. Either:")
            Logger().error("* specify the --input=dir option")
            Logger().error("* run opkgc from the opkg directory")
            raise SystemExit
        return path

    def checkDist(self, dist):
        """ Check if package is available on given dist (regarding filters on config.xml)
        """
        distFilters = self.configXml.getGlobalDistFilters()
        return len(distFilters) == 0 or dist in [df['name'] for df in distFilters]

    def getScripts(self):
        """ Return list of OpkgScript, listing files in scripts/
        """
        return [ OpkgScript(self.getPackageName(), path)
                 for path in Tools.listFiles(os.path.join(self.opkgdir, "scripts"))]

    def getDocFiles(self):
        """ Return list of OpkgDoc, listing files in doc/
        """
        return [ OpkgDoc(self.getPackageName(), path)
                 for path in Tools.listFiles(os.path.join(self.opkgdir, "doc"))]

    def getTestingFiles(self):
        """ Return list of OpkgTest, listing files in testing/
        """
        return [ OpkgTest(self.getPackageName(), path)
                 for path in Tools.listFiles(os.path.join(self.opkgdir, "testing"))]

    def getSourceFiles(self):
        """ Return list of OpkgFile to package
        """
        files = []
        files.extend(self.getScripts())
        files.extend(self.getDocFiles())
        files.extend(self.getTestingFiles())
        
        configFile = OpkgFile(self.getPackageName(), self.getConfigFile())
        configFile['dest'] = os.path.join("var", "lib", "oscar", "packages",
                                          self.getPackageName(),
                                          configFile['basename'])
        files.append(configFile)

        configuratorPath = os.path.join(self.opkgdir, "configurator.html")
        if os.path.exists(configuratorPath):
            configuratorFile = OpkgFile(self.getPackageName(), configuratorPath)
            configuratorFile['dest'] = os.path.join("var", "lib", "oscar", "packages",
                                                    self.getPackageName(),
                                                    configuratorFile['basename'])
            files.append(configuratorFile)

        return files

class ConfigXml(UserDict):

    xmldoc = None
    depsFactory = None
    dist = None

    nameRe = re.compile(r'^[a-z0-9][a-z0-9+-\.]+$')

    def __init__(self, configfile):
        UserDict.__init__(self)
        XmlTools().init(configfile)
        self.xmldoc = XmlTools().getXmlDoc()
        self.depsFactory = DependsFactory(self.xmldoc)

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

    def getGlobalArchFilters(self):
        (dists, arch) = self.depsFactory.getFilters(self.xmldoc.find('/filters'))
        return arch

class ConfigSchema(object):

    schemaTree = None

    def __init__(self):
        self.schemaTree = XmlTools().getXsdDoc()        
    
    def getArchs(self):
        """ Return list of authorized arch filters
        """
        complexType = filter(lambda x: x.get("name") == "archType",
                             self.schemaTree.findall("{%s}simpleType" % XmlTools.xsd_uri))[0]
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
    partsReqs = {"clientDeps":"oscar-base-client",
                 "apiDeps":"oscar-base",
                 "serverDeps":"oscar-base-server"}

    packageDeps = None
    filters = None

    def __init__(self, xmldoc):
        self.packageDeps = []
        self.filters = []
        self.__loadFromXml__(xmldoc)

        # Add OSCAR automatic deps
        for part in self.partsReqs.keys():
            p = PackageDeps(name=self.partsReqs[part],
                            relation='requires',
                            part=part)
            self.packageDeps.append(p)

    def __loadFromXml__(self, xmldoc):
        """ Load packageDeps from xmldoc
        """
        for pn in self.getPartNames():
            part = xmldoc.find("/%s" % pn)
            if part:
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
                                            part=pn)
                            self.packageDeps.append(p)

    def getFilters(self, e):
        """ Return 2 lists: dist and arch filters of
        an filters element
        """
        dists = []
        archs = []

        if e:
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
                for e in filter(lambda x: x.get("type") == "depsListType",
                                schema.findall('/{%s}element' % XmlTools.xsd_uri))]

    def getRelationNames(self):
        schema = XmlTools().getXsdDoc()
        complexType = filter(lambda x: x.get("name") == "depsListType",
                             schema.findall('{%s}complexType' % XmlTools.xsd_uri))[0]
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
        self['part'] = 'api'
        self['path'] = filename
        self['basename'] = os.path.basename(filename)

class OpkgDoc(OpkgFile):

    def __init__(self, pkg, filename):
        OpkgFile.__init__(self, pkg, filename)
        self['dest'] = os.path.join("usr", "share", "doc", "opkg-%s" % pkg, self['basename'])

class OpkgTest(OpkgFile):

    def __init__(self, pkg, filename):
        OpkgFile.__init__(self, pkg, filename)
        self['dest'] = os.path.join("var", "lib", "oscar", "testing", "%s" % pkg, self['basename'])

class OpkgScript(OpkgFile):

    scriptRe = re.compile(r'(?P<part>api|client|server)-(?P<time>pre|post)-(?P<action>un)?install')

    def __init__(self, pkg, filename):
        OpkgFile.__init__(self, pkg, filename)
        self['native'] = self.__isNative__()

        part = self.__extract__('part')
        if part:
            self['part'] = part
        else:
            self['part'] = 'api'
        self['time'] = self.__extract__('time')
        self['action'] = self.__extract__('action')
        self['dest'] = os.path.join("var", "lib", "oscar", "packages", pkg, self['basename'])

    def __isNative__(self):
        """ True if script is one of scripts included as
        {pre|post}{inst|rm} scripts
        name: basename of the script
        """
        return self.scriptRe.match(self['basename'])

    def __extract__(self, group):
        m = self.scriptRe.match(self['basename'])
        if m:
            return m.group(group)
        else:
            return ''
        
class OpkgSyntaxException(Exception):

    msg = None

    def __init__(self, msg):
        self.msg = msg
