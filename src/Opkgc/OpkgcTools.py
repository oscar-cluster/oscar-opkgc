###################################################################
# Copyright (c) 2007 INRIA-IRISA,
#                    Jean Parpaillon <jean.parpaillon@inria.fr>
#                    All rights reserved
# For license information, see the COPYING file in the top level
# directory of the source
###################################################################

from UserDict import UserDict
from UserList import UserList
from OpkgcLogger import *
import shutil
import re
import os
import subprocess

class Tools:
    scriptRe = re.compile(r'(?P<part>api|client|server)-(?P<time>pre|post)-(?P<action>un)?install')
    
    def rmDir (d):
        """ Remove recursively a directory, even if not empty, like rm -r
        """
        if os.path.exists(d):
            for p in os.listdir(d):
                if os.path.isdir(os.path.join(d,p)):
                    Tools.rmDir(os.path.join(d,p))
                else:
                    abspath = os.path.join(d,p)
                    os.remove(abspath)
                    Logger().debug("Remove file: %s" % abspath)
            abspath = os.path.join(d)
            os.rmdir(abspath)
            Logger().debug("Remove dir: %s" % abspath)
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
                    abspath = os.path.join(dest, os.path.basename(orig))
                    os.makedirs(abspath)
                    Logger().info("Create dir: %s" % abspath)
                    filelist = [os.path.join(orig, f) for f in os.listdir(orig)]
                    for f in filelist:
                        Tools.__copy(f,
                                     os.path.join(dest, os.path.basename(orig)),
                                     recursive,
                                     exclude)
            else:
                shutil.copy(orig, dest)
                Logger().info("Copy %s to %s" % (orig, dest))
    __copy = staticmethod(__copy)

    def normalizeWithDash(s):
        """ Replace non-alphanumeric chars by '-' in s
        """
        p = re.compile(r'[^a-zA-Z0-9-]')
        return p.sub('-', s)
    normalizeWithDash = staticmethod(normalizeWithDash)

    def isNativeScript(name):
        """ True if script is one of scripts included as
        {pre|post}{inst|rm} scripts
        name: basename of the script
        """
        return Tools.scriptRe.match(name)
    isNativeScript = staticmethod(isNativeScript)

    def getRpmScriptName(name):
        """ Convert opkg script name to RPM script name:
        api-post-uninstall -> %postun
        server-pre-install -> %pre server
        """
        m = Tools.scriptRe.match(name)
        res = "%%%s" % m.group('time')
        if m.group('action'):
            res = "%s%s" % (res, m.group('action'))
        if not m.group('part') == "api":
            res = "%s %s" % (res, m.group('part'))
        return res
    getRpmScriptName = staticmethod(getRpmScriptName)

    def getDebScriptName(name, pkgName):
        """ Convert opkg script name to Debian script name:
        api-post-uninstall -> opkg-<pkgName>.postinst
        server-pre-install -> opkg-<pkgName>-server.preinst
        """
        m = Tools.scriptRe.match(name)
        res = "opkg-%s" % pkgName
        if m.group('part') != "api":
            res = "%s-%s" % (res, m.group('part'))
        res = "%s.%s" % (res, m.group('time'))
        if m.group('action') == "un":
            res = "%srm" % res
        else:
            res = "%sinst" % res
        return res
    getDebScriptName = staticmethod(getDebScriptName)

    def isBourneScript(file):
        """ True if 'file' is a Bourne Shell script
        """
        file.seek(0)
        shebang = file.readline()
        return re.match(r'^#!.*/sh', shebang)
    isBourneScript = staticmethod(isBourneScript)

    def command(command, cwd):
        Logger().debug("Execute: %s" % command)
        exe = subprocess.Popen(command,
                               cwd=cwd,
                               bufsize=0,
                               stdin=None,
                               stdout=subprocess.PIPE,
                               stderr=subprocess.PIPE,
                               shell=True)
        if Logger().isDebug():
            for l in exe.stdout:
                Logger().debug(l.strip())
        for l in exe.stderr:
            Logger().info(l.strip())
        return exe.wait()
    command = staticmethod(command)

    def add_word(line, word, width):
        """ Add a word at the end of a line. 
        Return a duet (complete_lines, uncomplete_line)
        """
        complete = ''
        uncomplete = ''
        if (len(line) + len(word) + 1) > width:
            complete = "%s\n" % line
            if len(word) > width:
                complete += "%s-\n" % word[:width]
                uncomplete = word[width:]
            else:
                uncomplete = word
        else:
            uncomplete += "%s %s" % (line, word)
        return (complete, uncomplete)
    add_word = staticmethod(add_word)

    def align_lines(s, width):
        """ Cut a line in lines of 'width' columns, with no word
        truncating, except for words greater than 'width'
        """
        out = ""
        cur_line = ''
        cur_word = ''
        for c in s:
            if c == ' ':
                (newline, cur_line) = Tools.add_word(cur_line, cur_word, width)
                if newline != '':
                    out += newline
                cur_word = ''
            else:
                cur_word += c
        (newline, cur_line) = Tools.add_word(cur_line, cur_word, width)
        if newline != '':
            out += newline
        if cur_line != '':
            out += cur_line

        return out
    align_lines = staticmethod(align_lines)

    def align_paragraphs(s, width):
        """Return a list of paragraphs of 'width' cols, with
        no word truncated.
        Paragraphs in original string are marked with empty lines
        """
        paragraphs = []
        cur_par = ''
        s = s.strip()
        for line in s.split('\n'):
            line = line.strip()
            if line == '':
                if cur_par != '':
                    paragraphs.append(Tools.align_lines(cur_par, width))
                cur_par = ''
            else:
                cur_par += line
        if cur_par != '':
            paragraphs.append(Tools.align_lines(cur_par, width))

        return paragraphs
    align_paragraphs = staticmethod(align_paragraphs)

class NoneDict(UserDict):
    """ UserDict which returns None on __getitem__ with
    invalid key
    """
    def __init__(self, initdict=None):
        UserDict.__init__(self, initdict)

    def __getitem__(self, key):
        try:
            return UserDict.__getitem__(self, key)
        except KeyError, e:
            return None

class NoneList(UserList):
    """ UserList which contains 'None'
    """
    def __init__(self, initlist=None):
        UserList.__init__(self, initlist)

    def __contains__(self, item):
        if item == None:
            return True
        else:
            return UserList.__contains__(self, item)

class KeyDict(UserDict):
    """ UserDict which return the key if no value is found
    """
    def __init__(self, initdict=None):
        UserDict.__init__(self, initdict)

    def __getitem__(self, key):
        try:
            return UserDict.__getitem__(self, key)
        except KeyError, e:
            return key
