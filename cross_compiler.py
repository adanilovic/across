#!/usr/bin/env python3

#Standard import statements
import sys
import os
import errno
import subprocess
import argparse
from ftplib import FTP
import pathlib
from urllib.parse import urlparse

#Custom import statements

class Dir:
    def __init__(self, abspath, components):
        assert isinstance(components, list)
        self.abspath = abspath
        self.components = components
        print('Dir')
        print('\tabspath:\t',  self.abspath)
        print('\tcomponents:\t', self.components)

        """Create all directories if they don't already exist"""
        for comp in components:
            pathlib.Path(os.path.join(self.abspath, comp)).mkdir(parents=True, exist_ok=True)

class BuildDir(Dir):
    def __init__(self, basedir, components):
        super(BuildDir, self).__init__(os.path.join(basedir, 'build'), components)

class SrcDir(Dir):
    def __init__(self, basedir, components):
        super(SrcDir, self).__init__(os.path.join(basedir, 'src'), components)

class URL():

    def __init__(self, url):
        self.url = urlparse(url)

    def print_url(self):
        print('URL')
        print('\turl.scheme:\t',   self.url.scheme)
        print('\turl.netloc:\t',   self.url.netloc)
        print('\turl.path:\t',     self.url.path)
        print('\turl.params:\t',   self.url.params)
        print('\turl.query:\t',    self.url.query)
        print('\turl.fragment:\t', self.url.fragment)

    def get_url(self):
        return self.url.path

class FTPSite(FTP):

    def __init__(self, sitename, dirname, filename):
        self.sitename = sitename
        self.dirname  = dirname
        self.filename = filename

        self.ftpfilename = self.dirname + self.filename

        self.url = URL(sitename + dirname + filename)
        print('FTPSite')
        print('\tsitename:\t', self.sitename)
        print('\tdirname:\t',  self.dirname)
        print('\tfilename:\t', self.filename)


        print('\tftpfilename:\t', self.ftpfilename)

        self.url.print_url()

    def get_local_dir_from_ftp_dir(self):
        return os.path.join(self.dirname.lstrip(os.path.sep))

    def download(self, basedir):

        self.localdirname = os.path.join(basedir, self.get_local_dir_from_ftp_dir())
        self.localfilename = self.localdirname + self.filename

        if not os.path.exists(self.localfilename):
            print('Downloading \'', self.url.get_url(), '\' to \'', self.localdirname,
                  '\', please wait...', sep='')
            with open(self.localfilename, 'wb') as f:
                def callback(data):
                    f.write(data)

                FTP.__init__(self, self.sitename)
                self.login()
                FTP.retrbinary(self, cmd='RETR {}'.format(self.ftpfilename), callback=callback)
                self.quit

    def unzip(self):
        print('Unzipping \'', self.localfilename,'\', please wait...', sep='')
        subprocess.check_call(['tar',
                               '-xf',
                               self.localfilename,
                               '-C',
                               self.localdirname])

class GNU(FTPSite):

    def __init__(self, subdir, filename):
        super(GNU, self).__init__(sitename='ftp.gnu.org',
                                  dirname='/gnu' + subdir,
                                  filename=filename)

    def dir_callback(self, dir_listing):
        self.versions.append(dir_listing)

    def build(self):
        self.builddir   = os.path.join(self.localdirname, 'build')
        self.installdir = os.path.join(self.localdirname, 'install')

        if not os.path.exists(self.builddir):
                os.makedirs(self.builddir)

        if not os.path.exists(self.installdir):
                os.makedirs(self.installdir)

        saved_path = os.getcwd()
        os.chdir(self.builddir)
        try:
            command = os.path.join('..', self.dirname, 'configure')
            subprocess.check_call([command,
                                   '--target=arm-elf',
                                   '--prefix=' + self.installdir,
                                   self.configureargs])
            subprocess.check_call(['make'])
            subprocess.check_call(['make' , 'install'])
        finally:
            os.chdir(saved_path)

class GCC(GNU):

    #configure: error: Building GCC requires GMP 4.2+, MPFR 2.4.0+ and MPC 0.8.0+.
    #./contrib/download_prerequisites

    def __init__(self):
        super(GCC, self).__init__(subdir='/gcc/gcc-7.3.0',
                                  filename='/gcc-7.3.0.tar.gz')
        configureargs = '--enable-languages=c,c++'

class BinUtils(GNU):

    #ftpdirname = GNU.ftpdirname + '/binutils'
    #dirname = 'binutils-2.30'
    #filename = '/binutils-2.30.tar.gz'
    #configureargs = ''

    def __init__(self):
        super(BinUtils, self).__init__(subdir='/binutils',
                                       filename='/binutils-2.30.tar.gz')

class CrossCompiler():

    def __init__(self, name,
                       supported_platforms,
                       dependencies,
                       basedir):
        self.name = name
        self.__supported_platforms = supported_platforms
        self.__dependencies = dependencies
        self.basedir = basedir

        self.components = [GCC(), BinUtils()]
        self.bdir = BuildDir(self.basedir, [path.get_local_dir_from_ftp_dir() for path in self.components])

    def download(self):
        for component in self.components:
            component.download(self.bdir.abspath)

    def unzip(self):
        for component in self.components:
            component.unzip()

    def build(self):
        #self.binutils.build()
        self.gcc.build()

def main():
    print("hello cross compiler world")
    #arm_cc.download()
    #arm_cc.build()
    scomp = []
    sdir = SrcDir(os.path.abspath(os.getcwd()), scomp)

    arm_cc = CrossCompiler('GCC',
                          ['linux'],
                          ['build-essential'],
                          os.path.abspath(os.getcwd()))

    arm_cc.download()
    arm_cc.unzip()

if __name__ == '__main__':
    main()
