Magento OpenERP Integration
===========================

.. image:: https://travis-ci.org/openlabs/magento_integration.png?branch=develop
    :target: https://travis-ci.org/openlabs/magento_integration

This is a stable version of Magento OpenERP connector II, combining
the latest stable versions of the e-commerce platform and ERP software,
Magento 1.7 and OpenERP 7 respectively. This connector eradicates the
earlier problems of the Magento OpenERP connector as the code is written
from scratch. The Magento OpenERP connector is fully tested automatically
for regressions. The developers at Openlabs have followed the policy of
‘Simple is Beautiful’ for the creation of this connector.

.. image:: static/src/img/icon.png

The Magento OpenERP connector was created out of respect for the customers
of Openlabs and the users around the world, who were left stranded after
the release of OpenERP version 7. The primary motive was to create a simpler,
faster and clean connector unlike the previous ones. The connector is available
free of charge.


Features of Magento OpenERP connector
--------------------------------------

* Multiple Magento instance architecture: The existing structure has been
  retained with each instance having multiple websites with each website
  comprising of different stores leading to a group of store views. The 
  users can import these Magento instance parameters to OpenERP with the
  assistance of this connector.
* Import and Export: Users can import catalogues, categories and products
  along with customers’ information and addresses. The Magento OpenERP 
  connector imports every order status including the cancelled orders.
  The other imported orders are pending, enqueued, started, done or
  failed. The connector also creates a contact if it did not exist earlier.
* Synchronization: The Magento OpenERP connector processes the import of
  orders on the basis of the order status in OpenERP, thus synchronising
  the information across the e-commerce and ERP platforms.
* No Duplication: One individual task is created for each record to import 
  in OpenERP for sales order, customer, product and other categories thus
  reducing data redundancy.
* Fully Tested: The connector and the integration is completely scrutinized
  by unit test cases which check the functionality with different order and
  product types and other combinations. The testing ensures that the
  connector behavior is predictable and active development does not hinder
  the working features. You can 
  `see it <https://travis-ci.org/openlabs/magento_integration>`_ for yourself.


New features and functionality to be implemented have been added to
our `issues list <https://github.com/openlabs/magento_integration/issues>`_. 

Contributions and suggestions to improve the connector are always welcome,
courtesy to the truly 100% Open Source nature of the software.


Website
-------

Visit the `Openlabs website <http://www.openlabs.co.in>`_ for latest news
and downloads. You can also follow us on Twitter 
`@openlabsindia <http://twitter.com/openlabsindia>`_ to receive updates on
releases.

Support
-------

If you have any questions or problems, please report an
`issue <https://github.com/openlabs/magento-integration/issues>`_.

You can also reach us at `support@openlabs.co.in <mailto:support@openlabs.co.in>`_
or talk to a human at +1 813 793 6736. Please do not email any of the Openlabs
developers directly with issues or questions as you're more likely to get an
answer if you create a github issue or email us at the above address.

You can also mail us your ideas and suggestions about any changes.

About Us
--------

Openlabs specialises in building business applications for small and medium
enterprises. Our previous efforts includes nereid, Poweremail, Magento 
OpenERP integration & Callisto modules for OpenERP. Openlabs is committed
to creating innovations in the Open Source sphere.
