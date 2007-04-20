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
from OpkgcXml import *
from OpkgcConfig import *
from OpkgDescription import *
from OpkgcTools import *
from OpkgcLogger import *
from Cheetah.Template import Template

__all__ = ['Compiler', 'CompilerRpm', 'CompilerDebian']

class Compiler:
    """ Generic class for compiling config.xml
    """
    config = None

    dest_dir = ''
    validate = True
    inputdir = ''
    dist = ''
    
    xml_tool = XmlTools()

    def __init__(self, inputdir, dest_dir, dist, validate):
        self.dest_dir = dest_dir
        self.validate = validate
        self.inputdir = inputdir
        self.dist = dist

    def getDestDir(self):
        return self.dest_dir

    def xmlInit(self, orig):
        self.xml_tool.init (orig)

    def xmlValidate(self):
        if self.validate:
            self.xml_tool.validate()

    def getXmlDoc(self):
        return self.xml_tool.getXmlDoc()

    def xmlCompile(self, template, dest, params):
        """ Transform 'orig' to 'dest' with XSLT template 'template'
        'template' is a XSLT file
        'params' is a dictionnary with params to give to the template
        """
        self.xml_tool.transform (template, dest, params)

    def cheetahCompile(self, orig, template, dest):
        """ Transform 'orig' to 'dest' with Cheetah template 'template'
        
        'template' is a XSLT file
        """
        Logger().info("Generates %s from template %s" % (dest, template))
        t = Template(file=template, searchList=[orig])
        f = open(dest, 'w')
        f.write(t.respond())
        f.close()

    def compile(self, build):
        """ Abstract method to generate packaging files
        """
        raise NotImplementedError

    def getPackageName(self):
        return self.xml_tool.getXmlDoc().find('/name').text.lower()

    def getConfigFile(self):
        """ Return path of config.xml file
        Raise exception if not found
        """
        path = os.path.join(self.inputdir, "config.xml")
        if os.path.exists(path):
            Logger().info("%s file found" % path)
            return path
        else:
            Logger().error("No config.xml file found. Either:")
            Logger().error("* specify the --input=dir option")
            Logger().error("* run opkgc from the opkg directory")
            raise SystemExit

    def getScripts(self):
        """ Return list of files in scripts/ dir
        """
        ret = []
        scriptdir = os.path.join(self.inputdir, "scripts")
        if os.path.isdir(scriptdir):
            for p in os.listdir(scriptdir):
                if not re.search("\.svn|.*~", p) and not os.path.isdir(p):
                    path = os.path.join(self.inputdir, "scripts", p)
                    ret.append(path)
        # add configurator.html, if any
        configurator = os.path.join(self.inputdir, "configurator.html")
        if os.path.exists(configurator):
            ret.append(configurator)
        return ret

    def build(self, command, cwd='./'):
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
    supportedDist = ['fc', 'rhel', 'mdv', 'suse']
    pkgDir = ''
    specfile = ''

    def compile (self, doBuild):
        """ Compile opkg
        doBuild: if True, generates packages, if False, only meta-files
        """
        self.xmlInit (self.getConfigFile())
        self.xmlValidate ()

        pkgName = Tools.normalizeWithDash(self.getPackageName())
        Logger().debug("Package name: %s" % pkgName)
        self.pkgDir = os.path.join(self.getMacro('%_builddir'), "opkg-%s" % pkgName)

        # Clean/Create package dir
        if (os.path.exists(self.pkgDir)):
            Tools.rmDir(self.pkgDir)
        os.makedirs(self.pkgDir)

        # Clean existing .spec file
        specdir = self.getMacro('%_specdir')
        self.specfile = os.path.join(specdir, "opkg-%s.spec" % pkgName)
        if (not os.path.exists(specdir)):
            os.makedirs(specdir)
        else:
            if (os.path.exists(self.specfile)):
                os.remove(self.specfile)

        # Create template env from config.xml
        desc = OpkgDescriptionRpm(self.xml_tool.getXmlDoc(), self.dist)

        filelist = []
        # Manage [pre|post]-scripts
        scriptdir = os.path.join("var", "lib", "oscar", "packages", "%s" % pkgName)
        if (not os.path.exists(os.path.join(self.pkgDir, scriptdir))):
            os.makedirs(os.path.join(self.pkgDir, scriptdir))
        for orig in self.getScripts():
            basename = os.path.basename(orig)
            if Tools.isNativeScript(basename):
                # If script is one of scripts included as
                # {pre|post}{inst|rm} scripts, include them into templating
                # env
                header = Tools.getRpmScriptName(basename)
                content = "%s\n" % header
                f = open(orig, 'r')
                if Tools.isBourneScript(f):
                    for line in f:
                        content = "%s%s" % (content, line)
                    content = "%s\n" % content
                    desc.setScript(header, content)
                else:
                    f.close()
                    print "Error: %s is not a bourne shell script, as required by RPM packaging policy " % orig
                    raise SystemExit                
                f.close()
            else:
                # else, file is packaged in /var/lib/oscar/packages/<packages>/
                filelist.append(os.path.join(scriptdir, basename))
                shutil.copy(orig, os.path.join(self.pkgDir, scriptdir))

        # Copy doc
        docdir = os.path.join(self.inputdir, "doc")
        outdocdir = os.path.join("usr", "share", "doc", "packages", "opkg-%s" % pkgName)
        if os.path.isdir(docdir):
            Tools.copy(docdir,
                       os.path.join(self.pkgDir, outdocdir),
                       True,
                       '\.svn|.*~')
            filelist.append(outdocdir)

        # Copy testing scripts
        testdir = os.path.join(self.inputdir, "testing")
        outtestdir = os.path.join("var", "lib", "oscar", "testing", "%s" % pkgName)
        if os.path.isdir(testdir):
            Tools.copy(testdir,
                       os.path.join(self.pkgDir, outtestdir),
                       True,
                       '\.svn|.*~')
            filelist.append(outtestdir)

        desc.setFileList(filelist)

        # Produce spec file
        self.cheetahCompile(
            desc,
            os.path.join(Config().get(self.configSection, "templatedir"), "opkg.spec.tmpl"),
            self.specfile)

        if doBuild:
            cmd = "%s %s %s" % (Config().get(self.configSection, "buildcmd"),
                                Config().get(self.configSection, "buildopts"),
                                self.specfile)
            self.build(cmd)

            # Copy generated packages into output dir
            pkgName = Tools.normalizeWithDash(self.getPackageName())
            rpmdir = os.path.join(self.getMacro('%_rpmdir'), "noarch")
            shutil.copy(os.path.join(rpmdir, "opkg-%s-%s.noarch.rpm" % (pkgName, desc.version())),
                        self.getDestDir())
            shutil.copy(os.path.join(rpmdir, "opkg-%s-server-%s.noarch.rpm" % (pkgName, desc.version())),
                        self.getDestDir())
            shutil.copy(os.path.join(rpmdir, "opkg-%s-client-%s.noarch.rpm" % (pkgName, desc.version())),
                        self.getDestDir())


    def getMacro(self, name):
        line = os.popen("rpm --eval %s" % name).readline()
        return line.strip()

