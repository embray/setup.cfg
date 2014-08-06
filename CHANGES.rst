Changes
=========


0.9.0 (unreleased)
------------------

- Renamed the project from ``d2to1`` to ``setup.cfg`` and added several
  enhancements to go along with the name change.


0.2.11 (2013-08-29)
-------------------

- Replaced ``distribute_setup.py`` with ``ez_setup.py`` in order to bootstrap
  with modern setuptools when necessary.

- Fixed a couple minor Python 3-specific issues. In particular the
  ``data_files`` option could be passed to ``setup()`` as a ``dict_items``
  object instead of a ``list`` which is what would normally be expected.

- Added a tox.ini (frankly I thought there already was one).


0.2.10 (2013-04-10)
-------------------

- Added support for the ``setup-requires-dist`` option in the ``[metadata]``
  section of setup.cfg.  This is analogous to the Setup-Requires-Dist metadata
  field supported by PEP-426 and uses the ``setup_requires`` argument to
  setuptools' ``setup()`` to implement it.

- Added support for the ``dependency_links`` and ``include_package_data``
  arguments to setuptools' ``setup()`` in the ``[backwards_compat]`` section of
  setup.cfg.

- When a setup_hook calls sys.exit() don't show a traceback for the
  SystemExit exception.

- Fixed a bug in the exception formatting when exceptions occur in setup.cfg
  handling.


0.2.9 (2013-03-05)
------------------

- Fixed a bug in the extra-files supported added in 0.2.8.  Makes sure that
  monkey-patches can't be installed more than once and that the log
  reference is properly encapsulated.


0.2.8 (2013-03-05)
------------------

- Improved handling of packages where the packages_root option is set. That is,
  the Python package is not directly in the root of the source tree, but is in
  some sub-directory.  Now the packages_root directory is prepended to
  sys.path while processing the setup.cfg and running setup hooks.

- Added support for the Keywords metadata field via the keywords option in the
  ``[metadata]`` section of setup.cfg.

- Fixed a missing import that caused a misleading exception when setup.cfg is
  missing.

- Upgraded the shipped distribute_setup.py to the latest for distribute 0.6.28

- Added a few basic functional tests, along with an infrastructure to add more
  as needed.  They can be run with nose and possibly with py.test though the
  latter hasn't been tested.

- Improved hook imports to work better with namespace packages.

- Added support for the extra_files option of the ``[files]`` section in
  setup.cfg.  This was a feature from distutils2 that provided an alternative
  to MANIFEST.in for including additional files in source distributions (it
  does not yet support wildcard patterns but maybe it should?)

- Added support for the tests_require setup argument from setuptools via
  the [backwards_compat] section in setup.cfg.

- Supports Python 3 natively without 2to3.  This makes Python 3 testing of
  d2to1 easier to support.


0.2.7 (2012-02-20)
------------------

- If no extension modules or entry points are defined in the setup.cfg, don't
  clobber any extension modules/entry points that may be defined in setup.py.


0.2.6 (2012-02-17)
------------------

- Added support for setuptools entry points in an ``[entry_points]`` section of
  setup.cfg--this is just for backwards-compatibility purposes, as
  packaging/distutils2 does not yet have a standard replacement for the entry
  points system.

- Added a [backwards_compat] section for setup.cfg for other options that are
  supported by setuptools/distribute, but that aren't part of the distutils2
  standard.  So far the only options supported here are zip_safe and use_2to3.
  (Note: packaging does support a use-2to3 option to the build command, but if
  we tried to use that, distutils would not recognize it as a valid build
  option.)

- Added support for the new (and presumably final) extension section format
  used by packaging.  In this format, extensions should be specified in config
  sections of the format ``[extension: ext_mod_name]``, where any whitespace is
  optional.  The old format used an ``=`` instead of ``:`` and is still
  supported, but should be considered deprecated.

- Added support for the new syntax used by packaging for the package_data
  option (which is deprecated in packaging in favor of the resources system,
  but still supported).  The new syntax is like::

      package_data =
          packagename = pattern1 pattern2 pattern3
          packagename.subpack = 
              pattern1
              pattern2
              pattern3

  That is, after ``package_data =``, give the name of a package, followed by
  an ``=``, followed by any number of whitespace separated wildcard patterns (or
  actual filenames relative to the package).  Under this scheme, whitespace is
  not allowed in the patterns themselves.


0.2.5 (2011-07-21)
------------------

- Made the call to pkg_resources.get_distribution() to set __version__ more
  robust, so that it doesn't fail on, for example, VersionConflict errors


0.2.4 (2011-07-05)
------------------

- Fixed some bugs with installation on Python 3


0.2.3 (2011-06-23)
------------------

- Renamed 'setup_hook' to 'setup_hooks' as is now the case in the packaging
  module.  Added support for multiple setup_hooks


0.2.2 (2011-06-15)
------------------

- Fixed a bug in DefaultGetDict where it didn't actually save the returned
  default in the dictionary--so any command options would get lost
- Fixed a KeyError when the distribution does not have any custom commands
  specified


0.2.1 (2011-06-15)
------------------

- Reimplemented command hooks without monkey-patching and more reliably in
  general (though it's still a flaming hack).  The previous monkey patch-based
  solution would break if d2to1 were entered multiple times, which could happen
  in some scenarios


0.2.0 (2011-06-14)
------------------

- Version bump to start using micro-version numbers for bug fixes only, now
  that the my primary feature goals are complete


0.1.5 (2011-06-02)
------------------

- Adds support for the data_files option under [files].  Though this is
  considered deprecated and may go away at some point, it can be useful in the
  absence of resources support
- Adds support for command pre/post-hooks.  Warning: this monkey-patches
  distutils.dist.Distribution a little bit... :(
- Adds (slightly naive) support for PEP 345-style version specifiers in
  requires-dist (environment markers not supported yet)
- Fixed a bug where not enough newlines were inserted between description files


0.1.4 (2011-05-24)
------------------

- Adds support for custom command classes specified in the 'commands' option
  under the [global] section in setup.cfg
- Adds preliminary support for custom compilers specified in the 'compilers'
  option under the [global] section in setup.cfg.  This functionality doesn't
  exist in distutils/setuptools/distribute, so adding support for it is a
  flaming hack.  It hasn't really been tested beyond seeing that the custom
  compilers come up in `setup.py build_ext --help-compiler`, so any real-world
  testing of this feature would be appreciated


0.1.3 (2011-04-20)
------------------

- Adds zest.releaser entry points for updating the version number in a
  setup.cfg file; only useful if you use zest.releaser--otherwise harmless
  (might eventually move this functionality out into a separate product)
- Though version 0.1.2 worked in Python3, use_2to3 wasn't added to the setup.py
  so 2to3 had to be run manually
- Fixed a crash on projects that don't have a description-file option

0.1.2 (2011-04-13)
------------------

- Fixed the self-installation--it did not work if a d2to1 version was not
  already installed, due to the use of `pkg_resources.require()`
- Adds nominal Python3 support
- Fixes the 'classifier' option in setup.cfg

0.1.1 (2011-04-12)
------------------

- Fixed an unhelpful error message when a setup_hook fails to import
- Made d2to1 able to use its own machinery to install itself

