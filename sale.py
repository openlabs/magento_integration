# -*- coding: utf-8 -*-
"""
    sale

    Sale

    :copyright: (c) 2013 by Openlabs Technologies & Consulting (P) Limited
    :license: AGPLv3, see LICENSE for more details.
"""
import xmlrpclib

import magento
from openerp.osv import fields, osv
from openerp.tools.translate import _


class MagentoOrderState(osv.Model):
    """Magento - OpenERP Order State map

    This model stores a map of order states between OpenERP and Magento.
    This allows the user to configure the states mapping according to his/her
    convenience. This map is used to process orders in OpenERP when they are
    imported. This is also used to map the order status on magento when
    sales are exported. This also allows the user to determine in which state
    he/she wants the order to be imported in.
    """
    _name = 'magento.order_state'
    _description = 'Magento - OpenERP Order State map'

    _columns = dict(
        name=fields.char('Name', required=True, size=100, readonly=True),
        code=fields.char('Code', required=True, size=100, readonly=True),
        openerp_state=fields.selection([
            ('draft', 'Draft Quotation'),
            ('sent', 'Quotation Sent'),
            ('cancel', 'Cancelled'),
            ('waiting_date', 'Waiting Schedule'),
            ('progress', 'Sales Order'),
            ('manual', 'Sale to Invoice'),
            ('invoice_except', 'Invoice Exception'),
            ('done', 'Done')
        ], 'OpenERP State'),
        use_for_import=fields.boolean('Import orders in this magento state'),
        instance=fields.many2one(
            'magento.instance', 'Magento Instance', required=True,
            ondelete='cascade',
        )
    )

    _defaults = dict(
        use_for_import=lambda *a: 1,
    )

    _sql_constraints = [
        (
            'code_instance_unique', 'unique(code, instance)',
            'Each magento state must be unique by code in an instance'
        ),
    ]

    def create_all_using_magento_data(
        self, cursor, user, magento_data, context
    ):
        """This method expects a dictionary in which the key is the state
        code on magento and value is the state name on magento.
        This method will create each of the item in the dict as a record in
        this model.

        :param cursor: Database cursor
        :param user: ID of current user
        :param magento_data: Magento data in form of dict
        :param context: Application context
        :return: List of browse records of records created
        """
        new_records = []
        default_order_states_map = {
            # 'sent' here means quotation state, thats an OpenERP fuck up.
            'new': 'sent',
            'canceled': 'cancel',
            'closed': 'done',
            'complete': 'done',
            'processing': 'progress',
            'holded': 'sent',
            'pending_payment': 'sent',
            'payment_review': 'sent',
        }

        for code, name in magento_data.iteritems():
            if self.search(cursor, user, [
                ('code', '=', code),
                ('instance', '=', context['magento_instance'])
            ], context=context):
                continue

            new_records.append(
                self.create(cursor, user, {
                    'name': name,
                    'code': code,
                    'instance': context['magento_instance'],
                    'openerp_state': default_order_states_map[code],
                }, context=context)
            )

        return self.browse(
            cursor, user, new_records, context=context
        )


class Sale(osv.Model):
    "Sale"
    _inherit = 'sale.order'

    _columns = dict(
        magento_id=fields.integer('Magento ID', readonly=True),
        magento_instance=fields.many2one(
            'magento.instance', 'Magento Instance', readonly=True,
        ),
        magento_store_view=fields.many2one(
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
            if sale.magento_id:
                if sale.magento_store_view.instance != sale.magento_instance:
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
        if order_data['customer_id']:
            partner = partner_obj.find_or_create_using_magento_id(
                cursor, user, order_data['customer_id'], context
            )
        else:
            partner = partner_obj.create_using_magento_data(
                cursor, user, {
                    'firstname': order_data['customer_firstname'],
                    'lastname': order_data['customer_lastname'],
                    'email': order_data['customer_email'],
                    'magento_id': 0
                },
                context
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
            'magento_store_view': store_view.id,
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
            'price_unit': float(order_data.get('discount_amount', 0.00)),
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
        # TODO: Improve this method for invoicing and shipping etc
        magento_order_state_obj = self.pool.get('magento.order_state')

        state_ids = magento_order_state_obj.search(cursor, user, [
            ('code', '=', magento_state),
            ('instance', '=', context['magento_instance'])
        ])

        if not state_ids:
            raise osv.except_osv(
                _('Order state not found!'),
                _('Order state not found/mapped in OpenERP! '
                  'Please import order states on instance'
                 )
            )

        state = magento_order_state_obj.browse(
            cursor, user, state_ids[0], context=context
        )
        openerp_state = state.openerp_state

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

    def export_order_status_to_magento(self, cursor, user, sale, context):
        """
        Export order status to magento.

        :param cursor: Database cursor
        :param user: ID of current user
        :param sale: Browse record of sale
        :param context: Application context
        :return: Browse record of sale
        """
        if not sale.magento_id:
            return sale

        instance = sale.magento_instance
        if sale.state == 'cancel':
            increment_id = sale.name.split(instance.order_prefix)[1]
            # This try except is placed because magento might not accept this
            # order status change due to its workflow constraints.
            # TODO: Find a better way to do it
            try:
                with magento.Order(
                    instance.url, instance.api_user, instance.api_key
                ) as order_api:
                    order_api.cancel(increment_id)
            except xmlrpclib.Fault, f:
                if f.faultCode == 103:
                    return sale

        # TODO: Add logic for other sale states also

        return sale
