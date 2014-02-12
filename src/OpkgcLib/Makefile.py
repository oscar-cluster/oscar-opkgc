# -*- coding:utf-8 -*-
###################################################################
# Copyright (c) 2014 CEA Commissariat à l'Énergie Atomique et aux
#                    Énergie Alternatives.
#                    Olivier Lahaye <olivier.lahaye@cea.fr>
#                    All rights reserved
# For license information, see the COPYING file in the top level
# directory of the source
###################################################################

import copy
from PkgDescription import *
from OpkgDescription import *

class MakeDesc(PkgDescription):
    """ Describe Makefile
    """

    def filelist(self, part=None):
        filelist = self.opkgDesc.getSourceFiles()
        if part:
            return [ f for f in filelist if f['part'] == part ]
        else:
            return filelist

    def getSourceFiles(self):
        return [MakefileSourceFile(f) for f in self.opkgDesc.getSourceFiles()]

class MakefileSourceFile(UserDict):

    def __init__(self, opkgfile):
        UserDict.__init__(self, opkgfile)
        self['sourcedest'] = opkgfile['dest']
