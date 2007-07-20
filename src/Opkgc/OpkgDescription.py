###################################################################
# Copyright (c) 2007 INRIA-IRISA,
#                    Jean Parpaillon <jean.parpaillon@inria.fr>
#                    All rights reserved
# For license information, see the COPYING file in the top level
# directory of the source
###################################################################

import re
from time import *
from OpkgcXml import *
from OpkgcTools import *

class OpkgDescription:
    """ Contains data for templates
    """
    xmldoc = None
    month = {"01":"Jan", "02":"Feb", "03":"Mar", "04":"Apr",
             "05":"May", "06":"Jun", "07":"Jul", "08":"Aug",
             "09":"Sep", "10":"Oct", "11":"Nov", "12":"Dec"}
    dist = ""
    depsFactory = None

    def __init__(self, xmldoc, dist):
        self.xmldoc = xmldoc
        self.dist = dist
        self.depsFactory = DependsFactory(xmldoc)

    def isDist(self, dist):
        """ Return true if no package-wide filter on distros or
        dist is part of accepted distros
        """
        distNodes = self.xmldoc.findall('/filters/dist')
        return len(distNodes) == 0 or dist in [d.text for d in distNodes]
        
    def date(self, date, format):
        """ Convert 'xsdDate' in xsd:dateTime format
        (cf. http://www.w3.org/TR/2004/REC-xmlschema-2-20041028/datatypes.html#dateTime)
        and return in the format specified.
        Format is one of:
        'RFC822'
        """
        p = re.compile(r'^-?(?P<year>[0-9]{4})'
                       r'-(?P<month>[0-9]{2})'
                       r'-(?P<day>[0-9]{2})'
                       r'T(?P<hour>[0-9]{2}):'
                       r'(?P<min>[0-9]{2}):'
                       r'(?P<sec>[0-9]{2})(?P<sfrac>\.[0-9]+)?'
                       r'(?P<tz>((?P<tzs>-|\+)(?P<tzh>[0-9]{2}):(?P<tzm>[0-9]{2}))|Z)?')
        m = p.search(date)
        if format == 'RFC822':
            date = "%s %s %s" % (m.group('day'), self.month[m.group('month')], m.group('year'))
            time = "%s:%s" % (m.group('hour'), m.group('min'))
            if m.group('sec'):
                time += ":%s" % m.group('sec')
            zone = ""
            if m.group('tz'):
                if m.group('tz') == "Z":
                    zone = "GMT"
                else:
                    zone = "%s%s%s" % (m.group('tzs'), m.group('tzh'), m.group('tzm'))
            return "%s %s %s" % (date, time, zone)
        else:
            return date

    def name(self):
        p = re.compile('^[a-z0-9][a-z0-9+-\.]+$')
        name = self.node("/name")
        if p.match(name):
            return name
        else:
            raise OpkgSyntaxException('Incorrect package name syntax (pattern: [a-z0-9][a-z0-9+-\.]+)')

    def node(self, path, capitalize=''):
        """ Return the node given by path. Newlines are removed.
        capitalize: lower|upper|<none>
          lower: lower-case node text
          upper: upper-case node text
          <none>: don't touch case
          
        """
        p = re.compile('\n')
        text = self.xmldoc.findtext(path)
        if not text:
            return ""
        
        s = p.sub(' ', text)
        if capitalize == 'lower':
            return s.lower()
        elif capitalize == 'upper':
            return s.upper()
        else:
            return s

    def authors(self, type):
        """ Return comma separated list of authors of type 'type'
        """

        # Get filtered list of authors
        alist = [a for a in self.xmldoc.findall("authors/author") if a.get('cat') == type]
        authors = ''
        i = 0
        for a in alist:
            if i != 0:
                authors += ', '
            authors += self.author(a)
            i += 1
        return authors

    def author(self, etree):
        """ Format an author node:
            Name (nickname) <email@site.ext>
        """
        author = etree.findtext('name')
        nickname = etree.findtext('nickname')
        if nickname != None:
            author += ' (%s)' % nickname
        author += ' <%s>' % etree.findtext('email')
        return author

    def getArchs(self):
        """ Return list of authorized arch filters from config.xml XML schema
        """
        schema = XmlTools().getXsdDoc()
        complexType = filter(lambda x: x.get("name") == "archType",
                             schema.findall("{%s}simpleType" % XmlTools.xsd_uri))[0]
        archs = [e.get("value")
                 for e in complexType.find("{%s}restriction" % XmlTools.xsd_uri).findall("{%s}enumeration" % XmlTools.xsd_uri)]

        return archs

