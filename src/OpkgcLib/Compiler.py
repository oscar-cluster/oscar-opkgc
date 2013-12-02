###################################################################
# Copyright (c) 2007 Kerlabs
#                    Jean Parpaillon <jean.parpaillon@kerlabs.com>
#                    All rights reserved
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
import shutil, glob
import exceptions
import tempfile
from Config import *
from Tools import *
from Logger import *

from OpkgDescription import *
from PkgDescription import *
from Rpm import *
from Deb import *

class Compiler:
    """ main class for compiling for opgks
    """
    compilers = ['RPMCompiler', 'DebCompiler']
    
    config = None

    dest_dir = ''
    inputdir = ''
    dist = ''
    pkgName = None
    
    def __init__(self, inputdir, dest_dir, dist):
        self.dest_dir = dest_dir
        self.inputdir = inputdir
        self.dist = dist

    def compile (self, targets):
        """ Compile opkg
        targets: list of targets amongst: 'binary', 'source'
        """
        opkgDesc = OpkgDescription(self.inputdir)

        self.pkgName = opkgDesc.getPackageName()
        Logger().debug("Package name: %s" % self.pkgName)

        # Check if package is available on target dist
        if not opkgDesc.checkDist(self.dist):
            Logger().info("Package '%s' is not available on distribution '%s'" % (self.pkgName, self.dist))
            raise SystemExit

        tarfile = self.createTarball(opkgDesc)
        Logger().info("opkg tarball created: %s" % tarfile)

        for c in self.compilers:
            if self.dist in eval(c).supportedDist:
                dc = eval(c)(opkgDesc, self.dest_dir, self.dist)
                dc.run(tarfile, targets)
        
    def createTarball(self, opkgDesc):
        """ Create a tarball from opkg sources.
        Return: path to the tarball
        """
        tempdir = tempfile.mkdtemp('.opkgc')
        sourcedir = "opkg-%s-%s" % (self.pkgName, opkgDesc.getVersion('upstream'))
        tardir = os.path.join(tempdir, sourcedir)
        tarfile = "%s.tar.gz" % sourcedir
        tarname = os.path.join(opkgDesc.opkgdir, tarfile)
        filelist_filter = "SRPMS|distro|%s" % tarname
        
        os.mkdir(tardir, 0755)
        filelist = [ os.path.join(opkgDesc.opkgdir, f)
                     for f in Tools.ls(opkgDesc.opkgdir, exclude=filelist_filter) ]
        Tools.copy(filelist, tardir, exclude='\.svn|.*~$')

        if not Tools.tar(tarname, [sourcedir], tempdir):
            Logger().error("Error while creating tar file: %s" % tarname)
            raise SystemExit(1)
        Logger().debug("Delete temp dir: %s" % tempdir)
        Tools.rmDir(tempdir)
        
        return tarname

    def SupportDist(cls, dist):
        """ Return true if dist is supported 'dist'
        """
        for c in cls.compilers:
            if dist in eval(c).supportedDist:
                return True
        return False
    SupportDist = classmethod(SupportDist)

