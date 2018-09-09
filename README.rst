Confect
=======

``confect`` is a Python configuration library.

It provides a pleasant configuration definition and access interface, and it reads unrestricted python configuration file.

Basic Usage
-----------

Calling ``confect.Conf()`` creates a new configuration manager object. All
configuration properties resides in it. It is possible to create multiple
``Conf`` object, but normally, one ``Conf`` object per application. Initialize
it in some module, then import and use it anywhere in your package.

Put following lines in your application package. For example ``package_name.__init__.py``.

>>> from confect import Conf
>>> conf = Conf()

Configuration properties should be declared with a default value and group name
before using it. Default value can be any type as long as it can be deepcopy.
Group name shuold be a valid attribute name.

Put your configuration group declaration code in the module which you need it
and before all lines that access these properties. Normally, the group name is
your module name or subpackage name.

>>> from your_package import conf
>>> with conf.add_group('yummy') as yummy:
...     yummy.kind = 'seafood'
...     yummy.name = 'fish'
...     yummy.weight = 10
>>> yummy.name
'fish'
>>> yummy.weight
10

Use ``Conf.load_conf_file(path)`` or ``Conf.load_conf_module(module_name)`` to
load configuration files. It can be loaded before or after groups/properties
declaration. Loading multiple files is possible and won't break it. But be
aware, you should access your configuration properties after load configuration
file. If not, you might get wrong/old/default value of configuration property.

>>> conf.load_conf_file('path/to/conf.py')

The default configuration file is in Python. That makes your configuration file
programmable and unrestricted. Here's an example of configuration file.

.. code-block:: python

   from confect import c

   c.yummy.kind = 'poultry'
   c.yummy.name = 'chicken'
   c.yummy.weight = 25

   import os
   c.cache.expire = 60 * 60 # one hour
   c.cache.key = os.environ['CACHE_KEY']

   DEBUG = True
   if DEBUG:
       c.cache.disable = True

If it's hard for you to specify the path of configuration file. You can load it
through the import system of Python. Put your configuration file somewhere under
your package or make ``PYTHONPATH`` pointing to the directory it resides. Then
load it with ``Conf.load_conf_module(module_name)``.

.. code-block:: bash

   $ edit my_conf.py
   $ export PYTHONPATH=.
   $ python your_application.py

>>> from confect import Conf
>>> conf = Conf()
>>> conf.load_conf_module('my_conf')
