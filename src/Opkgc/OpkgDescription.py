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

__all__ = ['OpkgDescription',
           'OpkgDescriptionDebian',
           'OpkgDescriptionRpm',
           'OpkgSyntaxException']

class OpkgDescription:
    """ Contains data for templates
    """
    oscarDepends = {"clientDeps":"oscar-base-client",
                    "apiDeps":"oscar-base",
                    "serverDeps":"oscar-base-server"}    
    xmldoc = None
    month = {"01":"Jan", "02":"Feb", "03":"Mar", "04":"Apr",
             "05":"May", "06":"Jun", "07":"Jul", "08":"Aug",
             "09":"Sep", "10":"Oct", "11":"Nov", "12":"Dec"}
    dist = ""

    def __init__(self, xmldoc, dist):
        self.xmldoc = xmldoc
        self.dist = dist

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
        s = p.sub(' ', self.xmldoc.findtext(path))
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
        
    def formatDepends(self, dlist, part, relation):
        """ Format a dependancy list element
        (requires|provides|conflicts|suggests).
        relation: dlist parent
        part: relation parent
        (lxml does not keep track of parents :-(
        """
        pkglist = []
        for d in dlist:
            pkglist.extend(d.findall('pkg'))

        depends = ''
        i = 0
        # Add requires for oscar-base-<part>
        if relation == 'requires':
            depends += self.oscarDepends[part]
            i += 1
            
        for pkg in pkglist:
            if i != 0:
                depends += ', '
            depends += self.formatPkg(pkg)
            i += 1
        ret = ''
        if i == 0:
            return ''
        else:
            return self.dependsName[relation] + ': ' + depends + '\n'

    def filterDist(self, elem, dist):
        """ Return true if 'elem' contains a filter for distribution 'dist'
        or no filters at all.
        """
        distFilters = [d.text.strip().lower() for d in elem.findall('filters/dist')]
        return len(distFilters) == 0 or dist in distFilters

class OpkgDescriptionRpm(OpkgDescription):
    """ Filters out some fields in a opkg description,
        for RPM templates
    """
    dependsName = {"requires":"Requires",
                   "conflicts":"Conflicts",
                   "provides":"Provides"}

    relName = {"<":"<",
               "<=":">=",
               "=":"=",
               ">=":">=",
               ">":">"}

    fileList = []
    scripts = {}

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
        Relation is one of: requires, conflicts, provides, suggests
        Part is one of: apiDeps, serverDeps, clientDeps
        """
        dlist = [d
                 for d in self.xmldoc.findall(part + '/' + relation)
                 if self.filterDist(d, self.dist)]
        return self.formatDepends(dlist, part, relation)

    def formatPkg(self, e):
        """ Return formatted package name plus dependancy relation
        """
        ret = e.text.strip()
        version = e.get('version')
        rel = e.get('rel')
        if version:
            ret += ' %s %s' % (self.relName[rel], version)
        return ret

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

    archName = {"i386":"i386",
                "amd64":"amd64",
                "x86_64":"ia64"}

    dependsName = {"requires":"Depends",
                   "conflicts":"Conflicts",
                   "provides":"Provides",
                   "suggests":"Suggests"}

    relName = {"<":"<<",
               "<=":">=",
               "=":"=",
               ">=":">=",
               ">":">>"}

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
        """ Return 'all'
        """
        return "all"

    def depends(self, part, relation):
        """ Return list of dependencies of type 'relation' for
        the 'part' package part.
        Relation is one of: requires, conflicts, provides, suggests
        Part is one of: apiDeps, serverDeps, clientDeps
        """
        dlist = [d
                 for d in self.xmldoc.findall(part + '/' + relation)
                 if self.filterDist(d, self.dist)]
        return self.formatDepends(dlist, part, relation)

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

    def formatPkg(self, e):
        """ Return formatted package name plus dependancy relation
        """
        ret = e.text.strip()
        version = e.get('version')
        rel = e.get('rel')
        if version:
            ret += ' (%s %s)' % (self.relName[rel], version)
        return ret

class OpkgSyntaxException(Exception):

    msg = None

    def __init__(self, msg):
        self.msg = msg