class CompilerDebian(Compiler):
    """ Extend Compiler for Debian packaging
    """
    configSection = "DEBIAN"
    supportedDist = ['debian']
    pkgDir = ''
    scriptsOrigDest = {'api-pre-install'      : 'opkg-%s.preinst',
                       'api-post-install'     : 'opkg-%s.postinst',
                       'api-pre-uninstall'    : 'opkg-%s.prerm',
                       'api-post-uninstall'   : 'opkg-%s.postrm',
                       'server-pre-install'   : 'opkg-%s.preinst',
                       'server-post-install'  : 'opkg-%s.postinst',
                       'server-pre-uninstall' : 'opkg-%s.prerm',
                       'server-post-uninstall': 'opkg-%s.postrm',
                       'client-pre-install'   : 'opkg-%s.preinst',
                       'client-post-install'  : 'opkg-client-%s.postinst',
                       'client-pre-uninstall' : 'opkg-client-%s.prerm',
                       'client-post-uninstall': 'opkg-client-%s.postrm'}

    def compile (self, doBuild):
        """ Creates debian package files
        doBuild: if True, generate packages, if False only meta-files
        """
        self.xmlInit (self.getConfigFile())
        self.xmlValidate ()

        desc = OpkgDescriptionDebian(self.xml_tool.getXmlDoc(), self.dist)

        pkgName = Tools.normalizeWithDash(self.getPackageName())
        Logger().debug("Package base name: %s" % pkgName)
        self.pkgDir = os.path.join(self.getDestDir(), "opkg-%s" % pkgName)

        if (os.path.exists(self.pkgDir)):
            Tools.rmDir(self.pkgDir)

        debiandir = os.path.join(self.pkgDir, 'debian')
        os.makedirs(debiandir)

        # Compile template files
        for template in self.getTemplates():
            if re.search("\.tmpl", template):
                (head, tail) = os.path.split(template)
                (base, ext) = os.path.splitext(tail)
                self.cheetahCompile(desc, template, os.path.join(debiandir, base))
            else:
                shutil.copy(template, debiandir)
                Logger().info("Copy %s to %s" % (template, debiandir))

        # Manage [pre|post]-scripts
        for orig in self.getScripts():
            basename = os.path.basename(orig)
            if Tools.isNativeScript(basename):
                # If script is one of scripts included as
                # {pre|post}{inst|rm} scripts, copy with appropriate filename
                # (see Debian Policy for it)
                dest = Tools.getDebScriptName(basename, pkgName)
                shutil.copy(orig, os.path.join(debiandir, dest))
                Logger().info("Install script: %s" % dest)
            else:
                # else, file is packaged in /var/lib/oscar/packages/<packages>/
                filelist = open(os.path.join(debiandir, "opkg-%s.install" % pkgName), "a")
                filelist.write("%s /var/lib/oscar/packages/%s\n" % (basename, pkgName))
                filelist.close()
                shutil.copy(orig, self.pkgDir)
                Logger().info("Copy %s to %s" % (orig, self.pkgDir))

        # Copy doc
        docdir = os.path.join(self.inputdir, "doc")
        if os.path.isdir(docdir):
            Tools.copy(docdir,
                       self.pkgDir,
                       True,
                       '\.svn|.*~')
            filelist = open(os.path.join(debiandir, "opkg-%s.install" % pkgName), "a")
            filelist.write("doc/* /usr/share/doc/opkg-api-%s\n" % pkgName)
            filelist.close()

        # Copy testing scripts
        testdir = os.path.join(self.inputdir, "testing")
        if os.path.isdir(testdir):
            Tools.copy(testdir,
                       self.pkgDir,
                       True,
                       '\.svn|.*~')
            filelist = open(os.path.join(debiandir, "opkg-%s.install" % pkgName), "a")
            filelist.write("testing/* /var/lib/oscar/testing/%s\n" % pkgName)
            filelist.close()

        if doBuild:
            cmd = "%s %s" % (Config().get(self.configSection, "buildcmd"),
                             Config().get(self.configSection, "buildopts"))
            self.build(cmd, cwd=self.pkgDir)

    def getTemplates(self):
        """ Return list of files in Debian templates dir
        """
        ret = []
        for p in os.listdir(Config().get(self.configSection, "templatedir")):
            f = os.path.join(Config().get(self.configSection, "templatedir"), p)
            if not re.search("\.svn|.*~", p) and not os.path.isdir(f):
                ret.append(f)
        return ret
