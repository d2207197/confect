
Confect - a Python configuration library loads Python configuration files
**************************************************************************

Introduction
==============

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

- **Loads configuration file through module importing**

  Confect loads configuration file through a given file path, or through module importing.
  It's easy to control the source of configuration file through ``PYTHONPATH``.

- **Loads configuration file multiple times**

  Sometimes we need multiple configuration files — one for project,
  one for team and one for personal use.
  And we want that the personal configuration file has the highest priority.
  If there's a configuration setting existing in that file, it would override values
  from other files.

- **Loads configuration properties from environment variable**

  This feature is convenient if you want to change a single or some properties values,
  and don't want to modify the configuration file.

- **Attachs command line options to some click_ command**

  You can change any configuration value through command line options, if your command is created by click_.

- **Better maintainability**

  Confect forces users to define configuration properties and set a default value before using them.
  And the ``conf`` object is immutable for reducing the possibility of making errors.


Install
========

``confect`` is a Python package hosted on PyPI and works only with Python 3.6 up.

Just like other Python packages, install it by pip_ into a virtualenv_
, or use poetry_ to manage project dependencies and virtualenv.

.. code:: console

   $ pip install confect


Basics
===========

Conf Object
-----------

Calling ``conf = confect.Conf()`` creates a new configuration manager object.

Suppose ``projx`` is your top-level package name. Put the following lines into
``projx/core.py`` or ``projx/confspec.py``

.. code:: python

   import confect
   conf = confect.Conf()

It is possible to create multiple ``Conf`` objects, but normally it's not what
you want. In most cases, initialize and manage only one ``Conf`` object in your
application, then import and use it anywhere.


Configuration Properties Declaration
------------------------------------

**Configuration properties should be declared before using it.** This feature
makes your code more readable and maintainable.

Two ways to declare properties.

1.  context manager:

    .. code:: python

      with conf.declare_group(group_name) as group_name:
          group_name.prop1 = 'default value'
          group_name.prop2 = 42

2. function call

   .. code:: python

     conf.declare_group(group_name, prop1='default value', prop2=42)

Group names and property names should be valid Python variable names, which
consist of letters (A-Z, a-z), digits (0-9), and the underscore character (_).
Normally, the group name is your class name, module name or subpackage name.

Default Value and Parser
^^^^^^^^^^^^^^^^^^^^^^^^^

Default values of all properties should be defined along with the declaration.
Use ``confect.prop(default, desc=None, prop_type=None)`` to specify details other than the
default value. ``desc`` is for commentary and the help message in CLI option.
Argument of ``prop_type`` is an instance of confect.PropertyType which is
responsable for CLI argument and environment variable parsing. ``prop_type`` of
popular Python types would be infered from default value automatically.

Default values don't have to be a workable value (e.g. fake secret keys or
passwords). The true workable value can be defined in the configuration file.
However, even if it's not a workable value, the mock default values still make
the declaration and the code more readable and maintainable. For instance:

.. code:: python

   with conf.declare_group('aws') as aws:
       aws.access_key_id = 'true-access-key'
       aws.secret_access_key = 'fake-key-plz-set-it-in-local_conf.py'

Declaration Example
^^^^^^^^^^^^^^^^^^^^^

.. code:: python

   import confect
   conf = confect.Conf()

   # declare properties with context manager
   with conf.declare_group('api') as api:
       # default value only. confect would infer property type automatically
       api.cache_prefix = 'projx_cache'
       api.cache_expire = confect.prop(
           default=60 * 60 * 24,
           desc="expire time in seconds")

       # add description for CLI help message and commentary
       api.url_base_path = confect.prop(
           default='api/v2/',
           desc='URL base path of API')


   with conf.declare_group('db') as db:
       db.host = '127.0.0.1'
       db.db_name = 'projx'
       db.username = 'projx_admin'

       # if default value has to be None, it'd be better to assign property
       # type manually for parsing
       db.password = confect.prop(
          default=None,
          prop_type=confect.prop_type.String(),
          desc='`None` for no password')

       db.port = confect.prop(
           default=None,
           prop_type=confect.prop_type.Integer(),
           desc='`None` for db engine default port')

   # declare properties with function call
   conf.declare_group(
       'ctr_predict_model',
       model_pickle_s3folder='s3://some-bucket/path/to/folder',
       model_version=confect.prop(default='v3')
   )


Declaration Location
^^^^^^^^^^^^^^^^^^^^^

Property declarations can be put into the module where the ``conf`` object is
located. Or, you can put them into those modules where you need these
configurations, like ``projx/db.py`` or ``projx/api.py``. Just make sure your
application import all these modules eagerly, not lazily.


Configuration Access
--------------------

After the group and properties are declared, they are accessable through
the ``conf`` object directly, like ``conf.group_name.prop_name``.

``projx/api.py``

.. code:: python

   from projx.core import conf

   @routes(conf.api.url_base_path + 'add')
   @redis_cache(key=conf.api.cache_prefix, expire=conf.api.cache_expire)
   def add(a, b)
       return a + b

``projx/db.py``

.. code:: python

   from projx.core import conf

   engine = create_engine(
        f'mysql://{conf.db.username}:{conf.db.password}'
        f'@{conf.db.host}/{conf.db.db_name}')


Access Errors
^^^^^^^^^^^^^^^^^^^^^^^^^

Make sure that the configuration properties are **declared before access**. If not,
exceptions would be raised.

