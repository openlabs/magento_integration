Introduction
============

Magento is a feature-rich eCommerce platform built on open-source technology
that provides online merchants with unprecedented flexibility and control over
the look, content and functionality of their eCommerce store.

A new bridge between OpenERP and Magento has been initiated by Openlabs team.
This module allows synchronization of Magento with Open ERP. It
supports Synchronization of Customers, Addresses, Product Categories, Products,
Order Statuses, and Orders.

See `Installation`_ first, then to login to the ERP, see `Login Instructions`_.

.. _installation:

Installation
------------

**Step 1: Installation of Magento extension**

1. After login to magento Admin Panel, go to

System >> Magento Connect >> Magento Connect Manager

    .. image:: _images/goto-magento-connect-manager.png
       :width: 800
       :align: center

2. Key in your username and password, the same username and password you entered
   while login to magento
    
    .. image:: _images/login-magento-connect-manager.png
       :width: 800
       :align: center

3. Click on the second tab for settings and change preferred state to 'Beta'.
   (As of this date the plug-in is beta). Save your settings 

   .. image:: _images/set-to-beta.png
      :width: 800
      :align: center

.. note::
   Default state is ``Stable``, change it to ``Beta``.

4. Go to first tab i.e., ``Extensions`` to install magento-connector,

    .. image:: _images/magento-connect-manager.png
       :width: 800
       :align: center

5. You need to paste the following extension key in the box to install:

| **http://connect20.magentocommerce.com/community/Openlabs_OpenERPConnector**

|

    .. image:: _images/extension-key.png
       :width: 800
       :align: center

6. Click Install, and wait for the module to be shown for installation 

    .. image:: _images/loading.png
       :width: 800
       :align: center

7. Install it by clicking ``Proceed``, refer below screenshot:

    .. image:: _images/confirm-key.png
       :width: 800
       :align: center

8. The terminal shows the module installed, like shown below:

   .. image:: _images/terminal-refresh.png
      :width: 800
      :align: center

9. Now go to bottom of the page to check the installed module, where
   installed module is shown at the end of the list, see below:

    .. image:: _images/module-installed.png
       :width: 800
       :align: center

.. _Login Instructions:

Login to OpenERP
++++++++++++++++

To login to ERP using OpenERP client, you need to fill the following
information:

* Username: Ask your administrator for this information
* Password: Ask your administrator for this information

.. image:: _images/Login.png
    :width: 1000
    :align: center

**Step 2: Installation of Magento Integration**

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
