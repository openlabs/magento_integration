# -*- coding: utf-8 -*-
"""
    sale

    Sale

    :copyright: (c) 2013 by Openlabs Technologies & Consulting (P) Limited
    :license: AGPLv3, see LICENSE for more details.
"""
import magento
from openerp.osv import fields, osv
from openerp.tools.translate import _


# Its a map between order states of openerp and magento
# TODO: Replace by a better structure
ORDER_STATES_MAP = {
    'new': 'sent',
    'canceled': 'cancel',
    'closed': 'done',
    'complete': 'done',
    'processing': 'progress',
    'holded': 'sent',
    'pending_payment': 'sent',
    'payment_review': 'sent',
}


class Sale(osv.Model):
    "Sale"
    _inherit = 'sale.order'

    _columns = dict(
        magento_id=fields.integer('Magento ID', readonly=True),
        magento_instance=fields.many2one(
            'magento.instance', 'Magento Instance', readonly=True,
        ),
        store_view=fields.many2one(
            'magento.store.store_view', 'Store View', readonly=True,
        ),
    )

    _sql_constraints = [(
        'magento_id_instance_unique', 'unique(magento_id, magento_instance)',
        'A sale must be unique in an instance'
    )]

    def check_store_view_instance(self, cursor, user, ids, context=None):
        """
        Checks if instance of store view is same as instance of sale order

        :param cursor: Database cursor
        :param user: ID of current user
        :param ids: IDs of records
        :param context: Application context
        :return: True or False
        """
        for sale in self.browse(cursor, user, ids, context=context):
            if sale.store_view.instance != sale.magento_instance:
                return False
        return True

    _constraints = [
        (
            check_store_view_instance,
            'Error: Store view must have same instance as sale order',
            []
        )
    ]

    def find_or_create_using_magento_data(
        self, cursor, user, order_data, context
    ):
        """
        Find or Create sale using magento data

        :param cursor: Database cursor
        :param user: ID of current user
        :param order_data: Order Data from magento
        :param context: Application context
        :returns: Browse record of sale order found/created
        """
        sale = self.find_using_magento_data(
            cursor, user, order_data, context
        )
        if not sale:
            sale = self.create_using_magento_data(
                cursor, user, order_data, context
            )

        return sale

    def find_using_magento_data(
        self, cursor, user, order_data, context
    ):
        """
        Create sale using magento data

        :param cursor: Database cursor
        :param user: ID of current user
        :param order_data: Order Data from magento
        :param context: Application context
        :returns: Browse record of sale order found
        """
        # each sale has to be unique in an instance of magento
        sale_ids = self.search(cursor, user, [
            ('magento_id', '=', int(order_data['order_id'])),
            ('magento_instance', '=', context.get('magento_instance'))
        ], context=context)

        return sale_ids and self.browse(
            cursor, user, sale_ids[0], context
        ) or None

    def find_or_create_using_magento_increment_id(
        self, cursor, user, order_increment_id, context
    ):
        """
        Finds or create sale order using magento ID

        :param cursor: Database cursor
        :param user: ID of current user
        :param order_increment_id: Order increment ID from magento
        :type order_increment_id: string
        :param context: Application context
        :returns: Browse record of sale order created/found
        """
        instance_obj = self.pool.get('magento.instance')

        sale = self.find_using_magento_increment_id(
            cursor, user, order_increment_id, context
        )

        if not sale:
            instance = instance_obj.browse(
                cursor, user, context['magento_instance'], context=context
            )

            with magento.Order(
                instance.url, instance.api_user, instance.api_key
            ) as order_api:
                order_data = order_api.info(order_increment_id)

            sale = self.create_using_magento_data(
                cursor, user, order_data, context
            )

        return sale

    def find_using_magento_id(self, cursor, user, order_id, context):
        """
        Create sale using magento id

        :param cursor: Database cursor
        :param user: ID of current user
        :param order_id: Order ID from magento
        :type order_id: integer
        :param context: Application context
        :returns: Browse record of sale order created
        """
        # each sale has to be unique in an instance of magento
        sale_ids = self.search(cursor, user, [
            ('magento_id', '=', order_id),
            ('magento_instance', '=', context.get('magento_instance'))
        ], context=context)
        return sale_ids and self.browse(
            cursor, user, sale_ids[0], context
        ) or None

    def find_using_magento_increment_id(
        self, cursor, user, order_increment_id, context
    ):
        """
        Create sale using magento id

        :param cursor: Database cursor
        :param user: ID of current user
        :param order_increment_id: Order Increment ID from magento
        :type order_increment_id: string
        :param context: Application context
        :returns: Browse record of sale order created
        """
        instance_obj = self.pool.get('magento.instance')

        instance = instance_obj.browse(
            cursor, user, context['magento_instance'], context=context
        )

        # Each sale has to be unique in an instance of magento
        sale_ids = self.search(cursor, user, [
            ('name', '=', instance.order_prefix + order_increment_id),
            ('magento_instance', '=', context['magento_instance'])
        ], context=context)

        return sale_ids and self.browse(
            cursor, user, sale_ids[0], context
        ) or None

    def create_using_magento_data(self, cursor, user, order_data, context):
        """
        Create a sale order from magento data

        :param cursor: Database cursor
        :param user: ID of current user
        :param order_data: Order Data from magento
        :param context: Application context
        :returns: Browse record of sale order created
        """
        currency_obj = self.pool.get('res.currency')
        store_view_obj = self.pool.get('magento.store.store_view')
        partner_obj = self.pool.get('res.partner')
        uom_obj = self.pool.get('product.uom')
        product_obj = self.pool.get('product.product')

        store_view = store_view_obj.browse(
            cursor, user, context['magento_store_view'], context
        )
        if not store_view.shop:
            raise osv.except_osv(
                _('Not Found!'),
                _(
                    'Magento Store %s should have a shop configured.'
                    % store_view.store.name
                )
            )
        if not store_view.shop.pricelist_id:
            raise osv.except_osv(
                _('Not Found!'),
                _(
                    'Shop on store %s does not have a pricelist!'
                    % store_view.store.name
                )
            )

        instance = store_view.instance

        currency = currency_obj.search_using_magento_code(
            cursor, user, order_data['order_currency_code'], context
        )
        partner = partner_obj.find_or_create_using_magento_id(
            cursor, user, order_data['customer_id'], context
        )

        partner_invoice_address = \
            partner_obj.find_or_create_address_as_partner_using_magento_data(
                cursor, user, order_data['billing_address'], partner, context
            )

        partner_shipping_address = \
            partner_obj.find_or_create_address_as_partner_using_magento_data(
                cursor, user, order_data['shipping_address'], partner, context
            )
        unit, = uom_obj.search(
            cursor, user, [('name', '=', 'Unit(s)')], context=context
        )

        sale_data = {
            'name': instance.order_prefix + order_data['increment_id'],
            'shop_id': store_view.shop.id,
            'date_order': order_data['created_at'].split()[0],
            'partner_id': partner.id,
            'pricelist_id': store_view.shop.pricelist_id.id,
            'currency_id': currency.id,
            'partner_invoice_id': partner_invoice_address.id,
            'partner_shipping_id': partner_shipping_address.id,
            'magento_id': int(order_data['order_id']),
            'magento_instance': instance.id,
            'store_view': store_view.id,
            'order_line': [
                (0, 0, {
                    'name': item['name'],
                    'price_unit': float(item['price']),
                    'product_uom': unit,
                    'product_uom_qty': float(item['qty_ordered']),
                    'notes': item['product_options'],
                    'product_id':
                        product_obj.find_or_create_using_magento_id(
                            cursor, user, item['product_id'],
                            context=context
                        ).id
                }) for item in order_data['items']
            ]
        }

        if float(order_data.get('shipping_amount')):
            sale_data['order_line'].append(
                self.get_shipping_line_data_using_magento_data(
                    cursor, user, order_data, context
                )
            )

        if float(order_data.get('discount_amount')):
            sale_data['order_line'].append(
                self.get_discount_line_data_using_magento_data(
                    cursor, user, order_data, context
                )
            )

        sale_id = self.create(
            cursor, user, sale_data, context=context
        )

        sale = self.browse(cursor, user, sale_id, context)

        # Process sale now
        self.process_sale_using_magento_state(
            cursor, user, sale, order_data['state'], context
        )

        return sale

    def get_shipping_line_data_using_magento_data(
        self, cursor, user, order_data, context
    ):
        """
        Create a shipping line for the given sale using magento data

        :param cursor: Database cursor
        :param user: ID of current user
        :param order_data: Order Data from magento
        :param context: Application context
        """
        uom_obj = self.pool.get('product.uom')

        unit, = uom_obj.search(
            cursor, user, [('name', '=', 'Unit(s)')], context=context
        )

        return (0, 0, {
            'name': 'Magento Shipping',
            'price_unit': float(order_data.get('shipping_amount', 0.00)),
            'product_uom': unit,
            'notes': ' - '.join([
                order_data['shipping_method'],
                order_data['shipping_description']
            ])
        })

    def get_discount_line_data_using_magento_data(
        self, cursor, user, order_data, context
    ):
        """
        Create a discount line for the given sale using magento data

        :param cursor: Database cursor
        :param user: ID of current user
        :param order_data: Order Data from magento
        :param context: Application context
        """
        uom_obj = self.pool.get('product.uom')

        unit, = uom_obj.search(
            cursor, user, [('name', '=', 'Unit(s)')], context=context
        )

        return (0, 0, {
            'name': order_data['discount_description'] or 'Magento Discount',
            'price_unit': - float(order_data.get('discount_amount', 0.00)),
            'product_uom': unit,
            'notes': order_data['discount_description'],
        })

    def process_sale_using_magento_state(
        self, cursor, user, sale, magento_state, context
    ):
        """Process the sale in openerp based on the state of order
        when its imported from magento

        :param cursor: Database cursor
        :param user: ID of current user
        :param sale: Browse record of sale
        :param magento_state: State on magento the order was imported in
        :param context: Application context
        """
        # TODO: Improve this for invoicing and shipping etc
        openerp_state = ORDER_STATES_MAP[magento_state]

        # If order is canceled, just cancel it
        if openerp_state == 'cancel':
            self.action_cancel(cursor, user, [sale.id], context)
            return

        # Order is not canceled, move it to quotation
        self.action_button_confirm(cursor, user, [sale.id], context)

        if openerp_state in ['closed', 'complete', 'processing']:
            self.action_wait(cursor, user, [sale.id], context)

        if openerp_state in ['closed', 'complete']:
            self.action_done(cursor, user, [sale.id], context)
