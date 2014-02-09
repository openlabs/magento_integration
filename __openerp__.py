# -*- encoding: utf-8 -*-

{
    'name': 'Magento Integration',
    'author': 'Openlabs Technologies & Consulting Pvt Ltd.',
    'version': '2.0dev',
    'depends': [
        'base',
        'sale',
        'mrp',
        'delivery',
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
        'wizard/update_catalog.xml',
        'wizard/import_orders.xml',
        'wizard/export_orders.xml',
        'wizard/import_carriers.xml',
        'wizard/export_inventory.xml',
        'wizard/export_tier_prices.xml',
        'wizard/export_shipment_status.xml',
        'wizard/export_catalog.xml',
        'product.xml',
        'magento.xml',
        'sale.xml',
        'account.xml',
        'security/ir.model.access.csv',
    ],
    'css': [],
    'images': [],
    'demo': [],
    'installable': True,
    'application': True,
}
