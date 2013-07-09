# -*- coding: utf-8 -*-
"""
    api

    Extends magento python api

    :copyright: (c) 2013 by Openlabs Technologies & Consulting (P) Limited
    :license: BSD, see LICENSE for more details.
"""
from magento.api import API


class Core(API):
    """
    This API extends the API for the custom API implementation
    for the magento extension
    """

    __slots__ = ()

    def websites(self):
        """
        Returns list of all websites
        """
        return self.call('ol_websites.list', [])

    def stores(self, filters=None):
        """
        Returns list of all group store

        :param filters: Dictionary of filters.

               Format :
                   {<attribute>:{<operator>:<value>}}
               Example :
                   {'website_id':{'=':'1'}}
        :return: List of Dictionaries
        """
        return self.call('ol_groups.list', [filters])

    def store_views(self, filters=None):
        """
        Returns list of all store views

        :param filters: Dictionary of filters.

               Format :
                   {<attribute>:{<operator>:<value>}}
               Example :
                   {'website_id':{'=':'1'}}
        :return: List of Dictionaries
        """
        return self.call('ol_storeviews.list', [filters])


class OrderConfig(API):
    '''
    Getting Order Configuration from magento.
    '''

    def get_states(self):
        """
        Get states of orders

        :return: dictionary of all states.
                 Format :
                    {<state>: <state title>}
                 Example :
                    {   'canceled': 'Canceled',
                        'closed': 'Closed',
                        'holded': 'On Hold',
                        'pending_payment': 'Pending Payment'
                    }
        """
        return self.call('sales_order.get_order_states', [])

    def get_shipping_methods(self):
        """
        Get available shipping methods.

        :return: List of dictionaries of all available shipping method.
                 Example :
                         [
                            {'code': 'flatrate', 'label': 'Flat Rate'},
                            {'code': 'tablerate', 'label': 'Best Way'},
                            ...
                         ]
        """
        return self.call('sales_order.shipping_methods', [])
