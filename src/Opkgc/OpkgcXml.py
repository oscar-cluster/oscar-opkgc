###################################################################
# Copyright (c) 2007 Oak Ridge National Laboratory,
#                    Geoffroy Vallee <valleegr@ornl.gov>
#                    All rights reserved
# Copyright (c) 2007 IRISA-INRIA
#                    Jean Parpaillon <jean.parpaillon@irisa.fr>
#                    All rights reserved
# For license information, see the COPYING file in the top level
# directory of the source
###################################################################

import sys
import os
from lxml import etree
from StringIO import StringIO
from OpkgcConfig import *
from OpkgcTools import *
from OpkgcLogger import *

class XmlTools(object):
    xsd_uri = "http://www.w3.org/2001/XMLSchema"
    
    __instance = None
    __xml_doc = None
    __xmlschema_doc = None

    def __new__ (cls):
        if cls.__instance is None:
            cls.__instance = object.__new__(cls)
        return cls.__instance

    def init (self, xml_file):
        self.__xmlschema_doc = self.parseXml(Config().get("GENERAL", "xsdfile"))
        self.__xml_doc = self.parseXml(xml_file)

    def validate (self):
        """ Return false if config.xml is not valid
        """
        xmlschema = etree.XMLSchema(self.__xmlschema_doc)
        Logger().info("Validating XML file against schema")
        if not xmlschema.validate(self.__xml_doc):
            Logger().error("config.xml file is invalid. Check against XML schema %s " % Config().get("GENERAL", "xsdfile"))
            raise SystemExit

    def parseXml (self, file):
        xml_doc = None
        try:
            xml_file = open(file)
            parser_xml = etree.XMLParser()
            xml_doc = etree.parse(xml_file, parser_xml)
            xml_file.close()
            Logger().debug("%s loaded" % file)
        except Exception, e:
            Logger().error(e)
            raise SystemExit(1)

        return xml_doc

    def getXmlDoc(self):
        return self.__xml_doc

    def getXsdDoc(self):
        return self.__xmlschema_doc
