# -*- coding: UTF-8 -*-
'''
    magento

    :copyright: (c) 2013 by Openlabs Technologies & Consulting (P) LTD
    :license: AGPLv3, see LICENSE for more details
'''
from openerp.osv import fields, osv


class Category(osv.Model):
    """Product Category
    """
    _inherit = 'product.category'

    _columns = dict(
        magento_ids=fields.one2many(
            'magento.instance.product_category', 'category',
            string='Magento IDs', readonly=True,
        ),
    )

    def create_tree_using_magento_data(
        self, cursor, user, category_tree, context
    ):
        """Create the categories from the category tree

        :param cursor: Database cursor
        :param user: ID of current user
        :param category_tree: Category Tree from magento
        :param context: Application context
        """
        # Create the root
        root_categ = self.find_or_create_using_magento_data(
            cursor, user, category_tree, context=context
        )
        for child in category_tree['children']:
            self.find_or_create_using_magento_data(
                cursor, user, child, parent=root_categ.id, context=context
            )
            if child['children']:
                self.create_tree_using_magento_data(
                    cursor, user, child, context
                )

    def find_or_create_using_magento_data(
        self, cursor, user, category_data, parent=None, context=None
    ):
        """Find or Create category using magento data

        :param cursor: Database cursor
        :param user: ID of current user
        :param category_data: Category Data from magento
        :param parent: openerp ID of parent if present else None
        :param context: Application context
        :returns: Browse record of category found/created
        """
        category = self.find_using_magento_data(
            cursor, user, category_data, parent, context
        )
        if not category:
            category = self.create_using_magento_data(
                cursor, user, category_data, parent, context
            )

        return category

    def find_using_magento_data(
        self, cursor, user, category_data, parent=None, context=None
    ):
        """Find category using magento data

        :param cursor: Database cursor
        :param user: ID of current user
        :param category_data: Category Data from magento
        :param parent: openerp ID of parent if present else None
        :param context: Application context
        :returns: Browse record of category found or None
        """
        magento_category_obj = self.pool.get(
            'magento.instance.product_category'
        )
        record_ids = magento_category_obj.search(cursor, user, [
            ('magento_id', '=', int(category_data['category_id'])),
            ('instance', '=', context.get('magento_instance'))
        ], context=context)
        return record_ids and magento_category_obj.browse(
            cursor, user, record_ids[0], context=context
        ).category or None

    def create_using_magento_data(
        self, cursor, user, category_data, parent=None, context=None
    ):
        """Create category using magento data

        :param cursor: Database cursor
        :param user: ID of current user
        :param category_data: Category Data from magento
        :param parent: openerp ID of parent if present else None
        :param context: Application context
        :returns: Browse record of category created
        """
        category_id = self.create(cursor, user, {
            'name': category_data['name'],
            'parent_id': parent,
            'magento_ids': [(0, 0, {
                'magento_id': int(category_data['category_id']),
                'instance': context.get('magento_instance'),
            })]
        }, context=context)

        return self.browse(cursor, user, category_id, context=context)


class MagentoInstanceCategory(osv.Model):
    """Magento Instance - Product category store

    This model keeps a record of a category's association with an instance and
    the ID of category on that instance
    """
    _name = 'magento.instance.product_category'
    _description = 'Magento Instance - Product category store'

    _columns = dict(
        magento_id=fields.integer(
            'Magento ID', readonly=True, required=True, select=True,
        ),
        instance=fields.many2one(
            'magento.instance', 'Magento Instance', readonly=True,
            select=True, required=True
        ),
        category=fields.many2one(
            'product.category', 'Product Category', readonly=True,
            required=True, select=True
        )
    )

    _sql_constraints = [
        (
            'magento_id_instance_unique',
            'unique(magento_id, instance)',
            'Each category in an instance must be unique!'
        ),
    ]
