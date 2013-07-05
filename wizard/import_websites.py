# -*- coding: UTF-8 -*-
'''
    magento-integration

    :copyright: (c) 2013 by Openlabs Technologies & Consulting (P) LTD
    :license: AGPLv3, see LICENSE for more details
'''
from openerp.osv import osv
from openerp.tools.translate import _

from ..api import Core, OrderConfig


class ImportWebsites(osv.TransientModel):
    "Import websites from magentp"
    _name = 'magento.instance.import_websites'
    _description = __doc__

    def import_websites(self, cursor, user, ids, context):
        """
        Import the websites and their stores/view from magento

        :param cursor: Database cursor
        :param user: ID of current user
        :param ids: Record IDs
        :param context: Application context
        """
        Pool = self.pool

        instance_obj = Pool.get('magento.instance')
        website_obj = Pool.get('magento.instance.website')
        store_obj = Pool.get('magento.website.store')
        store_view_obj = Pool.get('magento.store.store_view')
        magento_order_state_obj = Pool.get('magento.order_state')

        instance = instance_obj.browse(
            cursor, user, context.get('active_id'), context
        )

        context.update({
            'magento_instance': instance.id
        })

        # Import order states
        with OrderConfig(
            instance.url, instance.api_user, instance.api_key
        ) as order_config_api:
            magento_order_state_obj.create_all_using_magento_data(
                cursor, user, order_config_api.get_states(), context
            )

        # Import websites
        with Core(
            instance.url, instance.api_user, instance.api_key
        ) as core_api:
            website_ids = []
            store_ids = []

            mag_websites = core_api.websites()

            # Create websites
            for mag_website in mag_websites:
                website_ids.append(website_obj.find_or_create(
                    cursor, user, instance.id, mag_website, context
                ))

            for website in website_obj.browse(
                    cursor, user, website_ids, context=context):
                mag_stores = core_api.stores(
                    {'website_id': {'=': website.magento_id}}
                )

                # Create stores
                for mag_store in mag_stores:
                    store_ids.append(store_obj.find_or_create(
                        cursor, user, website.id, mag_store, context
                    ))

            for store in store_obj.browse(
                    cursor, user, store_ids, context=context):
                mag_store_views = core_api.store_views(
                    {'group_id': {'=': store.magento_id}}
                )

                # Create store views
                for mag_store_view in mag_store_views:
                    store_view_obj.find_or_create(
                        cursor, user, store.id, mag_store_view, context
                    )

        return self.open_websites(cursor, user, ids, instance, context)

    def open_websites(self, cursor, user, ids, instance, context):
        """
        Opens view for websites for current instance

        :param cursor: Database cursor
        :param user: ID of current user
        :param ids: Record IDs
        :param instance: Browse record of magento.instance
        :param context: Application context
        :return: The websites tree view to be rendered
        """
        ir_model_data = self.pool.get('ir.model.data')

        tree_res = ir_model_data.get_object_reference(
            cursor, user, 'magento_integration', 'instance_website_tree_view'
        )
        tree_id = tree_res and tree_res[1] or False

        return {
            'name': _('Magento Instance Websites'),
            'view_type': 'form',
            'view_mode': 'form,tree',
            'res_model': 'magento.instance.website',
            'views': [(tree_id, 'tree')],
            'context': context,
            'type': 'ir.actions.act_window',
            'domain': [('instance', '=', instance.id)]
        }

ImportWebsites()
