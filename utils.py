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
import unittest

class Shell():
    def execute_shell_command(*args):
        logging.info(__file__, "About to execute:", args, 'from:', os.getcwd())

        ret = subprocess.call(args)

        if ret != 0:
            logging.info_fail_banner(args)
        else:
            logging.info_success_banner(args)

class Dir():
    def __init__(self, abspath, components):
        assert isinstance(components, list)
        self.abspath = abspath
        self.components = components
        logging.info('Dir')
        logging.info('\tabspath: %s\t',  self.abspath)
        logging.info('\tcomponents: %s\t', self.components)

        """Create all directories if they don't already exist"""
        for comp in components:
            pathlib.Path(os.path.join(self.abspath, comp)).mkdir(parents=True, exist_ok=True)

class DirTestMethods(unittest.TestCase):
    def test_init(self):
        dir = Dir('.', ['comp1', 'comp2'])

class BuildDir(Dir):

    build_dir = 'build'

    def __init__(self, basedir, components):
        assert isinstance(components, list)
        super(BuildDir, self).__init__(os.path.join(basedir, self.build_dir), components)

class BuildDirTestMethods(unittest.TestCase):
    def test_init(self):
        dir = BuildDir('.', ['comp1', 'comp2'])

class SrcDir(Dir):
    def __init__(self, basedir, components):
        super(SrcDir, self).__init__(os.path.join(basedir, 'src'), components)

class SrcDirTestMethods(unittest.TestCase):
    def test_init(self):
        dir = SrcDir('.', ['comp1', 'comp2'])

class URL():

    def __init__(self, url):
        self.url = urlparse(url)

    def print_url(self):
        logging.info('URL')
        logging.info('\turl.scheme: %s\t',   self.url.scheme)
        logging.info('\turl.netloc: %s\t',   self.url.netloc)
        logging.info('\turl.path: %s\t',     self.url.path)
        logging.info('\turl.params: %s\t',   self.url.params)
        logging.info('\turl.query: %s\t',    self.url.query)
        logging.info('\turl.fragment: %s\t', self.url.fragment)

    def get_url(self):
        return self.url.path

class URLTestMethods(unittest.TestCase):
    def test_init(self):
        url = URL('.')
    def test_print_url(self):
        url = URL('.')
        url.print_url()

if __name__ == '__main__':
    logging.basicConfig(filename=os.path.join(os.getcwd(), 'utils.py.log'),
                    filemode='w',
                    level=logging.DEBUG,
                    format='%(asctime)s - %(name)s - %(filename)s:%(lineno)s - %(funcName)s - %(levelname)s - %(message)s',
                    datefmt='%m/%d/%Y %I:%M:%S %p')
    unittest.main()
