###################################################################
# Copyright (c) 2007 INRIA-IRISA,
#                    Jean Parpaillon <jean.parpaillon@irisa.fr>
#                    All rights reserved
# For license information, see the COPYING file in the top level
# directory of the source
###################################################################

import ConfigParser, os

__all__ = ['Config']

class Config:
    __instance = None

    config = None
    configFile = ["./opkgc.conf", "~/.opkgc", "/etc/opkgc.conf"]

    def __new__ (cls):
        if cls.__instance is None:
            cls._instance = object.__new__(cls)
        return cls._instance

    def __init__(self):
        self.config = ConfigParser.ConfigParser()
        success = self.config.read(['/etc/opkgc.conf', os.path.expanduser('~/.opkgc'), './opkgc.conf'])
        if len(success) == 0:
            print "No configuration file found (in /etc/opkgc.conf, ~/.opkgc or ./opkgc.conf)"
            raise SystemExit
        
    def get (self, section, option):
        return self.config.get(section, option)
