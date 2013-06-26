=================================
|name| Melton Firebreak Install
=================================

.. toctree::
   :maxdepth: 2
   :numbered:

Introduction
============
The Melton Firebreak module is a custom module built on the IntraMaps Roam platform in order for Melton to streamline inspection of firebreaks.

This document is intended for system admins and is to be used as guide when installing |name| for Melton Firebreak.

Admin Tool Install
==================

1. Install QGIS by following :doc:`install_qgis`
2. Extract `IntraMaps Roam Admin` into `C:\\IntraMaps Roam Admin`

Device Install
==============+

1. Install QGIS on the device by following :doc:`install_qgis`

.. note:: 

	The following step is only needed if you have a network share on the device.  
	Having a network share will allow the |name| Admin Tool to install directly on the device

**With network share**

2. Edit `qmap-admin\\targets.config` in the `C:\\IntraMaps Roam Admin` directory to include the path to the network share for `Device 1 Network Share Install`

.. code-block:: json
	
	{
		"clients": {
			"Device 1 Network Share Install": {
				"path" : "\\devicename\\share",
				"projects" : [melton_firebreak]
			},
			"Local Install": {
				"path" : "C:/",
				"projects" : [melton_firebreak]
			}
		}
	}
		
3. Run `Raom Admin.bat` from `C:\\IntraMaps Roam Admin`
4. Install on the client by:
	4a. If the device has a network share select **Device 1 Network Share Install** from the **Clients** list
		1. Select **Install**
	4b. If no network access or share select **Local Install** from the **Clients** list
		1. Select **Install**
		2. Copy the `C:\\IntraMaps Roam` folder onto the device.  Normally `C:\IntraMaps Roam` is a good place but it doesn't matter.
	
5. Create a shortcut to `C:\\IntraMaps Roam\Roam.bat` on the device desktop.

Installing SQL Server Express
+++++++++++++++++++++++++++++

.. _SQL Server Express 2008: http://www.microsoft.com/en-us/download/details.aspx?id=26729

1. Install `SQL Server Express 2008`_
2. Accept all the defaults. Ensure that the follow compontants are installed:
	* Replication Components
	* SQL Server Management Studio
	
3.	After Default SQL Server Express install change the Server Authentication to **“SQL Server and Windows Authentication mode”**, so that SQL login is enabled.

	.. attention:: Restart the SQL Server Express Service for this to take effect.
	
	Using Management Studio
		a.	Connect to the database
		b.	Right mouse click the connection
		c.	Select properties
		d.	Select Security
		e.	Select “SQL Server and Windows Authentication mode”
		f.	Restart the SQL Express Service
		
			i.	Right mouse click the connection
			ii.	Select “Restart”

SQL Server Configuration
+++++++++++++++++++++++++++++++++

Database Creation
------------------

Make sure the laptop is connected to the network before doing the following tasks:

1.	Load `GenerateFirePreventionDB.sql` in Management Studio and run/execute the script. This will do the following

	a.	Create the database structure and stored procedures
	b.	Create fire user with password fire
	c.	Create linked server to MEL-57

After the above script is ran check to see if tables, views, stored procedure, user, and linked server has been created, see next 2 screen shots).

2.	In SQL Management Studio populate the FirePrevention database by running the following: `exec FirePrevention.dbo.refresh_lookup_data`.

	a.	Open new query window, 
	b.	select Fire Prevention Database 
	c.	copy and paste exec FirePrevention.dbo.refresh_lookup_data
	d.	execute procedure


Replication
------------

In SQL Management Studio create the subscription.  To do this:

1.	Right click on Replication node and select New Subscription. Runs wizard
2.	Click on <Find SQL Server Publisher> and connect to your network SQL Server.
3.	Password:  F1re
4.	Select the FirePrevention Database and Publication.  Click Next. 
5.	Select Run each agent as its Subscriber (pull subscriptions).  Click Next.  
6.	Select the Subscription Database on the laptop.  Click Next.  
7.	Click on … 
8.	Use the following options:
9.	Use SQL server login 

	* Login: `Fire`
	* Password: `F1re`
	
10.	Click Next and accept all defaults.  Click Next again.  
11.	Tick on Initialize At first synchronisation.   Click Next.  
12.	Select Client from the drop down menu under Subscription Type.  Click Next.  
l3.	Click Next and then Finish to complete the process.  

.. note:: If you need to setup the subscription again, remember to delete the client subscription and delete at published also. 

Connection String Setup
++++++++++++++++++++++++++++++++

Roam needs the connection string configured in different places in order to connect to the server correctly.

These places include:

	* DSN for data entry form
	* Replication Scripts
	
ODBC DSN Connection	
~~~~~~~~~~~~~~~~~~~~

This connection is used by both QGIS and the custom Melton form in order to connect to the database.

1. Open `C:\\IntraMaps Roam Admin\\projects\\melton_firebreak\\install\\FirePreventionDSN32bit.reg` in text editor

.. note:: Use FirePreventionDSN64bit.reg if running on a 64bit platform.

2. Replace `"Server"="nathan-dms\\express08"` with the local server install.

.. note:: If defaults were used in the SQL installer `localhost` should also work here.

3. Run `FirePreventionDSN32bit.reg` to add those entries to the registry
