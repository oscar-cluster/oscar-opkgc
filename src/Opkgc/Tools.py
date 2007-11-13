###################################################################
# Copyright (c) 2007 INRIA-IRISA,
#                    Jean Parpaillon <jean.parpaillon@inria.fr>
#                    All rights reserved
# For license information, see the COPYING file in the top level
# directory of the source
###################################################################

from UserDict import UserDict
from UserList import UserList
from Logger import *
from Cheetah.Template import Template
import shutil
import re
import os, sys, traceback
import subprocess

class Tools:
    scriptRe = re.compile(r'(?P<part>api|client|server)-(?P<time>pre|post)-(?P<action>un)?install')
    newlineRe = re.compile(r'\n')

    def ls(path, exclude=None):
        """ List files in path, excluding .svn, *~ and files
        described by exclude pattern, if any
        """
        ret = []
        if os.path.isdir(path):
            for p in os.listdir(path):
                if not (re.search("\.svn|.*~", p) or (exclude and re.search(exclude, p))):
                    ret.append(p)
        else:
            if os.path.exists(path):
                ret.append(path)

        return ret
    ls = staticmethod(ls)

    def rmNewline (text):
        """ Replace newlines with spaces
        """
        return Tools.newlineRe.sub(' ', text)
    rmNewline = staticmethod(rmNewline)
    
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
                    Logger().trace("Remove file: %s" % abspath)
            abspath = os.path.join(d)
            os.rmdir(abspath)
            Logger().trace("Remove dir: %s" % abspath)
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
                    Logger().debug("Create dir: %s" % abspath)
                    filelist = [os.path.join(orig, f) for f in os.listdir(orig)]
                    for f in filelist:
                        Tools.__copy(f,
                                     os.path.join(dest, os.path.basename(orig)),
                                     recursive,
                                     exclude)
            else:
                shutil.copy(orig, dest)
                Logger().debug("Copy %s to %s" % (orig, dest))
    __copy = staticmethod(__copy)

    def normalizeWithDash(s):
        """ Replace non-alphanumeric chars by '-' in s
        """
        p = re.compile(r'[^a-zA-Z0-9-]')
        return p.sub('-', s)
    normalizeWithDash = staticmethod(normalizeWithDash)

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
            line += " "
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

    def cheetahCompile(orig, template, dest):
        """ Transform 'orig' to 'dest' with Cheetah template 'template'
        
        'template' is a XSLT file
        """
        try:
            Logger().info("Generates %s from template %s" % (dest, template))
            t = Template(file=template, searchList=[orig])
            f = open(dest, 'w')
            f.write(t.respond())
            f.close()
        except Exception, e :
            Logger().error(e)
            traceback.print_exc()
            raise SystemExit(1)
    cheetahCompile = staticmethod(cheetahCompile)

    def tar(tarname, filelist, rootdir=os.path.dirname(sys.argv[0])):
        """ Create a .tar.gz with files from filelist
        """
        abs_tarname = os.path.abspath(tarname)
        files = ""
        for f in filelist:
            files += " %s" % f
        cmd = "tar zcf %s %s" % (abs_tarname, files)
        Logger().debug("Create tarball '%s' with '%s' into '%s'" % (abs_tarname, files, rootdir))
        Tools.command(cmd, rootdir)
    tar = staticmethod(tar)

    def untar(tarname, rootdir=os.path.dirname(sys.argv[0])):
        """ Untar tarname in rootdir
        """
        cmd = "tar zxf %s" % tarname
        Logger().debug("Untar '%s' into '%s'" % (tarname, rootdir))
        Tools.command(cmd, rootdir)
    untar = staticmethod(untar)

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
