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
import argparse
import logging

#Custom import statements
from utils import *

# class Logger(Object):
    # def __init__(self, filepath='.', filename='log'):
        # self.filepath = filepath
        # self.filename = filename

    # def log(self, logdata):
        # with open(os.path.join(filepath, filename), 'a') as logfile:
            # logfile.write(logdata)

class FTPSite(FTP):

    def __init__(self, sitename, dirname, filename, extension):
        self.sitename = sitename
        self.dirname  = dirname
        self.filename = filename + extension
        self.extension = extension

        self.ftpfilename = self.dirname + self.filename

        self.url = URL(sitename + dirname + filename)
        logging.info('FTPSite')
        logging.info('\tsitename: %s\t', self.sitename)
        logging.info('\tdirname: %s\t',  self.dirname)
        logging.info('\tfilename: %s\t', self.filename)


        logging.info('\tftpfilename: %s\t', self.ftpfilename)

        self.url.print_url()

    def get_local_dir_from_ftp_dir(self):
        return os.path.join(self.dirname.lstrip(os.path.sep))

    def download(self, basedir):

        self.localdirname = os.path.join(basedir, self.get_local_dir_from_ftp_dir())
        self.localfilename = self.localdirname + self.filename

        if not os.path.exists(self.localfilename):
            logging.info('Downloading \'%s\' to \'%s\', please wait...',
                    self.url.get_url(), self.localdirname)
            with open(self.localfilename, 'wb') as f:
                def callback(data):
                    f.write(data)

                FTP.__init__(self, self.sitename)
                self.login()
                FTP.retrbinary(self, cmd='RETR {}'.format(self.ftpfilename), callback=callback)
                self.quit

    def unzip(self):
        logging.info('Unzipping \'', self.localfilename,'\', please wait...', sep='')
        subprocess.check_call(['tar',
                               '--skip-old-files',
                               '-xf',
                               self.localfilename,
                               '-C',
                               self.localdirname])

        logging.info('localdirname = %s', self.localdirname)
        logging.info('filename = %s', self.filename)
        logging.info('unzipdirname = %s', self.filename.lstrip(os.path.sep).replace(self.extension, ''))
        self.unzipdirname = os.path.join(self.localdirname,
                                         self.filename.lstrip(os.path.sep).replace(self.extension, ''))

class GNU(FTPSite):

    def __init__(self, subdir, filename, extension, configureargs=''):
        super(GNU, self).__init__(sitename='ftp.gnu.org',
                                  dirname='/gnu' + subdir,
                                  filename=filename,
                                  extension=extension)
        self.configureargs = configureargs

    def dir_callback(self, dir_listing):
        self.versions.append(dir_listing)

    def configure(self):
        logging.info('Configuring \'', self.localfilename,'\', please wait...', sep='')

        self.localbuilddir = os.path.join(self.localdirname, 'build')
        self.localinstalldir = os.path.join(self.localdirname, 'install')

        pathlib.Path(self.localbuilddir).mkdir(parents=True, exist_ok=True)

        saved_path = os.getcwd()
        os.chdir(self.localbuilddir)
        try:
            command = os.path.join(self.unzipdirname, 'configure')
            subprocess.check_call([command,
                                   '--target=arm-none-eabi',
                                   '--prefix=' + self.localinstalldir,
                                   self.configureargs])
        finally:
            os.chdir(saved_path)

    def make(self):

        self.localbuilddir = os.path.join(self.localdirname, 'build')

        pathlib.Path(self.localbuilddir).mkdir(parents=True, exist_ok=True)

        saved_path = os.getcwd()
        os.chdir(self.localbuilddir)
        try:
            subprocess.check_call(['make'])
            subprocess.check_call(['make' , 'install'])
        finally:
            os.chdir(saved_path)

class GCC(GNU):

    #configure: error: Building GCC requires GMP 4.2+, MPFR 2.4.0+ and MPC 0.8.0+.
    #./contrib/download_prerequisites

    def __init__(self):
        super(GCC, self).__init__(subdir='/gcc/gcc-7.3.0',
                                  filename='/gcc-7.3.0',
                                  extension='.tar.gz',
                                  configureargs='--enable-languages=c,c++')

    def configure(self):

        saved_path = os.getcwd()
        os.chdir(self.unzipdirname)
        try:
            subprocess.check_call([os.path.join('contrib', 'download_prerequisites')])
        finally:
            os.chdir(saved_path)

        super(GCC, self).configure()

class BinUtils(GNU):

    #ftpdirname = GNU.ftpdirname + '/binutils'
    #dirname = 'binutils-2.30'
    #filename = '/binutils-2.30.tar.gz'
    #configureargs = ''

    def __init__(self):
        super(BinUtils, self).__init__(subdir='/binutils',
                                       filename='/binutils-2.30',
                                       extension='.tar.gz')

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
        for component in self.components:
            component.configure()
            component.make()

def main():

    logfiledir = os.path.join(os.getcwd(), BuildDir.build_dir)
    """Create all directories if they don't already exist"""
    pathlib.Path(logfiledir).mkdir(parents=True, exist_ok=True)

    file_handler = logging.FileHandler(filename=os.path.join(logfiledir, 'build.log'), mode='w')
    stdout_handler = logging.StreamHandler(sys.stdout)
    handlers = [file_handler, stdout_handler]

    logging.basicConfig(level=logging.DEBUG,
                format='%(asctime)s - %(name)s - %(filename)s:%(lineno)s - %(funcName)s - %(levelname)s - %(message)s',
                datefmt='%m/%d/%Y %I:%M:%S %p',
                handlers=handlers)

    #scomp = []
    #sdir = SrcDir(os.path.abspath(os.getcwd()), scomp)

    arm_cc = CrossCompiler('GCC',
                          ['linux'],
                          ['build-essential'],
                          os.path.abspath(os.getcwd()))

    arm_cc.download()
    arm_cc.unzip()
    arm_cc.build()
    sys.exit(0)

if __name__ == '__main__':
    main()
