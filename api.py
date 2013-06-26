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
