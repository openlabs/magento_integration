# -*- coding: utf-8 -*-
"""
    test_base

    :copyright: © 2013 by Openlabs Technologies & Consulting (P) Limited
    :license: AGPL, see LICENSE for more details.
"""
import os
import json

import unittest

from itsbroken.testing import POOL, install_module


def load_json(resource, filename):
    """Reads the json file from the filesystem and returns the json loaded as
    python objects

    On filesystem, the files are kept in this format:
        json----
              |
            resource----
                       |
                       filename

    :param resource: The prestashop resource for which the file has to be
                     fetched. It is same as the folder name in which the files
                     are kept.
    :param filename: The name of the file to be fethced without `.json`
                     extension.
    :returns: Loaded json from the contents of the file read.
    """
    root_json_folder = os.path.join(
        os.path.dirname(os.path.abspath(__file__)), 'json'
    )
    file_path = os.path.join(
        root_json_folder, resource, str(filename)
    ) + '.json'

    return json.loads(open(file_path).read())


class TestBase(unittest.TestCase):
    """Setup basic defaults
    """

    def setUp(self):
        "Setup"
        install_module('magento_integration')

    def setup_defaults(self, txn):
        """Setup default data
        """
        instance_obj = POOL.get('magento.instance')
        website_obj = POOL.get('magento.instance.website')

        # Create two instances
        self.instance_id1 = instance_obj.create(
            txn.cursor, txn.user, {
                'name': 'Test Instance 1',
                'url': 'some test url 1',
                'api_user': 'admin',
                'api_key': 'testkey',
            }, txn.context
        )
        self.instance_id2 = instance_obj.create(
            txn.cursor, txn.user, {
                'name': 'Test Instance 2',
                'url': 'some test url 2',
                'api_user': 'admin',
                'api_key': 'testkey',
            }, txn.context
        )

        # Create one website under each instance
        self.website_id1 = website_obj.create(txn.cursor, txn.user, {
            'name': 'A test website 1',
            'magento_id': 1,
            'code': 'test_code',
            'instance': self.instance_id1,
        })
        self.website_id2 = website_obj.create(txn.cursor, txn.user, {
            'name': 'A test website 2',
            'magento_id': 1,
            'code': 'test_code',
            'instance': self.instance_id2,
        })
