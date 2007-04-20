###################################################################
# Copyright (c) 2007 INRIA-IRISA,
#                    Jean Parpaillon <jean.parpaillon@irisa.fr>
#                    All rights reserved
# For license information, see the COPYING file in the top level
# directory of the source
###################################################################

from OpkgcLogger import *
import ConfigParser, os

__all__ = ['Config']

class Config(object):
    __instance = None

    __config = None

    def __new__ (cls):
        if cls.__instance is None:
            cls.__instance = object.__new__(cls)
            cls.__instance.readConfig()
        return cls.__instance

    def readConfig (self):
        self.__config = ConfigParser.ConfigParser()
        success = self.__config.read(['/etc/opkgc.conf', os.path.expanduser('~/.opkgc'), './opkgc.conf'])
        if len(success) == 0:
            Logger().error("No configuration file found (in /etc/opkgc.conf, ~/.opkgc or ./opkgc.conf)")
            raise SystemExit
        else:
            for c in success:
                Logger().info("Read config file %s" % c)
        
    def get (self, section, option):
        return self.__config.get(section, option)