class OpkgDescriptionRpm(OpkgDescription):
    """ Filters out some fields in a opkg description,
        for RPM templates
    """
    dependsName = {"requires":"Requires",
                   "conflicts":"Conflicts",
                   "provides":"Provides"}

    relName = KeyDict()
    
    fileList = []
    scripts = {}

    def archFilters(self):
        """ Return an ExclusiveArch tag if package-wide filter on arch
        """
        archNodes = self.xmldoc.findall('/filters/arch')
        archs = ""        
        for archNode in archNodes:
            archs += " %s" % archNode.text

        out = ""
        if archs != "":
            out = "ExclusiveArch: %s\n" % archs

        return out

    def version(self, part=""):
        """ Return version. If no part is given, return whole version
        part: upstream|release
        """
        version = self.xmldoc.find('changelog/versionEntry').get('version').strip()
        if not part == "":
            return re.match(r'^(?P<upstream>.*)-(?P<release>.*)', version).group(part)
        else:
            return version

    def description(self):
        """ Return the description formatted as lines of 80 columns
        """
        t = self.xmldoc.findtext('/description')
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
        archs = self.getArchs()
        archs.append(None)

        out = ""
        for arch in archs:
            deps = []
            deps.extend(self.depsFactory.getDeps(part=part, relation=relation, arch=arch, dist=None))
            deps.extend(self.depsFactory.getDeps(part=part, relation=relation, arch=arch, dist=self.dist))

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
            out += ' %s %s' % (self.relName[p['op']], p['version'])
        return out

    def fileList(self):
        return self.fileList

    def setFileList(self, fileList):
        """ Set file list for opkg-<package>
        """
        self.fileList = fileList

    def script(self, name):
        """ Return content of script given by 'name'
        """
        try:
            return self.scripts[name]
        except(KeyError):
            return ""

    def setScript(self, name, content):
        """ Set content for script. 'name' follows Rpm naming:
        %pre server, %post, %preun client, etc.
        """
        self.scripts[name] = content

