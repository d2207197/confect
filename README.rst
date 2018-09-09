Confect
=======

``confect`` is a Python configuration library.

It provides a pleasant configuration definition and access interface, and it reads unrestricted python configuration file.

Basic Usage
-----------

Calling ``confect.Conf()`` creates a new configuration manager object. All
configuration properties resides in it. It is possible to create multiple
``Conf`` object, but normally, one ``Conf`` object per application. Initialize
one in some module, then import and use it anywhere in your application.

Put following lines in your application package. For example, in ``your_package.__init__.py``.

>>> from confect import Conf
>>> conf = Conf()

Configuration properties should be declared before using it. Use
``Conf.add_group(group_name)`` context manager to declare a configuration group
and all properties under it. It's nessasery to provide a default
value for each properties. Default value can be any type as long as the value
can be deepcopy. Group names shuold be valid attribute names.

Put your configuration group declaration code in the module which you need those
properties. And make sure that the declaration is before all the lines that
access these properties. Normally, the group name is your class name, module
name or subpackage name.

>>> from your_package import conf
>>> with conf.add_group('yummy') as yummy:
...     yummy.kind = 'seafood'
...     yummy.name = 'fish'
...     yummy.weight = 10
>>> conf.yummy.name
'fish'
>>> conf.yummy.weight
10
>>> class Yummy:
...     yummy_conf = conf.yummy
... def get_kind(self):
...     return yummy_conf.kind

Configuration properties and groups are immutable. You can only globally change
it by loading configuration files. Otherwise, they are always default values.

>>> conf.yummy.name = 'octopus'
Traceback (most recent call last):
   ...
confect.error.FrozenConfPropError: Configuration properties are frozen.

Configuration File
------------------

Use ``Conf.load_conf_file(path)`` or ``Conf.load_conf_module(module_name)`` to
load configuration files. No matter it is loaded before or after
groups/properties declaration, property values in configuration file always
override default values. Loading multiple files is possible, the latter one
would replace old values.

Be aware, you should access your configuration property values after load
configuration file. If not, you might get wrong/old/default value.

>>> conf.load_conf_file('path/to/conf.py')

The default configuration file is in Python. That makes your configuration file
programmable and unrestricted. In configuration file, import ``confect.c``
object and set all properties on it. Here's an example of configuration file.

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

   import json
   with open('secret.json') as f:
       secret = json.load(f)

   c.secret.key = secret['key']
   c.secret.token = secret['token']

The ``c`` object only exits when loading a python configuration file, it's not
possible to import it in your source code. You can set any property in any
configuration group onto the ``c`` object. However, they are only accessable if
you declared it in the source code with ``Conf.add_group(group_name)``.

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

Local Environment
-----------------

``Conf.local_env()`` context manager creates an environment that makes ``Conf``
object temporarily mutable. All changes would be restored when it leaves the
block.

>>> conf = Conf()
>>> conf.add_group('dummy', prop1=3, prop2='some string') # add group through keyword arguments
>>> with conf.local_env():
...     conf.dummy.prop1 = 5
...     print(conf.dummy.prop1)
5
...     call_some_function_use_this_property()
>>> print(conf.dummy.prop1)  # all configuration restored
3


To-Dos
======

- Utility functions for loading dictionary into ConfDepotGroup
