###################################################################
# Copyright (c) 2007 INRIA-IRISA,
#                    Jean Parpaillon <jean.parpaillon@inria.fr>
#                    All rights reserved
# Copyright (c) 2007 Oak Ridge National Laboratory
#                    Geoffroy Vallee <valleegr@ornl.gov>
#                    All rights reserved
# For license information, see the COPYING file in the top level
# directory of the source
###################################################################

import sys
import os
import re
import shutil
import exceptions
from Config import *
from Tools import *
from Logger import *
from Cheetah.Template import Template

from OpkgDescription import *
from PkgDescription import *
from Rpm import *
from Deb import *

__all__ = ['Compiler', 'CompilerRpm', 'CompilerDebian']

class Compiler:
    """ Generic class for compiling config.xml
    """
    config = None

    dest_dir = ''
    inputdir = ''
    dist = ''
    pkgName = None
    
    def __init__(self, inputdir, dest_dir, dist):
        self.dest_dir = dest_dir
        self.inputdir = inputdir
        self.dist = dist

    def cheetahCompile(self, orig, template, dest):
        """ Transform 'orig' to 'dest' with Cheetah template 'template'
        
        'template' is a XSLT file
        """
        try:
            Logger().info("Generates %s from template %s" % (dest, template))
            t = Template(file=template, searchList=[orig])
            f = open(dest, 'w')
            f.write(t.respond())
            f.close()
        except OpkgSyntaxException,e :
            Logger().error(e.msg)
            sys.exit(1)

    def compile (self, doBuild):
        """ Compile opkg
        doBuild: if True, generates packages, if False, only meta-files
        """
        opkgDesc = OpkgDescription(self.inputdir)
        outputDesc = self.getOutputDesc(opkgDesc)

        self.pkgName = opkgDesc.getPackageName()
        Logger().debug("Package name: %s" % self.pkgName)

        # Check if package is available on target dist
        if not opkgDesc.checkDist(self.dist):
            Logger().info("Package '%s' is not available on distribution '%s'" % (self.pkgName, self.dist))
            raise SystemExit

        self.pkgDir = self.getSourceDir()

        self.cleanSources()
        self.prepareBuildEnv()
        
        # Copy files from opkg dir to sources dir
        for f in outputDesc.getSourceFiles():
            fDest = os.path.join(self.pkgDir, f['sourcedest'])
            fDir = os.path.dirname(fDest)
            if (not os.path.exists(fDir)):
                os.makedirs(fDir)
            shutil.copy(f['path'], fDest)

        # Produce templated files
        self.createSources(outputDesc)

        if doBuild:
            self.build(outputDesc)

    def getOutputDesc(self, opkgDesc):
        """ Implemented by sub-classes
        """
        raise NotImplemented

    def cleanSources(self):
        """ Implemented in sub-classes
        """
        raise NotImplemented

    def prepareBuildEnv(self):
        """ Implemented in sub-classes
        """
        raise NotImplemented

    def getSourceDir(self):
        """ Implemented in sub-classes
        """
        raise NotImplemented        

    def prepareSources(self):
        """ Implemented in sub-classes
        """
        raise NotImplemented

    def createSources(self, outputDesc):
        """ Implemented in sub-classes
        """
        raise NotImplemented

    def build(self, outputDesc):
        """ Implemented in sub-classes
        """
        raise NotImplemented        

    def execBuild(self, command, cwd='./'):
        ret = Tools.command(command, cwd)
        if ret == 0:
            Logger().info("Packages succesfully generated")
        else:
            Logger().error("Package generation failed: return %d" % ret)

    def SupportedDist(cls):
        """ Return a list of supported dist
        """
        return cls.supportedDist
    SupportedDist = classmethod(SupportedDist)

    def SupportDist(cls, dist):
        """ Return true if the class support 'dist'
        """
        return dist in cls.supportedDist
    SupportDist = classmethod(SupportDist)
        
