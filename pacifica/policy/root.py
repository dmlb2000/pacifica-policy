#!/usr/bin/python
# -*- coding: utf-8 -*-
"""CherryPy root object class."""
from __future__ import print_function
import sys
from time import sleep
from json import dumps
import cherrypy
from .uploader.rest import UploaderPolicy
from .status.rest import StatusPolicy
from .ingest.rest import IngestPolicy
from .events.rest import EventsPolicy
from .reporting.rest import ReportingPolicy
from .config import get_config
from .globals import METADATA_CONNECT_ATTEMPTS, METADATA_WAIT
from .utils import requests_retry_session


def error_page_default(**kwargs):
    """The default error page should always enforce json."""
    cherrypy.response.headers['Content-Type'] = 'application/json'
    json_str = dumps({
        'postdata': cherrypy.request.body.read().decode('UTF-8'),
        'status': kwargs['status'],
        'message': kwargs['message'],
        'traceback': kwargs['traceback'],
        'version': kwargs['version']
    }, sort_keys=True, indent=4)
    print(json_str, file=sys.stderr)
    return json_str


# pylint: disable=too-few-public-methods
class Root(object):
    """
    CherryPy root object class.

    not exposed by default the base objects are exposed
    """

    exposed = True

    def __init__(self):
        """Create the local objects we need."""
        self.uploader = UploaderPolicy()
        self.status = StatusPolicy()
        self.reporting = ReportingPolicy()
        self.ingest = IngestPolicy()
        self.events = EventsPolicy()

    @staticmethod
    @cherrypy.tools.json_out()
    # pylint: disable=invalid-name
    def GET():
        """Return happy message about functioning service."""
        return {'message': 'Pacifica Policy Up and Running'}
    # pylint: enable=invalid-name

    @classmethod
    def try_meta_connect(cls, attempts=0):
        """Try to connect to the metadata service see if its there."""
        try:
            ret = requests_retry_session().get(get_config().get('metadata', 'status_url'))
            if ret.status_code != 200:
                raise Exception(
                    'try_meta_connect: {0}\n'.format(ret.status_code)
                )
        # pylint: disable=broad-except
        except Exception:
            # pylint: enable=broad-except
            if attempts < METADATA_CONNECT_ATTEMPTS:
                sleep(METADATA_WAIT)
                attempts += 1
                cls.try_meta_connect(attempts)
            else:
                raise Exception
# pylint: enable=too-few-public-methods
