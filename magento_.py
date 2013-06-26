# -*- coding: UTF-8 -*-
'''
    magento

    :copyright: (c) 2013 by Openlabs Technologies & Consulting (P) LTD
    :license: AGPLv3, see LICENSE for more details
'''
from openerp.osv import fields, osv


class Instance(osv.Model):
    """Magento Instance

    Refers to a magento installation identifiable via url, api_user and api_key
    """
    _name = 'magento.instance'
    _description = "Magento Instance"

    _columns = dict(
        name=fields.char('Name', required=True, size=50),
        url=fields.char('Magento Site URL', required=True, size=255),
        api_user=fields.char('API User', required=True, size=50),
        api_key=fields.char('API Password / Key', required=True, size=100),
        active=fields.boolean('Active'),
        websites=fields.one2many(
            'magento.instance.website', 'instance', 'Websites'
        )
    )

    _defaults = dict(
        active=lambda *a: 1,
    )

    _sql_constraints = [
        ('url_unique', 'unique(url)', 'URL of an instance must be unique'),
    ]


class InstanceWebsite(osv.Model):
    """Magento Instance Website

    A magento instance can have multiple websites.
    They act as  ‘parents’ of stores. A website consists of one or more stores.
    """
    _name = 'magento.instance.website'
    _description = "Magento Instance Website"

    _columns = dict(
        name=fields.char('Name', required=True, size=50),
        code=fields.char('Code', required=True, size=50),
        instance=fields.many2one(
            'magento.instance', 'Instance', required=True,
        ),
        stores=fields.one2many(
            'magento.website.store', 'website', 'Stores'
        )
    )

    _sql_constraints = [(
        'code_instance_unique', 'unique(code, instance)',
        'Code of a website must be unique in an instance'
    )]


class WebsiteStore(osv.Model):
    """Magento Website Store or Store view groups

    Stores are ‘children’ of websites. The visibility of products and
    categories is managed on magento at store level by specifying the
    root category on a store.
    """
    _name = 'magento.website.store'
    _description = "Magento Website Store"

    _columns = dict(
        name=fields.char('Name', required=True, size=50),
        website=fields.many2one(
            'magento.instance.website', 'Website', required=True,
        ),
        instance=fields.related(
            'website', 'instance', type='many2one',
            relation='magento.instance', string='Instance'
        ),
        store_views=fields.one2many(
            'magento.store.store_view', 'store', 'Store Views'
        ),
    )


class WebsiteStoreView(osv.Model):
    """Magento Website Store View

    A store needs one or more store views to be browse-able in the front-end.
    It allows for multiple presentations of a store. Most implementations
    use store views for different languages.
    """
    _name = 'magento.store.store_view'
    _description = "Magento Website Store View"

    _columns = dict(
        name=fields.char('Name', required=True, size=50),
        code=fields.char('Code', required=True, size=50),
        store=fields.many2one(
            'magento.website.store', 'Store', required=True,
        ),
        instance=fields.related(
            'website', 'instance', type='many2one',
            relation='magento.instance', string='Instance'
        ),
        website=fields.related(
            'store', 'website', type='many2one',
            relation='magento.instance.website', string='Website'
        )
    )

    _sql_constraints = [(
        'code_store_unique', 'unique(code, store)',
        'Code of a storeview must be unique in a store'
    )]
