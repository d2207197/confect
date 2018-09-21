Confect - a Python configuration library loads Python configuration files
=============================================================================

Why you need a configuration library?
-------------------------------------


- You have a project that needs to access database or other services with password or some secret keys. 
  Storing secrets and passwords in your code is not smart. 
  You need a configuration file and a library for loading and using it.

- Your project runs in different environments. 
  For example, database IP addresses and passwords in development environment normally differs from production environment. 
  You need multiple configuration files for storing those information for different environment, and load one of them in the run time.
  
- You're doing some experiments, e.g. Machine Learning projects. 
  There're a bunch of parameters needs to be changed in the run time. 
  And you want to manage them in a smarter and more elegant way.

How confect differs from others?
-------------------------------------

- loads Python configuration files. This makes it possible to

  + have complex type objects as configuration values, like Decimal, timedelta
    or any class instance
  + dynamically handle complicated logic, you can use conditional statements
    like ``if`` in it.
  + read other TOML/YMAL/JSON/ini files or even environment variables in the
    configuration file.

- supports multiple configuration file loading ways and can load multiple times.
  It loads configuration file through a given file path, or through module importing. 
- loads configurations properties from environment variable. 
  It's convenient if you want to change single or some properties values and don't want to modify the configuration file.
- forces users to predefine configuration properties for readability and maintainability.
- Immutable conf object for reducing the possibility of making errors. 
  No one should modify configuration too dynamically as if they are global variables.
- A readable and pleasant accessing interface
    

Install
========

``confect`` is a Python package hosted on PyPI and works only with Python 3.6 up.

Just like other Python packages, install it by `pip
<https://pip.pypa.io/en/stable/>`_ into a `virtualenv
<https://hynek.me/articles/virtualenv-lives/>`_, or use `poetry
<https://poetry.eustace.io/>`_ to manage project dependencies and virtualenv.

.. code:: console

   $ pip install confect


Basic Usage
===========

Initialize Conf object
----------------------

Calling ``conf = confect.Conf()`` creates a new configuration manager object.

For example, suppose ``proj_X`` is your top-level package name. 
Put the following lines into ``proj_X.core.py``.

.. code:: python

   import confect
   conf = confect.Conf()

   # load configuration files through importing
   try:
       conf.load_module('proj_X_conf')
   except ImportError:
       pass

   # overrides configuration with environment variables with the prefix `proj_X`
   conf.load_envvars('proj_X')
   
And import the ``conf`` object module in any other module

.. code:: python

   from proj_X.core import conf

It is possible to create multiple ``Conf`` objects, but normally you don't need
it. In most cases, initialize only one ``Conf`` object in one module of your
package, then import and use it anywhere in your application.

Use ``PYTHONPATH`` environment varibale to control the source of configuration file.

.. code:: console

   $ vi proj_X_conf.py
   $ export PYTHONPATH=.
   $ python your_application.py

Declare Configuration Groups and Properties
-------------------------------------------