class RPMCompiler:
    """ RPM Compiler
    """
    opkgDesc = None
    opkgName = None
    dist = None
    dest_dir = None
    configSection = "RPM"
    supportedDist = ['fc', 'rhel', 'mdv', 'suse', 'ydl']
    buildCmd = "rpmbuild"

    def __init__(self, opkgDesc, dest_dir, dist):
        self.opkgDesc = opkgDesc
        self.opkgName = opkgDesc.getPackageName()
        self.dist = dist
        self.dest_dir = dest_dir

    def run(self, tarfile, targets):
        # Create SOURCES dir and copy opkg tarball to it
        sourcedir = self.getMacro('%{_sourcedir}')
        if not os.path.exists(sourcedir):
            os.makedirs(sourcedir)
        Logger().debug("Copying %s to %s" % (tarfile, sourcedir))
        shutil.copy(tarfile, sourcedir)

        # Create SPECS dir and create spec file
        specdir = self.getMacro('%_specdir')
        if not os.path.exists(specdir):
            os.makedirs(specdir)

        specfile = os.path.join(specdir, "opkg-%s.spec" % self.opkgName)
        if os.path.exists(specfile):
            os.remove(specfile)

        if self.opkgDesc.arch == "all":
            specfile = os.path.join(self.getMacro('%_specdir'), "opkg-%s.spec" % self.opkgName)
        else:
            specfile = os.path.join(self.getMacro('%_specdir'), "opkg-%s.spec.tmp" % self.opkgName)
            finalspec = os.path.join(self.getMacro('%_specdir'), "opkg-%s.spec" % self.opkgName)
        Tools.cheetahCompile(
            RpmSpec(self.opkgDesc, self.dist),
            os.path.join(Config().get(self.configSection, "templatedir"), "opkg.spec.tmpl"),
            specfile)

        # GV: I am not familiar enough with Cheetah to trick the spec file on
        # the fly so i do it here manually. The idea is to remove the BuildArch
        # line in the spec file when the package is not noarch
        Logger().debug ("Arch: %s" % self.opkgDesc.arch)
        if self.opkgDesc.arch == "any":
            Logger().debug ("Modifying the spec file for the creation of arch dependent RPMs")
            cmd = "/bin/sed s/BuildArch/\#BuildArch/g < " + specfile + " > " + finalspec
            Logger().info("Executing %s" % (cmd))
            os.system(cmd)
                    
            os.remove(specfile)
            specfile = finalspec
            cmd = "cp " + specfile + " /tmp"
            os.system(cmd)

        # Build targets
        if 'source' in targets:
            if Tools.command("%s --clean -bs %s" % (self.buildCmd, specfile), "./"):
                Logger().info("Source package succesfully generated in %s" % self.getMacro('%_srcrpmdir'))
            else:
                Logger().error("Source package generation failed")
                raise SystemExit(1)
            
        if 'binary' in targets:
            if Tools.command("%s --clean -bb %s" % (self.buildCmd, specfile), "./"):
                Logger().info("Moving generated files to %s" % self.dest_dir)
                for file in glob.glob(os.path.join(self.getMacro('%_rpmdir'), "*/opkg-%s*.rpm" % self.opkgName)):
                    dest_file = os.path.join(self.dest_dir, os.path.basename(file))
                    if os.path.exists(dest_file):
                        Logger().info("Removing existing file: %s" % dest_file)
                        os.unlink(dest_file)
                    Logger().info("Moving file: %s" % file)
                    shutil.move(file, self.dest_dir)
            else:
                Logger().error("Binary package generation failed")
                raise SystemExit(1)
            
    def getMacro(self, name):
        line = os.popen("rpm --eval %s" % name).readline()
        return line.strip()

class DebCompiler:
    """ Extend Compiler for Debian packaging
    """
    opkgDesc = None
    dest_dir = None
    opkgName = None
    configSection = "DEBIAN"
    buildCmd = "dpkg-buildpackage -uc -us"
    supportedDist = ['debian']

    def __init__(self, opkgDesc, dest_dir, dist):
        self.opkgDesc = opkgDesc
        self.dist = dist
        self.dest_dir = dest_dir
        self.opkgName = opkgDesc.getPackageName()

    def run(self, tarfile, targets):
        sourcedir = os.path.join(self.opkgDesc.opkgdir,
                                 "opkg-%s-%s" % (self.opkgName, self.opkgDesc.getVersion('upstream')))
        # Rename tar to follow Debian non-native package rule
        debtarfile = os.path.join(self.opkgDesc.opkgdir,
                                  "opkg-%s_%s.orig.tar.gz" % (self.opkgName, self.opkgDesc.getVersion('upstream')))
        os.rename(tarfile, debtarfile)
        
        # Uncompress tar
        if os.path.exists(sourcedir):
            Tools.rmDir(sourcedir)
        if not Tools.untar(debtarfile, self.opkgDesc.opkgdir):
            Logger().error("Error while extracting tar file: %s" % debtarfile)
            raise SystemExit(1)

        # Create debian dir
        debiandir = os.path.join(sourcedir, "debian")
        os.makedirs(debiandir)

        # Compile template files
        debDesc = DebDescription(self.opkgDesc, self.dist)
        templateDir = os.path.abspath(Config().get(self.configSection, "templatedir"))
        tmplList = [ os.path.join(templateDir, t)
                     for t in Tools.ls(templateDir) ]
        Logger().debug("Templates: %s" % tmplList)
        for template in tmplList:
            if re.search("\.tmpl", template):
                (head, tail) = os.path.split(template)
                (base, ext) = os.path.splitext(tail)
                Tools.cheetahCompile(debDesc, template, os.path.join(debiandir, base))
            else:
                shutil.copy(template, debiandir)
                Logger().info("Copy %s to %s" % (template, debiandir))

        # [2010/06/17] DEPRECATED!!! We do not need to update the debian/rules
        # script anymore!
        # Update the debian/rules file
        # GV: For the rules file, we need to do some simple updates and
        # I do not know cheetah enough to do that quickly... there we
        # execute a sed command (yes, it is far from perfect).
