Introduction
============

Magento is a feature-rich eCommerce platform built on open-source technology
that provides online merchants with unprecedented flexibility and control over
the look, content and functionality of their eCommerce store.

A new bridge between OpenERP and Magento has been initiated by Openlabs team.
This module allows synchronization of Magento with Open ERP. It
supports Synchronization of Customers, Addresses, Product Categories, Products,
Order Statuses, and Orders.

To login to the ERP, see `Login Instructions`_.

.. _Login Instructions:

Login Instructions
------------------

Login to OpenERP
++++++++++++++++

To login to ERP using OpenERP client, you need to fill the following
information:

* Username: Ask your administrator for this information
* Password: Ask your administrator for this information

.. image:: _images/Login.png
    :width: 1000
    :align: center

Installation
------------

To install Magento Integration module, follow the below instructions:

1. The module should be placed under the addons folder as specified in the
   OpenERP configuration file.

2. Go to ``Settings``, click on *Update Modules List* shown under **Modules**

3. Search for magento module in the search bar at top-right side of the page.

4. Search returns the module named ``Magento Integration``, now click on
   the module to install, refer below screenshot:

    .. image:: _images/search_magento.png
        :width: 800
        :align: center

5. A new window is now open to install this, click on ``Install``.

    .. image:: _images/Install_magento.png
       :width: 800

6. On installing this a new window pop-ups asking ``Configure Accounting
   Data`` details for your taxes and chart of accounts. Enter the details
   and ``Continue``.

   .. image:: _images/Account_data.png
      :width: 800
      :align: center

7. Now magento is installed. To configure it, refer :ref:`configuration`.
