
Confect - a Python configuration library loads Python configuration files
=============================================================================

Why you need a configuration library?
-------------------------------------


- **For storing secrets**

  You have a project that needs to access database or other services with password or some secret keys.
  Storing secrets and passwords in your code is not smart.
  You need a configuration file and a library for loading and using it in the runtime.

- **For different runtime environments**

  For example, database IP addresses and passwords in development environment normally differs from production environment.
  You need multiple configuration files for storing those information for different environment, and load one of them in the run time.

- **For better parameter management**

  You're running some experiments, e.g. working on Machine Learning projects.
  There're a bunch of parameters needs to be changed in the run time.
  And you want to manage them in a smarter and more elegant way.

How confect differs from others?
-------------------------------------

- **Python configuration files**

  This makes it possible to

  + have complex type objects as configuration values, like Decimal, timedelta
    or any class instance
  + dynamically handle complicated logic, you can use conditional statements
    like ``if`` in it.
  + read other TOML/YMAL/JSON/ini files or even environment variables in the
    configuration file.

- **can load configuration file through module importing**

  Confect loads configuration file through a given file path, or through module importing.
  It's easy to control the source of configuration file through ``PYTHONPATH``.

- **can load configuration file multiple times**

  Sometimes we need multiple configuration files — one for project,
  one for team and one for personal use.
  And we want that the personal configuration file has the highest priority.
  If there's a configuration setting existing in that file, it would override values
  from other files.

- **loads configurations properties from environment variable**

  This feature is convenient if you want to change a single or some properties values,
  and don't want to modify the configuration file.

- **attachs command line options to some click_ command**

  You can change any configuration value through command line options, if your command is created by click_.

- **better maintainability**

  Confect forces users to define configuration properties and set a default value before using them.
  And the ``conf`` object is immutable for reducing the possibility of making errors.


Install
========

``confect`` is a Python package hosted on PyPI and works only with Python 3.6 up.

Just like other Python packages, install it by pip_ into a virtualenv_
, or use poetry_ to manage project dependencies and virtualenv.

.. code:: console

   $ pip install confect


Basic Usage
===========

Initialize Conf object
----------------------

Calling ``conf = confect.Conf()`` creates a new configuration manager object.

For example, suppose ``proj_X`` is your top-level package name.
Put the following lines into ``proj_X/core.py``.

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

**Configuration properties should be declared before using it.** This feature
makes your code more readable and maintainable.

Use ``Conf.declare_group(group_name)`` context manager to declare a new
configuration group along with all properties and corresponding default values.
Default values can be any type. The group name should be a valid attribute name.
Normally, the group name is your class name, module name
or subpackage name.

The following code can be in the ``proj_X/core.py`` module after ``conf =
confect.Conf()``, or in those modules where you need these configuration, like
``proj_X/db.py`` or ``proj_X/api.py``.

.. code:: python

   with conf.declare_group('api') as cg: # `cg` stands for conf_group
       cg.cache_expire = 60 * 60 * 24
       cg.cache_prefix = 'proj_X_cache'
       cg.url_base_path = 'api/v2/'

   with conf.declare_group('db') as cg:
       cg.db_name = 'proj_x'
       cg.username = 'proj_x_admin'
       cg.password = 'your_password'
       cg.host = '127.0.0.1'


Make sure that the declaration is before all the lines that access these
properties. If not, exceptions would be raised.

Default values of all properties should be defined along with the configuration
declaration. It doesn't have to be a workable value (e.g. fake secret keys or
passwords), the true workable value can be defined in the configuration file.
However, even if it's not a workable value, the mock default values still makes
the declaration and the code more readable and maintainable.


Access Configuration
--------------------

After the group and properties are declared, they are accessable through
getting attribute from the ``Conf`` object, like this ``conf.group_name.prop_name``.

``proj_X/api.py``
.................

.. code:: python

   from proj_X.core import conf

   @routes(conf.api.url_base_path + 'add')
   @redis_cache(key=conf.api.cache_prefix, expire=conf.api.cache_expire)
   def add(a, b)
       return a + b

``proj_X/db.py``
.................

.. code:: python

   from proj_X.core import conf

   engine = create_engine(
        f'mysql://{conf.db.username}:{conf.db.password}'
        f'@{conf.db.host}/{conf.db.db_name}')


**Configuration properties and groups are immutable.** They can only be globally
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

.. code:: python

   from confect import c

   import os

   DEBUG = True

   if DEBUG:
       c.cache.expire = 1

   c.cache.key = os.environ['CACHE_KEY']

   # loading some secret file and set configuration
   import json
   with open('db_secret.json') as f:
       db_secret = json.load(f)

   c.db.username = db_secret['username']
   c.db.password = db_secret['password']


You can set any property in any configuration group onto the ``c`` object.
However, **they are only accessable if you declared it in the source code with**
``Conf.declare_group(group_name)``.

The ``c`` object only exits when loading a python configuration file, it's not
possible to import it in your source code.


Add command line options
-------------------------

``conf.click_options`` decorator attachs all declared configuration to a click_
command.


``proj_X/cli.py``
.................

.. code:: python

   import click
   from proj_X.core import conf

   @click.command()
   @conf.click_options
   def cli():
       click.echo(f'cache_expire = {conf.api.cache_expire}')

   if __name__ == '__main__':
       cli()

It automatically creates a comprehensive help message with all properties and default values.

.. code:: console

   $ python -m proj_X.cli --help
   Usage: cli.py [OPTIONS]

   Options:
     --api-cache_expire INTEGER  [default: 86400]
     --api-cache_prefix TEXT     [default: proj_X_cache]
     --api-url_base_path TEXT    [default: api/v2/]
     --db-db_name TEXT           [default: proj_x]
     --db-username TEXT          [default: proj_x_admin]
     --db-password TEXT          [default: your_password]
     --db-host TEXT              [default: 127.0.0.1]
     --help                      Show this message and exit.


The option do change the value of configuration property.

.. code:: console

   $ python -m proj_X.cli
   cache_expire = 86400
   $ python -m proj_X.cli --api-cache_expire 33
   cache_expire = 33


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

- A public interface for exporting a conf group into a dictionary
- A plugin for `Click <http://click.pocoo.org/5/>`_ arg `argparse <https://docs.python.org/3/library/argparse.html>`_  that adds command line options for altering configuration properties.
- Copy-on-write mechenism in ``conf.mutate_locally()`` for better performance and memory usage.
- API reference page


.. _click: http://click.pocoo.org/
.. _pip: https://pip.pypa.io/en/stable/
.. _virtualenv: https://hynek.me/articles/virtualenv-lives/
.. _poetry: https://poetry.eustace.io/