#        rulescript = debiandir + "/rules"
#        cmd = "/bin/sed s/OPKGNAME/" + self.opkgName + "/g < " + debiandir + "/rules.in > " + rulescript
#        Logger().info("Executing %s" % (cmd))
#        os.system(cmd)
#        os.chmod (rulescript, 0744)

        # Create the debian/rules script
        source = debiandir + "/rules.in"
        dest = debiandir + "/rules"
        shutil.copy(source, dest)
        os.chmod (dest, 0744)

        # Deal with the different post install scripts specific to each part 
        # of the OPKG
        fl = self.opkgDesc.getScripts()
        for f in fl:
            script_name = debDesc.getPkgScript(f)
            # OPKG script also include scripts that are not related to the 
            # binary package, so we just ignore those (they just need to be
            # included into the package at the good location).
            if (script_name != ""):
                pkgScript = os.path.join(debiandir, debDesc.getPkgScript(f))
                # Logger().debug ("--> File: "+f['basename']+" part of "+f['part'])
                Logger().debug("-> Creating %s" % pkgScript)
                filelist = open(pkgScript, "a")
                Logger().debug("--> Adding /"+f['dest'] + "/" + f['basename'])
                filelist.write("#!/bin/sh\n/%s/%s\n" % (f['dest'], f['basename']))
                filelist.close()

        # Copy the different scripts at the good location, i.e., in the good
        # directory so it will correctly be included in the appropriate pkg
        for part in ['api', 'server', 'client']:
            list = debDesc.getPackageFiles(part)
            for f in list:
                Logger().debug("*** Handling "+f['orig']+" (part:"+f['part']+")")
                if (part == "" or f['part'] == part):
                    orig = f['orig']
                    if not os.path.isdir (debiandir):
                        Logger().debug("Debian directory does not exist(%s)" % debiandir)
                        sys.exit (1)
                    if (part == "api"):
                        dest = debiandir+"/opkg-"+self.opkgName
                    else:
                        dest = debiandir+"/opkg-"+self.opkgName+"-"+f['part']
                    dest = dest+"/usr/lib/oscar/packages/"+self.opkgName
                    if not os.path.isfile(orig):
                        Logger().debug("File %s does not exist" % orig)
                    else:
                        try:
                            Logger().debug("Creating %s" % dest)
                            if not os.path.exists(dest):
                                os.makedirs (dest)
                        except:
                            Logger().debug("ERROR: impossible to create %s" % dest)
                            sys.exit (1)
                        Logger().debug("Copy "+orig+" to " + dest)
                        shutil.copy(orig, dest)

        # Since we modified the files from the orig package, we should recreate
        # the .orig.tar.gz file or just delete it. Right now, we just delete it
        os.remove (debtarfile)

        # Build targets
        cmd = "%s -rfakeroot -sa" % self.buildCmd
        if 'source' in targets and 'binary' in targets:
            opts = ""
        elif 'source' in targets:
            opts = "-S"
        elif 'binary' in targets:
            opts = "-B"

        if Tools.command("%s %s" % (cmd, opts), sourcedir):
            Logger().info("Packages succesfully generated")
        else:
            Logger().error("Packages generation failed")
            raise SystemExit(1)

        # Now, move the packages from self.opkgDesc.opkgdir/../*.deb to self.dest_dir
        for file in glob.glob(os.path.join(self.opkgDesc.opkgdir, "opkg-%s*.deb" % self.opkgName)):
            dest_file = os.path.join(self.dest_dir, os.path.basename(file))
            if os.path.exists(dest_file):
                 Logger().info("Removing existing file: %s" % dest_file)
                 os.unlink(dest_file)
            Logger().info("Moving file: %s" % file)
            shutil.move(file, self.dest_dir)
