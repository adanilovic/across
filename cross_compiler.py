#!/usr/bin/env python3

#Standard import statements
import sys
import os
import errno
import subprocess
import argparse
from ftplib import FTP

#Custom import statements

class GNU(FTP):

    sitename = 'ftp.gnu.org'
    ftpdirname = '/gnu'

    def __init__(self):
        self.versions = []

    def dir_callback(self, dir_listing):
        self.versions.append(dir_listing)

    def find_latest_version(self):
        print('find_latest_version')
        FTP.__init__(self, self.sitename)
        self.login()
        self.cwd(self.ftpdirname)
        self.dir(self.dir_callback)
        self.quit
        print('AD - num versions = ', len(self.versions))
        #TODO: Find latest version

    def download(self):
        self.localdirname = os.path.abspath(self.ftpdirname.lstrip(os.path.sep))
        self.filename = self.localdirname + self.filename

        if not os.path.exists(os.path.dirname(self.filename)):
                os.makedirs(os.path.dirname(self.filename))
        if not os.path.exists(self.filename):
            with open(self.filename, 'wb') as f:
                FTP.__init__(self, self.sitename)
                self.login()
                FTP.retrbinary(self, cmd='RETR {}'.format(self.filename), callback=f.write(data))
                self.quit

            subprocess.check_call(['tar',
                                   '-xvf',
                                   self.filename,
                                   '-C',
                                   os.path.dirname(self.filename)])

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

    ftpdirname = GNU.ftpdirname + '/gcc'
    dirname = 'gcc-7.3.0/gcc-7.3.0'
    filename = '/gcc-7.3.0/gcc-7.3.0.tar.gz'
    configureargs = '--enable-languages=c,c++'

    def __init__(self):
        super(GCC, self).__init__()
        latest_version = self.find_latest_version()

class BinUtils(GNU):

    ftpdirname = GNU.ftpdirname + '/binutils'
    dirname = 'binutils-2.30'
    filename = '/binutils-2.30.tar.gz'
    configureargs = ''

    def __init__(self):
        super(BinUtils, self).__init__()
        latest_version = self.find_latest_version()

class CrossCompiler():

    def __init__(self, name,
                       supported_platforms,
                       dependencies):
        self.name = name
        self.__supported_platforms = supported_platforms
        self.__dependencies = dependencies

        self.binutils = BinUtils()
        self.gcc = GCC()

    def download(self):
        self.binutils.download()
        self.gcc.download()

    def build(self):
        #self.binutils.build()
        self.gcc.build()

arm_cc = CrossCompiler('GCC',
                      ['linux'],
                      ['build-essential'])

def main():
    print("hello cross compiler world")
    arm_cc.download()
    arm_cc.build()

if __name__ == '__main__':
    main()
