# -*- encoding: utf-8 -*-

{
    'name': 'Magento Integration',
    'author': 'Openlabs Technologies & Consulting Pvt Ltd.',
    'version': '0.1',
    'depends': [
        'base', 'sale'
    ],
    'category': 'Specific Industry Applications',
    'summary': 'Magento Integration',
    'description': """
This module integrates OpenERP with magento.
============================================

This will import the following:

* Product categories
* Products
* Customers
* Addresses
* Orders
    """,
    'data': [
        'wizard/test_connection.xml',
        'wizard/import_websites.xml',
        'wizard/import_catalog.xml',
        'wizard/import_orders.xml',
        'product.xml',
        'magento.xml',
    ],
    'css': [],
    'images': [],
    'demo': [],
    'installable': True,
    'application': True,
}
