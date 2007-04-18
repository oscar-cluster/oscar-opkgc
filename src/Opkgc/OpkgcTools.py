###################################################################
# Copyright (c) 2007 INRIA-IRISA,
#                    Jean Parpaillon <jean.parpaillon@inria.fr>
#                    All rights reserved
# For license information, see the COPYING file in the top level
# directory of the source
###################################################################

import shutil
import re
import os

__all__ = ['Tools']

class Tools:
    def rmDir (d):
        """ Remove recursively a directory, even if not empty, like rm -r
        """
        if os.path.exists(d):
            for p in os.listdir(d):
                if os.path.isdir(os.path.join(d,p)):
                    Tools.rmDir(os.path.join(d,p))
                else:
                    os.remove(os.path.join(d,p))
            os.rmdir(os.path.join(d))
    rmDir = staticmethod(rmDir)

    def copy(orig, dest, recursive=True, exclude=''):
        """ copy orig to dest, with recursive and exclude options
        orig: string or list
        desst: string
        recursive: boolean
        exclude: pattern
        """
        if type(orig) == str:
            Tools.__copy(orig, dest, recursive, exclude)
        elif type(orig) == list:
            for path in orig:
                Tools.__copy(path, dest, recursive, exclude)
    copy = staticmethod(copy)

    def __copy(orig, dest, recursive, exclude):
        """ copy orig to dest, with recursive and exclude option
        orig is a string
        """ 
        if not re.search(exclude, orig):
            if os.path.isdir(orig):
                if recursive:
                    os.makedirs(os.path.join(dest, os.path.basename(orig)))
                    filelist = [os.path.join(orig, f) for f in os.listdir(orig)]
                    for f in filelist:
                        Tools.__copy(f,
                                     os.path.join(dest, os.path.basename(orig)),
                                     recursive,
                                     exclude)
            else:
                shutil.copy(orig, dest)
    __copy = staticmethod(__copy)

    def normalizeWithDash(s):
        """ Replace non-alphanumeric chars by '-' in s
        """
        p = re.compile(r'[^a-zA-Z0-9-]')
        return p.sub('-', s)
    normalizeWithDash = staticmethod(normalizeWithDash)
