# -*- coding: UTF-8 -*-
'''
    magento-integration

    :copyright: (c) 2013 by Openlabs Technologies & Consulting (P) LTD
    :license: AGPLv3, see LICENSE for more details
'''
import xmlrpclib
import socket

import magento
from openerp.osv import osv
from openerp.tools.translate import _


class TestConnection(osv.TransientModel):
    "Test Magento Connection"
    _name = 'magento.instance.test_connection'
    _description = __doc__

    def default_get(self, cursor, user, fields, context):
        """Set a default state

        :param cursor: Database cursor
        :param user: ID of current user
        :param fields: List of fields on wizard
        :param context: Application context
        """
        self.test_connection(cursor, user, context)
        return {}

    def test_connection(self, cursor, user, context):
        """Test the connection to magento instance(s)

        :param cursor: Database cursor
        :param user: ID of current user
        :param context: Application context
        """
        Pool = self.pool

        instance_obj = Pool.get('magento.instance')

        instance = instance_obj.browse(
            cursor, user, context.get('active_id'), context
        )
        try:
            with magento.API(
                instance.url, instance.api_user, instance.api_key
            ):
                return
        except (
            xmlrpclib.Fault, IOError,
            xmlrpclib.ProtocolError, socket.timeout
        ):
            raise osv.except_osv(
                _('Incorrect API Settings!'),
                _('Please check and correct the API settings on instance.')
            )

TestConnection()
