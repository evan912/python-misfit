#!/usr/bin/env python
"""Misfit client

Usage:
  misfit authenticate --client_id=<client_id> --client_secret=<client_secret> [--config=<config_file>]
  misfit profile [--config=<config_file>] [--user_id=<user_id>] [--object_id=<object_id>]
  misfit device [--config=<config_file>] [--user_id=<user_id>] [--object_id=<object_id>]
  misfit goal --start_date=<start_date> --end_date=<end_date> [--config=<config_file>] [--user_id=<user_id>] [--object_id=<object_id>]
  misfit summary --start_date=<start_date> --end_date=<end_date> [--detail] [--config=<config_file>] [--user_id=<user_id>]
  misfit session --start_date=<start_date> --end_date=<end_date> [--config=<config_file>] [--user_id=<user_id>] [--object_id=<object_id>]
  misfit sleep --start_date=<start_date> --end_date=<end_date> [--config=<config_file>] [--user_id=<user_id>] [--object_id=<object_id>]
  misfit --version

Options:
  -h --help                        Show this screen.
  --version                        Show version.
  --client_id=<client_id>          App key of your Misfit app.
  --client_secret=<client_secret>  App secret of your Misfit app.
  --config=<config_file>           Use the config file specified [default: ./misfit.cfg]
  --user_id=<user_id>              Misfit User ID.
  --object_id=<object_id>          ID of a single Misfit object.
  --start_date=<start_date         Date at the start of a range: Eg. 2014-11-20.
  --end_date=<end_date>            Date at the end of a range: Eg. 2014-11-30.
  --detail                         If specified, print summary detail for each day.

"""
from __future__ import absolute_import

import cherrypy

from docopt import docopt

from . import __version__
from .auth import AuthServer
from .misfit import Misfit

try:
    import configparser
except ImportError:  # Python 2.x fallback
    import ConfigParser as configparser


class MisfitCli:
    def __init__(self, arguments):
        """
        Runs the command specified as an argument with options specified
        """

        self.config_file = arguments['--config']
        self.config = configparser.ConfigParser()
        self.client_id = None
        self.client_secret = None
        self.access_token = None

        if arguments['authenticate']:
            self.client_id = arguments['--client_id']
            self.client_secret = arguments['--client_secret']
            self.authenticate()
        else:
            try:
                # Fail if config file doesn't exist or is missing information
                self.read_config()
            except (IOError, configparser.NoOptionError,
                    configparser.NoSectionError):
                print('Missing config information, please run '
                      '"misfit authenticate"')
            else:
                # Everything is good! Get the requested resource(s)
                self.get_resource(arguments)

    def read_config(self):
        """ Read credentials from the config file """
        with open(self.config_file) as cfg:
            self.config.readfp(cfg)
        self.client_id = self.config.get('misfit', 'client_id')
        self.client_secret = self.config.get('misfit', 'client_secret')
        self.access_token = self.config.get('misfit', 'access_token')

    def write_config(self, access_token):
        """ Write credentials to the config file """
        self.config.add_section('misfit')
        self.config.set('misfit', 'client_id', self.client_id)
        self.config.set('misfit', 'client_secret', self.client_secret)
        self.config.set('misfit', 'access_token', access_token)
        with open(self.config_file, 'w') as cfg:
            self.config.write(cfg)
        print('Credentials written to %s' % self.config_file)

    def get_resource(self, arguments):
        """ Gets the resource requested in the arguments """
        user_id = arguments['--user_id']
        object_id = arguments['--object_id']
        start_date = arguments['--start_date']
        end_date = arguments['--end_date']
        detail = arguments['--detail']

        misfit = Misfit(self.client_id, self.client_secret, self.access_token,
                        user_id)

        if arguments['profile']:
            print(misfit.profile(object_id))
        elif arguments['device']:
            print(misfit.device(object_id))
        elif arguments['goal']:
            print(misfit.goal(start_date, end_date, object_id))
        elif arguments['summary']:
            print(misfit.summary(start_date, end_date, detail, object_id))
        elif arguments['session']:
            print(misfit.session(start_date, end_date, object_id))
        elif arguments['sleep']:
            print(misfit.sleep(start_date, end_date, object_id))

    def authenticate(self):
        """
        Open a browser to the authentication page, spool up a CherryPy to
        accept the response, and write resulting credentials to a config file.
        """

        # Thanks to the magic of docopts, I can be guaranteed to have a
        # a client_id and client_secret
        auth_server = AuthServer(self.client_id, self.client_secret)
        auth_server.authenticate()
        cherrypy.quickstart(auth_server)

        # Write the authentication information to a config file for later use
        self.write_config(auth_server.access_token)


def main():
    """ Parse the arguments and use them to create a MisfitCli object """
    version = 'Python Misfit %s' % __version__
    arguments = docopt(__doc__, version=version)
    MisfitCli(arguments)


if __name__ == '__main__':
    """ Makes this file runnable with "python -m misfit.cli" """
    main()