Introduction
==============
.. image:: https://travis-ci.org/embray/setup.cfg.png?branch=master
   :alt: travis build status
   :target: https://travis-ci.org/embray/setup.cfg

``setup.cfg`` is a cheekily named Python package which supports providing
all of a Python distribution's metadata and build configuration via the
``setup.cfg`` *file* at the base of the distribution's source tree, rather
than in the ``setup.py`` script.

The standard ``setup.py`` script is reduced to a stub which uses the
``setup.cfg`` package to convert the contents of the ``setup.cfg`` file to
keyword arguments understood by the ``setup()`` function (in particular, the
implementation provided by setuptools).  Thus all the standard functionality of
the ``setup.py`` script is still supported for tools and procedures that use
it.

In other words, rather than defining your project in a source file, it is
defined in an easy to parse, easy to read plain-text file.  However, several
hook points are still provided where Python functions can modify the build
process if necessary.  But efforts are made to minimize the need for this
in the majority of Python projects.

This package was originally called ``d2to1``, and was intended as a temporary
translation layer between the original distutils and the ill-fated distutils2
project.  distutils2 introduced the idea of providing all the project's
metadata and build configuration via the ``setup.cfg`` file.  *This* project
takes the same idea but goes beyond what was fully supported by distutils2.


Usage
=======
``setup.cfg`` *requires* a distribution to use setuptools.  Your distribution
must include a specially-formatted "setup.cfg" file, and a minimal "setup.py"
script.  For details on writing the setup.cfg, see the `distutils2
documentation`_.  A simple sample can be found in ``setup.cfg``'s own setup.cfg
file (it uses its own machinery to install itself)::

    [metadata]
    name = setup.cfg
    version = 0.9.0.dev
    author = Erik M. Bray
    author-email = embray@stsci.edu
    summary = Reads a distributions's metadata from its setup.cfg file and passes it to setuptools.setup()
    description-file =
        README.rst
        CHANGES.rst
    home-page = http://pypi.python.org/pypi/setup.cfg
    requires-dist = setuptools
    classifier = 
        Development Status :: 5 - Production/Stable
        Environment :: Plugins
        Framework :: Setuptools Plugin
        Intended Audience :: Developers
        License :: OSI Approved :: BSD License
        Operating System :: OS Independent
        Programming Language :: Python
        Programming Language :: Python :: 3
        Topic :: Software Development :: Build Tools
        Topic :: Software Development :: Libraries :: Python Modules
        Topic :: System :: Archiving :: Packaging

    [files]
    packages =
        setup
        setup.cfg
        setup.cfg.extern
    extra_files =
        CHANGES.rst
        LICENSE
        ez_setup.py

The minimal setup.py should look something like this::

 #!/usr/bin/env python

 try:
     from setuptools import setup
 except ImportError:
     from ez_setup import use_setuptools
     use_setuptools()
     from setuptools import setup

 setup(
     setup_requires=['setup.cfg'],
     setup_cfg=True
 )

Note that it's important to specify ``setup_cfg=True`` or else the
``setup.cfg`` functionality will not be enabled.  It is also possible to set
``setup_cfg='some_file.cfg'`` to specify the (relative) path of the setup.cfg
file to use.  But in general this functionality should not be necessary.

It should also work fine if additional arguments are passed to ``setup()``, but
it should be noted that they will be clobbered by any options in the setup.cfg
file.

.. _distutils2 documentation: http://alexis.notmyidea.org/distutils2/setupcfg.html
