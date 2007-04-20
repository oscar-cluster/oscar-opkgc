###################################################################
# Copyright (c) 2007 INRIA-IRISA,
#                    Jean Parpaillon <jean.parpaillon@irisa.fr>
#                    All rights reserved
# For license information, see the COPYING file in the top level
# directory of the source
###################################################################

import ConfigParser, os

__all__ = ['Logger']

class Logger(object):
    """ Logger for opkgc.
    """
    ERROR = 0
    INFO  = 1
    DEBUG = 2

    __instance = None
    __level = ERROR

    def __new__ (cls):
        if cls.__instance is None:
            cls.__instance = object.__new__(cls)
        return cls.__instance

    def level(self, lvl):
        """ Set verbosity level
        """
        self.__level = lvl

    def isError(self):
        return self.__level >= Logger.ERROR
        
    def error(self, msg):
        print "[ERROR] %s" % msg

    def isInfo(self):
        return self.__level >= Logger.INFO
        
    def info(self, msg):
        if self.__level >= Logger.INFO:
            print "[INFO] %s" % msg

    def isDebug(self):
        return self.__level >= Logger.DEBUG
        
    def debug(self, msg):
        if self.__level >= Logger.DEBUG:
            print "[DEBUG] %s" % msg
