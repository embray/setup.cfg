"""Main setup.cfg file processing and distutils setup."""

# These first two imports are not used, but are needed to get around an
# irritating Python bug that can crop up when using ./setup.py test.
# See: http://www.eby-sarna.com/pipermail/peak/2010-May/003355.html
import multiprocessing
import logging

import os
import re
import sys
import traceback

import distutils.ccompiler

from distutils import log
from distutils.errors import (DistutilsOptionError, DistutilsModuleError,
                              DistutilsFileError)

from setuptools.command.egg_info import manifest_maker
from setuptools.dist import Distribution
from setuptools.extension import Extension

from .extern.six import moves
from .util import (resolve_name, has_get_option, split_multiline, split_csv,
                   monkeypatch_method)

RawConfigParser = moves.configparser.RawConfigParser

# Mappings from setup() keyword arguments to setup.cfg options;
# The values are (section, option) tuples, or simply (section,) tuples if
# the option has the same name as the setup() argument
SETUP_ARGS_TO_CFG = {
    "name": ("metadata",),
    "version": ("metadata",),
    "author": ("metadata",),
    "author_email": ("metadata",),
    "maintainer": ("metadata",),
    "maintainer_email": ("metadata",),
    "url": ("metadata", "home_page"),
    "description": ("metadata", "summary"),
    "keywords": ("metadata",),
    "long_description": ("metadata", "description"),
    "download-url": ("metadata",),
    "classifiers": ("metadata", "classifier"),
    "platforms": ("metadata", "platform"),
    "license": ("metadata",),
    # Use setuptools install_requires, not
    # broken distutils requires
    "install_requires": ("metadata", "requires_dist"),
    "setup_requires": ("metadata", "setup_requires_dist"),
    "provides": ("metadata", "provides_dist"),
    "obsoletes": ("metadata", "obsoletes_dist"),
    "package_dir": ("files", 'packages_root'),
    "packages": ("files",),
    "package_data": ("files",),
    "data_files": ("files",),
    "scripts": ("files",),
    "py_modules": ("files", "modules"),
    "cmdclass": ("global", "commands"),
    "use_2to3": ("backwards_compat", "use_2to3"),
    "zip_safe": ("backwards_compat", "zip_safe"),
    "tests_require": ("backwards_compat", "tests_require"),
    "dependency_links": ("backwards_compat",),
    "include_package_data": ("backwards_compat",),
}

# setup() arguments that can have multiple values in setup.cfg
MULTI_FIELDS = set([
    "classifiers",
    "platforms",
    "install_requires",
    "provides",
    "obsoletes",
    "packages",
    "package_data",
    "data_files",
    "scripts",
    "py_modules",
    "dependency_links",
    "setup_requires",
    "tests_require",
    "cmdclass"
])

# setup() arguments that contain boolean values
BOOL_FIELDS = set(["use_2to3", "zip_safe", "include_package_data"])

# setup() arguments that take a comma-separated value
CSV_FIELDS = set(["keywords"])

# Arguments to Extension module descriptors
EXTENSION_FIELDS = set([
    "sources",
    "include_dirs",
    "define_macros",
    "undef_macros",
    "library_dirs",
    "libraries",
    "runtime_library_dirs",
    "extra_objects",
    "extra_compile_args",
    "extra_link_args",
    "export_symbols",
    "swig_opts",
    "depends"
])


# A simplified RE for this; just checks that the line ends with version
# predicates in ()
_VERSION_SPEC_RE = re.compile(r'\s*(.*?)\s*\((.*)\)\s*$')


def setup_cfg_to_setup(path='setup.cfg'):
    """
    Reads given setup.cfg file and returns keyword arguments to setup().

    Also installs plugins and patches to distutils as needed to support some
    of the features supported by setup.cfg (pre/post-command hooks, etc.)
    """

    # The method source code really starts here.
    parser = RawConfigParser()
    if not os.path.exists(path):
        raise DistutilsFileError("file '%s' does not exist" %
                                 os.path.abspath(path))
    parser.read(path)
    config = {}
    for section in parser.sections():
        config[section] = dict(parser.items(section))

    # Run setup_hooks, if configured
    setup_hooks = has_get_option(config, 'global', 'setup_hooks')
    package_dir = has_get_option(config, 'files', 'packages_root')

    # Add the source package directory to sys.path in case it contains
    # additional hooks, and to make sure it's on the path before any existing
    # installations of the package
    if package_dir:
        package_dir = os.path.abspath(package_dir)
        sys.path.insert(0, package_dir)

    try:
        if setup_hooks:
            setup_hooks = split_multiline(setup_hooks)
            for hook in setup_hooks:
                hook_fn = resolve_name(hook)
                try :
                    hook_fn(config)
                except SystemExit:
                    log.error('setup hook %s terminated the installation')
                except:
                    e = sys.exc_info()[1]
                    log.error('setup hook %s raised exception: %s\n' %
                              (hook, e))
                    log.error(traceback.format_exc())
                    sys.exit(1)

        kwargs = process_config(config)

        register_custom_compilers(config)

        ext_modules = get_extension_modules(config)
        if ext_modules:
            kwargs['ext_modules'] = ext_modules

        entry_points = get_entry_points(config)
        if entry_points:
            kwargs['entry_points'] = entry_points

        wrap_commands(kwargs)

        # Handle the [files]/extra_files option
        extra_files = has_get_option(config, 'files', 'extra_files')
        if extra_files:
            extra_files = split_multiline(extra_files)
            # Let's do a sanity check
            for filename in extra_files:
                if not os.path.exists(filename):
                    raise DistutilsFileError(
                        '%s from the extra_files option in setup.cfg does not '
                        'exist' % filename)

            # Unfortunately the only really sensible way to do this is to
            # monkey-patch the manifest_maker class
            @monkeypatch_method(manifest_maker)
            def add_defaults(self, extra_files=extra_files, log=log):
                log.info('[setup.cfg] running patched manifest_maker command '
                          'with extra_files support')
                add_defaults._orig(self)
                self.filelist.extend(extra_files)

    finally:
        # Perform cleanup if any paths were added to sys.path
        if package_dir:
            sys.path.pop(0)

    return kwargs