class CompilerRpm(Compiler):
    """ Extend Compiler for RPM packaging
    """
    configSection = "RPM"
    supportedDist = ['fc', 'rhel', 'mdv', 'suse', 'ydl']
    pkgDir = ''

    def getOutputDesc(self, opkgDesc):
        return RpmSpec(opkgDesc, self.dist)

    def cleanSources(self):
        if (os.path.exists(self.pkgDir)):
            Tools.rmDir(self.pkgDir)

        # Clean existing .spec file
        specfile = self.getSpecFile()
        if os.path.exists(os.path.dirname(specfile)):
            if os.path.exists(specfile):
                os.remove(specfile)

    def getSpecFile(self):
        specdir = self.getMacro('%_specdir')
        return os.path.join(specdir, "opkg-%s.spec" % self.pkgName)

    def prepareBuildEnv(self):
        os.makedirs(self.pkgDir)

        specdir = self.getMacro('%_specdir')
        if not os.path.exists(specdir):
            os.makedirs(specdir)

    def getSourceDir(self):
        return os.path.join(self.getMacro('%_builddir'), "opkg-%s" % self.pkgName)

    def createSources(self, rpmDesc):
        # Produce spec file
        self.cheetahCompile(
            rpmDesc,
            os.path.join(Config().get(self.configSection, "templatedir"), "opkg.spec.tmpl"),
            self.getSpecFile())

    def build(self, rpmDesc):
        cmd = "%s %s %s" % (Config().get(self.configSection, "buildcmd"),
                            Config().get(self.configSection, "buildopts"),
                            self.getSpecFile())
        ret = Tools.command(cmd, "./")
        if ret == 0:
            Logger().info("Packages succesfully generated in %s" % self.getMacro('%_rpmdir'))
        else:
            Logger().error("Package generation failed: return %d" % ret)

    def getMacro(self, name):
        line = os.popen("rpm --eval %s" % name).readline()
        return line.strip()

class CompilerDebian(Compiler):
    """ Extend Compiler for Debian packaging
    """
    configSection = "DEBIAN"
    supportedDist = ['debian']
    pkgDir = ''
    def getOutputDesc(self, opkgDesc):
        return DebDescription(opkgDesc, self.dist)

    def getSourceDir(self):
        return os.path.join(self.dest_dir, "opkg-%s" % self.pkgName)

    def cleanSources(self):
        sourceDir = self.getSourceDir()
        if os.path.exists(sourceDir):
            Tools.rmDir(sourceDir)

    def prepareBuildEnv(self):
        debiandir = os.path.join(self.getSourceDir(), 'debian')
        os.makedirs(debiandir)

    def createSources(self, debDesc):
        debiandir = os.path.join(self.getSourceDir(), 'debian')
        
        # Compile template files
        templateDir = Config().get(self.configSection, "templatedir")
        for template in Tools.listFiles(templateDir):
            if re.search("\.tmpl", template):
                (head, tail) = os.path.split(template)
                (base, ext) = os.path.splitext(tail)
                self.cheetahCompile(debDesc, template, os.path.join(debiandir, base))
            else:
                shutil.copy(template, debiandir)
                Logger().info("Copy %s to %s" % (template, debiandir))

        for part in ['api', 'server', 'client']:
            fl = debDesc.getPackageFiles(part)
            installFile = os.path.join(debiandir, debDesc.getInstallFile(part))
            filelist = open(installFile, "a")
            for f in fl:
                Logger().debug("File: %s" % f['path'])
                filelist.write("%s /%s\n" % (f['sourcedest'], f['dest']))
            filelist.close()        

    def build(self, debDesc):
        cmd = "%s %s" % (Config().get(self.configSection, "buildcmd"),
                         Config().get(self.configSection, "buildopts"))
        ret = Tools.command(cmd, self.getSourceDir())
        if ret == 0:
            Logger().info("Packages succesfully generated")
        else:
            Logger().error("Package generation failed: return %d" % ret)
