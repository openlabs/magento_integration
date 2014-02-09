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

**Step 1: Installation of Magento core API extension**

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


**Step 2: Installation of Magento Integration [OpenERP module]**

**Setup Python environment**

1. If not already installed by the default python installation, download the 
   pycountry module and install it in your python directory

2. Download the `magento module <https://github.com/openlabs/magento>`_ and 
   install it in your python directory (*)

(*) it seems that in linux installations, Magento Integration takes care of 
'magento module' and installs it when running the Magento Integration setup 
(see .5 below). So you have to install it yourself only if you are working 
under windows systems because for some reason Magento Integration lacks to 
install the 'magento module' (to be confirmed by developers)

(if your openERP is installed on a Windows systems, copy the above modules from
YourPythonDir\\Lib\\site-packages to YourOpenErpDir\\Server\\server)

**Downloading the magento_integration module**

1. The module source is available online and can be downloaded from
   `here <https://github.com/openlabs/magento_integration>`_.

2. The module can be downloaded as a `zip` or can be `cloned` by running

    .. code-block:: sh

        git clone https://github.com/openlabs/magento_integration.git

    OR

    .. code-block:: sh

        git clone git@github.com:openlabs/magento_integration.git

3. If the module is downloaded as a zip, extract the module which will
   give a directory.

   .. warning::

      The directory name of the extracted contents should be
      `magento_integration`. The module will not work otherwise as OpenERP
      identifies modules by the folder name.

      If you are downloading the source from github, the folder name
      created includes the branch name like `magento_integration-develop`.

4. Copy this directory to **addons** folder of openerp. [Advanced
   users can update the addons path to add this module's parent folder in their
   server config file.]

5. From the module directory, use the setup.py script with the command:

   .. code-block:: sh

        python setup.py install

**Installing the module in OpenERP database**

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

1. Go to ``Settings``, click on *Update Modules List* shown under **Modules**

2. Search for magento module in the search bar at top-right side of the page.

3. Search returns the module named ``Magento Integration``, now click on
   the module to install, refer below screenshot:

    .. image:: _images/search_magento.png
        :width: 800
        :align: center

4. A new window is now open to install this, click on ``Install``.

    .. image:: _images/Install_magento.png
       :width: 800

5. On installing this a new window pop-ups asking ``Configure Accounting
   Data`` details for your taxes and chart of accounts. Enter the details
   and ``Continue``.

   .. image:: _images/Account_data.png
      :width: 800
      :align: center

6. Now magento is installed. To configure it, refer :ref:`configuration`.
