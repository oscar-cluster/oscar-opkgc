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

class XmlTools:
    __instance = None
    __xml_doc = None
    __xmlschema_doc = None

    filter_xslt_file = "/tmp/opkgc/param.xsl"

    def __new__ (cls):
        if cls.__instance is None:
            cls._instance = object.__new__(cls)
        return cls._instance
    
    def init (self, xml_file):
        self.__xml_doc = self.parseXml(xml_file)
        self.__xmlschema_doc = self.parseXml(Config().get("GENERAL", "xsdfile"))

    def transform (self, xsl_file, output_file, params):
        # Creating the params stylesheet
        self.genXSLTParam(params)
        
        # we parse then the XSLT file
        xsl_doc = self.parseXml(xsl_file)
        
        transform = etree.XSLT(xsl_doc)
        
        # We apply then the XSLT transformation to the XML doc
        result = transform(self.__xml_doc)
        
        # We open the output file
        output = open (output_file, "w")
        output.write(str(result))
        output.close()
        
        # Remove the params stylesheet
        self.delXSLTParam()
    
    def validate (self):
        """ Return false if config.xml is not valid
        """
        xmlschema = etree.XMLSchema(self.__xmlschema_doc)
        Logger().info("Validating XML file against schema")
        if not xmlschema.validate(self.__xml_doc):
            Logger().error("config.xml file is invalid. Check against XML schema %s " % Config().get("GENERAL", "xsdfile"))
            raise SystemExit

    def parseXml (self, file):
        Logger().debug("Load xml file %s" % file)
        xml_file = open(file)
        parser_xml = etree.XMLParser()
        xml_doc = etree.parse(xml_file, parser_xml)
        xml_file.close()
        return xml_doc

    def getXmlDoc(self):
        return self.__xml_doc

    def genXSLTParam(self, vars):
        """ Generate a XSLT stylesheet with
        <xsl:variable /> tags, from 'vars' dictionnary
        """
        try:
            self.delXSLTParam()

            os.makedirs(os.path.dirname(self.filter_xslt_file))
                        
            root = etree.Element("xsl:stylesheet")
            root.set("version", "1.0")
            root.set("xmlns:xsl", "http://www.w3.org/1999/XSL/Transform")
            
            output = etree.SubElement(root, "xsl:output")
            output.set("method", "text")
            output.set("encoding", "us-ascii")
            
            for key in vars.keys():
                v = etree.SubElement(root, "xsl:variable")
                v.set("name", key)
                v.text = vars[key]
                
            tree = etree.ElementTree(root)
            tree.write(self.filter_xslt_file, xml_declaration=True)
        except(Exception), e:
            print "Can not write params stylesheet('%s'): %s" % (self.filter_xslt_file, e)
            sys.exit(2)

    def delXSLTParam(self):
        Tools.rmDir(os.path.dirname(self.filter_xslt_file))
        