def process_config(config):
    """
    Processes the setup.cfg options and converts them to arguments accepted by
    setuptools' setup() function.
    """

    kwargs = {}

    for arg in SETUP_ARGS_TO_CFG:
        if len(SETUP_ARGS_TO_CFG[arg]) == 2:
            # The distutils field name is different than distutils2's.
            section, option = SETUP_ARGS_TO_CFG[arg]

        elif len(SETUP_ARGS_TO_CFG[arg]) == 1:
            # The distutils field name is the same thant distutils2's.
            section, option = SETUP_ARGS_TO_CFG[arg][0], arg

        in_cfg_value = has_get_option(config, section, option)
        if not in_cfg_value:
            # There is no such option in the setup.cfg
            if arg == "long_description":
                in_cfg_value = has_get_option(config, section,
                                              "description_file")
                if in_cfg_value:
                    in_cfg_value = split_multiline(in_cfg_value)
                    value = ''
                    for filename in in_cfg_value:
                        description_file = open(filename)
                        try:
                            value += description_file.read().strip() + '\n\n'
                        finally:
                            description_file.close()
                    in_cfg_value = value
            else:
                continue

        if arg in CSV_FIELDS:
            in_cfg_value = split_csv(in_cfg_value)
        if arg in MULTI_FIELDS:
            in_cfg_value = split_multiline(in_cfg_value)
        elif arg in BOOL_FIELDS:
            # Provide some flexibility here...
            if in_cfg_value.lower() in ('true', 't', '1', 'yes', 'y'):
                in_cfg_value = True
            else:
                in_cfg_value = False

        if in_cfg_value:
            if arg in ('install_requires', 'tests_require'):
                # Replaces PEP345-style version specs with the sort expected by
                # setuptools
                in_cfg_value = [_VERSION_SPEC_RE.sub(r'\1\2', pred)
                                for pred in in_cfg_value]
            elif arg == 'package_dir':
                in_cfg_value = {'': in_cfg_value}
            elif arg in ('package_data', 'data_files'):
                data_files = {}
                firstline = True
                prev = None
                for line in in_cfg_value:
                    if '=' in line:
                        key, value = line.split('=', 1)
                        key, value = (key.strip(), value.strip())
                        if key in data_files:
                            # Multiple duplicates of the same package name;
                            # this is for backwards compatibility of the old
                            # format prior to d2to1 0.2.6.
                            prev = data_files[key]
                            prev.extend(value.split())
                        else:
                            prev = data_files[key.strip()] = value.split()
                    elif firstline:
                        raise DistutilsOptionError(
                            'malformed package_data first line %r (misses '
                            '"=")' % line)
                    else:
                        prev.extend(line.strip().split())
                    firstline = False
                if arg == 'data_files':
                    # the data_files value is a pointlessly different structure
                    # from the package_data value
                    data_files = list(data_files.items())
                in_cfg_value = data_files
            elif arg == 'cmdclass':
                cmdclass = {}
                dist = Distribution()
                for cls in in_cfg_value:
                    cls = resolve_name(cls)
                    cmd = cls(dist)
                    cmdclass[cmd.get_command_name()] = cls
                in_cfg_value = cmdclass

        kwargs[arg] = in_cfg_value

    return kwargs