Configuration properties should be declared before using it. This feature makes 
your code more readable and maintainable. Default values of all properties
should be defined along with the configuration declaration. 
It doesn't have to be a workable value
(like some secret key you shouldn't put it in the code), 
the true workable value can be defined 
in the configuration file. 
However, even if it's not a workable value, 
the default values still makes the declaration and the code more readable.

Use ``Conf.declare_group(group_name)`` context manager to declare a configuration
group and all properties under it at the same time. It's nessasery to provide
default values for each properties. Default values can be any type. The group
name should be a valid attribute name.

Put your configuration group declaration code in the module where you need those
properties. And make sure that the declaration is before all the lines that
access these properties, or it would raise exceptions.
Normally, the group name is your class name, module name or subpackage name.

Suppose that there's a ``proj_X/api.py`` module for http API service. 
We declared a new configuration group named of ``api``. 
And we need three configuration properties for the API service, 
``cache_expire``, ``cache_prefix`` and ``url_base_path``.

.. code:: python
   :number-lines: 1

   from proj_X.core import conf

   with conf.declare_group('api') as cg: # `cg` stands for conf_group
       cg.cache_expire = 60 * 60 * 24
       cg.cache_prefix = 'proj_X_cache'
       cg.url_base_path = 'api/v2/'

Access Configuration
--------------------

After the group and properties are declared, they are accessable through
getting attribute from the ``Conf`` object, like this ``conf.group_name.prop_name``.

Here's the rest of ``proj_X/api.py`` module for demostrating how to access configurations.

.. code:: python
   :number-lines: 9

   @routes(conf.api.url_base_path + 'add')
   @redis_cache(key=conf.api.cache_prefix, expire=conf.api.cache_expire)
   def add(a, b)
       return a + b


Configuration properties and groups are immutable. They can only be globally
changed by loading configuration files. Otherwise, they are always default
values.

>>> conf.api.cache_expire = 60 * 60 * 3
Traceback (most recent call last):
   ...
confect.error.FrozenConfPropError: Configuration properties are frozen.

Configuration File
------------------

Confect loads configuration files is in Python. That makes your configuration file
programmable and unrestricted as we described in the section `How confect differs from others?`_.

It's not necessary and is unusual to have all configuration properties be defined in the
configuration file. *Put only those configuration properties and corresponding
values that you want to override to the configuration file.*

In configuration file, import ``confect.c`` object and set all properties on it
as if ``c`` is the conf object. Here's an example of configuration file.

.. code-block:: python

   from confect import c

   c.yummy.kind = 'poultry'
   c.yummy.name = 'chicken'
   c.yummy.weight = 25

   import os
   # simple calculation or loading env var
   c.cache.expire = 60 * 60 # one hour
   c.cache.key = os.environ['CACHE_KEY']

   # it's easy to have conditional statement
   DEBUG = True
   if DEBUG:
       c.cache.disable = True

   # loading some secret file and set configuration
   import json
   with open('secret.json') as f:
       secret = json.load(f)

   c.secret.key = secret['key']
   c.secret.token = secret['token']

The ``c`` object only exits when loading a python configuration file, it's not
possible to import it in your source code. You can set any property in any
configuration group onto the ``c`` object. However,
*they are only accessable if you declared it in the source code with* ``Conf.declare_group(group_name)``.


Advanced Usage
==============

Loading Configuration
---------------------

Configuration properties and groups are immutable. The standard way to change it
is to load configuration from files or environment variables.

Use ``Conf.load_conf_file(path)`` or ``Conf.load_conf_module(module_name)`` to
load configuration files, or use ``Conf.load_envvars(prefix)`` to load
configuration from environment variable. No matter the loading statement is
located before or after groups/properties declaration, property values in
configuration file always override default values. It's possible to load 
configuration multiple times, the latter one would replace values from former loading.

Be aware, *you should access your configuration properties after load
configuration files.* If not, you might get wrong/default value. Therefore, we
usually load configuration file right after the statement of creating the
``Conf`` object.



The code in the section `Initialize Conf object`_ is a simple example that loads only through module importing. 
Here's an much more complex example that demostrates how to dynamically select and load configurations.

.. code:: python

   import sys
   import confect

   conf = confect.Conf()

   # load configuration file
   if len(sys.argv) == 2:
       conf.load_conf_file(sys.argv[1])
   else:
       try:
          conf.load_conf_file('path/to/team_conf.py')
       FileNotFoundError:
          logger.warning('Unable to find team configuration file')

       try:
          conf.load_conf_file('path/to/personal_conf.py')
       FileNotFoundError:
          logger.info('Unable to find personal configuration file')

   # load configuration file through importing
   try:
       conf.load_module('proj_X_conf')
   except ImportError:
       logger.warning('Unable to load find configuration module %r',
                      'proj_x_conf')

   # overrides configuration with environment variables
   conf.load_envvars('proj_X')




Load Environment Variables
---------------------------

``Conf.load_envvars(prefix: str)`` automatically searches environment variables
in ``<prefix>__<group>__<prop>`` format. All of these three identifier are case
sensitive. If you have a configuration property ``conf.cache.expire_time`` and
you call ``Conf.load_envvars('proj_X')``. It will set that ``expire_time``
property to the parsed value of ``proj_X__cache__expire_time`` environment
variable.

>>> import os
>>> os.environ['proj_X__cache__expire'] = '3600'

>>> conf = confect.Conf()
>>> conf.load_envvars('proj_X')  # doctest: +SKIP

If ``cache.expire`` has been declared, then

>>> conf.cache.expire
3600

Confect includes predefined parsers of these primitive types.

- ``str``: ``s``
- ``int``: ``int(s)``
- ``float``: ``float(s)``
- ``bytes``: ``s.decode()``
- ``datetime.datetime`` : ``pendulum.parse(s)``
- ``datetime.date`` : ``pendulum.parse(s).date()``
- ``Decimal`` : ``decimal.Decimal(s)``
- ``tuple`` : ``json.loads(s)``
- ``dict``: ``json.loads(s)``
- ``list``: ``json.loads(s)``

Mutable Environment
-----------------

``Conf.mutate_locally()`` context manager creates an environment that makes
``Conf`` object temporarily mutable. All changes would be restored when it
leaves the block. It is usaful on writing test case or testing configuration
properties in Python REPL.

>>> conf = Conf()
>>> conf.declare_group(  # declare group through keyword arguments
...      'dummy',
...      prop1=3,
...      prop2='some string')
...
>>> with conf.mutate_locally():
...      conf.dummy.prop1 = 5
...      print(conf.dummy.prop1)
5
...     call_some_function_use_this_property()
>>> print(conf.dummy.prop1)  # all configuration restored
3


To-Dos
======

- A function for loading dictionary into ``conflect.c``.
- A function that loads command line arguments and overrides configuration properties.
- Copy-on-write mechenism in ``conf.mutate_locally()`` for better performance and memory usage.
- API reference page
