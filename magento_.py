# -*- coding: UTF-8 -*-
'''
    magento

    :copyright: (c) 2013 by Openlabs Technologies & Consulting (P) LTD
    :license: AGPLv3, see LICENSE for more details
'''
from openerp.osv import fields, osv


class Instance(osv.Model):
    """Magento Instance
    """
    _name = 'magento.instance'
    _description = __doc__