def register_custom_compilers(config):
    """Handle custom compilers; this has no real equivalent in distutils, where
    additional compilers could only be added programmatically, so we have to
    hack it in somehow.
    """

    compilers = has_get_option(config, 'global', 'compilers')
    if compilers:
        compilers = split_multiline(compilers)
        for compiler in compilers:
            compiler = resolve_name(compiler)

            # In distutils2 compilers these class attributes exist; for
            # distutils1 we just have to make something up
            if hasattr(compiler, 'name'):
                name = compiler.name
            else:
                name = compiler.__name__
            if hasattr(compiler, 'description'):
                desc = compiler.description
            else:
                desc = 'custom compiler %s' % name

            module_name = compiler.__module__
            # Note; this *will* override built in compilers with the same name
            # TODO: Maybe display a warning about this?
            cc = distutils.ccompiler.compiler_class
            cc[name] = (module_name, compiler.__name__, desc)

            # HACK!!!!  Distutils assumes all compiler modules are in the
            # distutils package
            sys.modules['distutils.' + module_name] = sys.modules[module_name]


def get_extension_modules(config):
    """Handle extension modules"""

    ext_modules = []
    for section in config:
        if ':' in section:
            labels = section.split(':', 1)
        else:
            # Backwards compatibility for old syntax; don't use this though
            labels = section.split('=', 1)
        labels = [l.strip() for l in labels]
        if (len(labels) == 2) and (labels[0] == 'extension'):
            ext_args = {}
            for field in EXTENSION_FIELDS:
                value = has_get_option(config, section, field)
                # All extension module options besides name can have multiple
                # values
                if not value:
                    continue
                value = split_multiline(value)
                if field == 'define_macros':
                    macros = []
                    for macro in value:
                        macro = macro.split('=', 1)
                        if len(macro) == 1:
                            macro = (macro[0].strip(), None)
                        else:
                            macro = (macro[0].strip(), macro[1].strip())
                        macros.append(macro)
                    value = macros
                ext_args[field] = value
            if ext_args:
                if 'name' not in ext_args:
                    ext_args['name'] = labels[1]
                ext_modules.append(Extension(ext_args.pop('name'),
                                             **ext_args))
    return ext_modules


def get_entry_points(config):
    """Process the [entry_points] section of setup.cfg to handle setuptools
    entry points.  This is, of course, not a standard feature of
    distutils2/packaging, but as there is not currently a standard alternative
    in packaging, we provide support for them.
    """

    if not 'entry_points' in config:
        return {}

    return dict((option, split_multiline(value))
                for option, value in config['entry_points'].items())


def wrap_commands(kwargs):
    dist = Distribution()

    # This should suffice to get the same config values and command classes
    # that the actual Distribution will see (not counting cmdclass, which is
    # handled below)
    dist.parse_config_files()

    for cmd, _ in dist.get_command_list():
        hooks = {}
        for opt, val in dist.get_option_dict(cmd).items():
            val = val[1]
            if opt.startswith('pre_hook.') or opt.startswith('post_hook.'):
                hook_type, alias = opt.split('.', 1)
                hook_dict = hooks.setdefault(hook_type, {})
                hook_dict[alias] = val
        if not hooks:
            continue

        if 'cmdclass' in kwargs and cmd in kwargs['cmdclass']:
            cmdclass = kwargs['cmdclass'][cmd]
        else:
            cmdclass = dist.get_command_class(cmd)

        new_cmdclass = wrap_command(cmd, cmdclass, hooks)
        kwargs.setdefault('cmdclass', {})[cmd] = new_cmdclass


def wrap_command(cmd, cmdclass, hooks):
    def run(self, cmdclass=cmdclass):
        self.run_command_hooks('pre_hook')
        cmdclass.run(self)
        self.run_command_hooks('post_hook')

    return type(cmd, (cmdclass, object),
                {'run': run, 'run_command_hooks': run_command_hooks,
                 'pre_hook': hooks.get('pre_hook'),
                 'post_hook': hooks.get('post_hook')})


def run_command_hooks(cmd_obj, hook_kind):
    """Run hooks registered for that command and phase.

    *cmd_obj* is a finalized command object; *hook_kind* is either
    'pre_hook' or 'post_hook'.
    """

    if hook_kind not in ('pre_hook', 'post_hook'):
        raise ValueError('invalid hook kind: %r' % hook_kind)

    hooks = getattr(cmd_obj, hook_kind, None)

    if hooks is None:
        return

    for hook in hooks.values():
        if isinstance(hook, str):
            try:
                hook_obj = resolve_name(hook)
            except ImportError:
                err = sys.exc_info()[1] # For py3k
                raise DistutilsModuleError('cannot find hook %s: %s' %
                                           (hook,err))
        else:
            hook_obj = hook

        if not hasattr(hook_obj, '__call__'):
            raise DistutilsOptionError('hook %r is not callable' % hook)

        log.info('running %s %s for command %s',
                 hook_kind, hook, cmd_obj.get_command_name())

        try :
            hook_obj(cmd_obj)
        except:
            e = sys.exc_info()[1]
            log.error('hook %s raised exception: %s\n' % (hook, e))
            log.error(traceback.format_exc())
            sys.exit(1)
