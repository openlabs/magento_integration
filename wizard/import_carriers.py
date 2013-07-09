# -*- coding: utf-8 -*-
"""
    import_carriers

    Import Carriers

    :copyright: (c) 2013 by Openlabs Technologies & Consulting (P) Limited
    :license: AGPLv3, see LICENSE for more details.
"""
from openerp.osv import osv
from ..api import OrderConfig


class ImportCarriers(osv.TransientModel):
    "Import Carriers"
    _name = 'magento.instance.import_carriers'

    def import_carriers(self, cursor, user, ids, context):
        """
        Imports all the carriers for current instance

        :param cursor: Database cursor
        :param user: ID of current user
        :param ids: List of ids of records for this model
        :param context: Application context
        """
        instance_obj = self.pool.get('magento.instance')
        magento_carrier_obj = self.pool.get('magento.instance.carrier')

        instance = instance_obj.browse(
            cursor, user, context.get('active_id')
        )
        context.update({
            'magento_instance': instance.id
        })

        with OrderConfig(
            instance.url, instance.api_user, instance.api_key
        ) as order_config_api:
            mag_carriers = order_config_api.get_shipping_methods()

        magento_carrier_obj.create_all_using_magento_data(
            cursor, user, mag_carriers, context
        )