class OpkgDescriptionDebian(OpkgDescription):
    """ Filters out some fields in a opkg description,
        for Debian templates
    """

    archName = KeyDict({"x86_64":"ia64"})

    dependsName = {"requires":"Depends",
                   "conflicts":"Conflicts",
                   "provides":"Provides",
                   "suggests":"Suggests"}

    relName = KeyDict({"<":"<<",
                       ">":">>"})

    def description(self):
        """ Return the description in Debian format:
            each line begin with a space
        """
        desc = ''
        pat = re.compile(r'\n')
        t = self.xmldoc.findtext('/description')
        paragraphs = Tools.align_paragraphs(t, 80)
        i = 0
        while i < len(paragraphs):
            desc += pat.sub(r'\n ', paragraphs[i])
            if i != len(paragraphs)-1:
                desc += '\n .\n'
            i += 1
        return desc

    def arch(self):
        """ Return list of supported archs for the package
        """
        return "all"

    def depends(self, part, relation):
        """ Return list of dependencies of type 'relation' for
        the 'part' package part.
        Relation is one of: requires, conflicts, provides, suggests
        Part is one of: apiDeps, serverDeps, clientDeps
        """
        deps = []
        deps.extend(self.depsFactory.getDeps(part=part, relation=relation, arch="*", dist=None))
        deps.extend(self.depsFactory.getDeps(part=part, relation=relation, arch="*", dist='debian'))

        if len(deps) == 0:
            return ""
        else:
            out = "%s: " % self.dependsName[relation]
            for i, d in enumerate(deps):
                if i != 0:
                    out += ', '
                out += self.formatPkg(d)
            out += "\n"

        Logger().debug(out)

        return out

    def changelog(self):
        """ Return a list of versionEntries
        """
        changelog = []
        vEntryNodes = self.xmldoc.findall('/changelog/versionEntry')
        for vEntryNode in vEntryNodes:

            cEntries = []
            cEntryNodes = vEntryNode.findall('changelogEntry')
            for cEntryNode in cEntryNodes:
                items = [i.text.strip() for i in cEntryNode.findall('item')]
                
                closes = cEntryNode.get('closes')
                if closes:
                    for bug in closes.split():
                        items.append("closes: Bug#%s" % bug)
                
                cEntries.append({"items":items,
                                 "name":cEntryNode.get('authorName')})
            
            vEntry = {"version":vEntryNode.get('version'),
                      "uploader":(self.uploader(vEntryNode)),
                      "logs":cEntries}
            changelog.append(vEntry)

        return changelog

    def uploader(self, versionEntry):
        """ Return the version uploader
        """
        cEntry = versionEntry.find('changelogEntry')
        name = cEntry.get('authorName').strip()
        date = cEntry.get('date')
        authors = self.xmldoc.findall('authors/author')
        for a in authors:
            if a.findtext('name').strip() == name:
                return "%s  %s" % (self.author(a), self.date(date, "RFC822"))

    def copyrights(self, cat):
        """ Return list of copyrights for 'cat'
        cat: mainstream|uploader|upstream
        """
        copyrights = []
        clist = self.xmldoc.findall('authors/author')
        for c in clist:
            if c.get('cat') == cat:
                company = c.findtext('institution')
                if company:
                    ccholder = company
                else:
                    ccholder = "%s <%s>" % (c.findtext('name'), c.findtext('email'))
                beginyear = c.findtext('beginYear')
                endyear = c.findtext('endYear')
                if not(endyear):
                    endyear = "%i" % gmtime().tm_year
                ccyear = ""
                if beginyear:
                    ccyears = "%s-" % beginyear
                ccyear += "%s" % endyear

                cc = "Copyright (c) %s %s\n" % (ccyear, ccholder)
                if company:
                    cc += "\t%s <%s>" % (c.findtext('name'), c.findtext('email'))
                copyrights.append(cc)

        return copyrights

    def formatPkg(self, p):
        """ Return formatted package information for Debian
        """
        out = p['name']
        if p['version']:
            out += " (%s %s)" % (self.relName[p['op']], p['version'])
        if len(p['arch']) != 0:
            out += " ["
            for i, a in enumerate(p['arch']):
                if i != 0:
                    out += " "
                out += "%s" % a
            out += "]"
        return out

class OpkgSyntaxException(Exception):

    msg = None

    def __init__(self, msg):
        self.msg = msg

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
        self.__loadFromXml(xmldoc)

        # Add OSCAR automatic deps
        for part in self.partsReqs.keys():
            p = PackageDeps(name=self.partsReqs[part],
                            relation='requires',
                            part=part)
            self.packageDeps.append(p)

    def __loadFromXml(self, xmldoc):
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

    def __str__(self):
        out = self['name']
        if self['op']:
            out += "%s%s" % (self['op'], self['version'])
        return out

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

    def __str__(self):
        out = "%s %s %s" % (self['part'], self['relation'], self['name'])
        if self['version']:
            out += " (%s%s)" % (self['op'], self['version'])
        if len(self['dist']) > 0:
            out += " for distro "
            for d in self['dist']:
                out += "%s, " % d
        if len(self['arch']):
            out += " for arch "
            for a in self['arch']:
                out += "%s, " % a

        return out
