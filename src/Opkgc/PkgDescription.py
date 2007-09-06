###################################################################
# Copyright (c) 2007 INRIA-IRISA,
#                    Jean Parpaillon <jean.parpaillon@inria.fr>
#                    All rights reserved
# For license information, see the COPYING file in the top level
# directory of the source
#
# Parent class for output package description
#
###################################################################

import re
from time import *
from Logger import *
from Tools import *
from OpkgDescription import *

class PkgDescription(object):

    opkgDesc = None
    configXml = None
    dist = None

    month = {"01":"Jan", "02":"Feb", "03":"Mar", "04":"Apr",
             "05":"May", "06":"Jun", "07":"Jul", "08":"Aug",
             "09":"Sep", "10":"Oct", "11":"Nov", "12":"Dec"}
    dateRe = re.compile(r'^-?(?P<year>[0-9]{4})'
                        r'-(?P<month>[0-9]{2})'
                        r'-(?P<day>[0-9]{2})'
                        r'T(?P<hour>[0-9]{2}):'
                        r'(?P<min>[0-9]{2}):'
                        r'(?P<sec>[0-9]{2})(?P<sfrac>\.[0-9]+)?'
                        r'(?P<tz>((?P<tzs>-|\+)(?P<tzh>[0-9]{2}):(?P<tzm>[0-9]{2}))|Z)?')
    versionRe = re.compile(r'^(?P<upstream>.*)-(?P<release>.*)')

    def __init__(self, opkgDesc, dist):
        self.opkgDesc = opkgDesc
        self.configXml = opkgDesc.configXml
        self.dist = dist

    def changelog(self):
        """ Return a list of versionEntries
        """
        return self.configXml.getChangelog()

    def summary(self):
        return Tools.rmNewline(self.configXml['summary'])
            
    def name(self):
        return self.configXml['name']

    def version(self, part=None):
        version = self.configXml['version']
        if not part:
            return version
        else:
            return self.versionRe.match(version).group(part)
       
    def group(self):
        return self.configXml['group']

    def authors(self, type):
        """ Return comma separated list of authors of type 'type'
        """
        # Get filtered list of authors
        alist = self.configXml.getAuthors(type)
        Logger().debug("%s: %d" % (type, len(alist)))
        authors = ''
        i = 0
        for a in alist:
            if i != 0:
                authors += ', '
            authors += self.formatAuthor(a)
            i += 1
        return authors

    def formatAuthor(self, author):
        """ Format an author object:
            Name (nickname) <email@site.ext>
        """
        res = author['name']
        nickname = author['nickname']
        if nickname != None:
            res += ' (%s)' % nickname
        res += ' <%s>' % author['email']
        return res

    def uri(self):
        return Tools.rmNewline(self.configXml['uri'])

    def copyrights(self, cat):
        """ Return list of copyrights for 'cat'
        cat: mainstream|uploader|upstream
        """
        copyrights = []
        authors = self.configXml.getAuthors(cat)
        for a in authors:
            company = a['institution']
            if company:
                ccholder = company
            else:
                ccholder = "%s <%s>" % (a['name'], a['email'])
            beginyear = a['beginYear']
            endyear = a['endYear']
            if not(endyear):
                endyear = "%i" % gmtime().tm_year
            ccyear = ""
            if beginyear:
                ccyears = "%s-" % beginyear
            ccyear += "%s" % endyear

            cc = "Copyright (c) %s %s\n" % (ccyear, ccholder)
            if company:
                cc += "\t%s <%s>" % (a['name'], a['email'])
            copyrights.append(cc)

        return copyrights

    def date(self, date, format):
        """ Convert 'xsdDate' in xsd:dateTime format
        (cf. http://www.w3.org/TR/2004/REC-xmlschema-2-20041028/datatypes.html#dateTime)
        and return in the format specified.
        Format is one of:
        'RFC822'
        """
        m = self.dateRe.search(date)
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