.. code:: python

   >>> conf.unknown_group.unknown_prop
   Traceback (most recent call last):
     ...
   UnknownConfError: "Unknown configuration group 'unknown_group'"

.. code:: python

   >>> conf.api.unknown_prop
   Traceback (most recent call last):
     ...
   UnknownConfError: "Unknown 'unknown_prop' property in configuration group 'api'"


**Configuration properties and groups are immutable.** They are meant to be
altered globally by loading configuration files, environment variables or CLI
argument.

.. code:: python

   >>> conf.api.cache_expire = 60 * 60 * 3
   Traceback (most recent call last):
     ...
   confect.error.FrozenConfPropError: Configuration properties are frozen.


Configuration File
------------------

Confect loads Python configuration files. That makes your configuration file
programmable and unrestricted as we described in the section `How confect
differs from others?`_.

Configuration File Loading
^^^^^^^^^^^^^^^^^^^^^^^^^^

Two ways to load configuration file.

1. Through module importing: ``conf.load_module(module_name)``
2. Through Python file reading: ``conf.load_file(file_path)``

.. code:: python

   import confect
   conf = confect.Conf()

   # load configuration files through importing
   try:
       conf.load_module('local_conf')
   except ImportError:
       pass

   SYSTEM_CONF_PATH = Path('path/to/system_conf.py')
   if SYSTEM_CONF_PATH.exists():
       conf.load_file(SYSTEM_CONF_PATH)


Use ``PYTHONPATH`` environment varibale to control the source of configuration file.

.. code:: console

   $ vi local_conf.py
   $ export PYTHONPATH=.
   $ python your_application.py

Write Configuration File
^^^^^^^^^^^^^^^^^^^^^^^^^

It's not necessary and is unusual to have all configuration properties be defined in the
configuration file. *Put only those configuration properties and corresponding
values that you want to override the configuration file.*

In configuration file, import ``confect.c`` object and set all properties on it
as if ``c`` is the conf object. Here's an example of configuration file.

``local_conf.py``

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

-----------------------

   # overrides configuration with environment variables with the prefix `projx`
   conf.load_envvars('projx')


Add command line options
-------------------------

``conf.click_options`` decorator attachs all declared configuration to a click_
command.


``projx/cli.py``

.. code:: python

   import click
   from projx.core import conf

   @click.command()
   @conf.click_options
   def cli():
       click.echo(f'cache_expire = {conf.api.cache_expire}')

   if __name__ == '__main__':
       cli()

It automatically creates a comprehensive help message with all properties and default values.

.. code:: console

   $ python -m projx.cli --help
   Usage: cli.py [OPTIONS]

   Options:
     --api-cache_expire INTEGER  [default: 86400]
     --api-cache_prefix TEXT     [default: projx_cache]
     --api-url_base_path TEXT    [default: api/v2/]
     --db-db_name TEXT           [default: proj_x]
     --db-username TEXT          [default: proj_x_admin]
     --db-password TEXT          [default: your_password]
     --db-host TEXT              [default: 127.0.0.1]
     --help                      Show this message and exit.


The option do change the value of configuration property.

.. code:: console

   $ python -m projx.cli
   cache_expire = 86400
   $ python -m projx.cli --api-cache_expire 33
   cache_expire = 33


Advanced Usage
==============

Loading Configuration
---------------------

Configuration properties and groups are immutable. The standard way to change it
is to load configuration from files or environment variables.

Use ``Conf.load_file(path)`` or ``Conf.load_module(module_name)`` to
load configuration files, or use ``Conf.load_envvars(prefix)`` to load
configuration from environment variable. No matter the loading statement is
located before or after groups/properties declaration, property values in
configuration file always override default values. It's possible to load
configuration multiple times, the latter one would replace values from former loading.

Be aware, *you should access your configuration properties after load
configuration files.* If not, you might get wrong/default value. Therefore, we
usually load configuration file right after the statement of creating the
``Conf`` object.

The code in the section `Conf Object`_ is a simple example that loads only through module importing.
Here's an much more complex example that demostrates how to dynamically select and load configurations.

.. code:: python

   import sys
   import confect

   conf = confect.Conf()

   # load configuration file
   if len(sys.argv) == 2:
       conf.load_file(sys.argv[1])
   else:
       try:
          conf.load_file('path/to/team_conf.py')
       FileNotFoundError:
          logger.warning('Unable to find team configuration file')

       try:
          conf.load_file('path/to/personal_conf.py')
       FileNotFoundError:
          logger.info('Unable to find personal configuration file')

   # load configuration file through importing
   try:
       conf.load_module('projx_conf')
   except ImportError:
       logger.warning('Unable to load find configuration module %r',
                      'proj_x_conf')

   # overrides configuration with environment variables
   conf.load_envvars('projx')


Load Environment Variables
---------------------------

``Conf.load_envvars(prefix: str)`` automatically searches environment variables
in ``<prefix>__<group>__<prop>`` format. All of these three identifier are case
sensitive. If you have a configuration property ``conf.cache.expire_time`` and
you call ``Conf.load_envvars('projx')``. It will set that ``expire_time``
property to the parsed value of ``projx__cache__expire_time`` environment
variable.

>>> import os
>>> os.environ['projx__cache__expire'] = '3600'

>>> conf = confect.Conf()
>>> conf.load_envvars('projx')  # doctest: +SKIP

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
