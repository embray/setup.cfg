"""Miscellaneous utilities."""

import re

from collections import defaultdict


def resolve_name(name):
    """Resolve a name like ``module.object`` to an object and return it.

    Raise ImportError if the module or name is not found.
    """

    parts = name.split('.')
    cursor = len(parts) - 1
    module_name = parts[:cursor]
    attr_name = parts[-1]

    while cursor > 0:
        try:
            ret = __import__('.'.join(module_name), fromlist=[attr_name])
            break
        except ImportError:
            if cursor == 0:
                raise
            cursor -= 1
            module_name = parts[:cursor]
            attr_name = parts[cursor]
            ret = ''

    for part in parts[cursor:]:
        try:
            ret = getattr(ret, part)
        except AttributeError:
            raise ImportError(name)

    return ret


def has_get_option(config, section, option):
    if section in config and option in config[section]:
        return config[section][option]
    elif section in config and option.replace('_', '-') in config[section]:
        return config[section][option.replace('_', '-')]
    else:
        return False


def split_multiline(value):
    """Special behaviour when we have a multi line options"""

    value = [element for element in
             (line.strip() for line in value.split('\n'))
             if element]
    return value


def split_csv(value):
    """Special behaviour when we have a comma separated options"""

    value = [element for element in
             (chunk.strip() for chunk in value.split(','))
             if element]
    return value


class MonkeyPatcher(object):
    def __init__(self):
        self._patched = set()

    def __call__(self, cls):
        """
        A function decorator to monkey-patch a method of the same name on the
        given class.
        """

        def wrapper(func):
            orig = getattr(cls, func.__name__, None)
            if hasattr(orig, '_orig'):  # Already patched
                return orig

            func._orig = orig
            setattr(cls, func.__name__, func)
            self._patched.add((cls, orig))

            return func

        return wrapper

    def unpatch_all(self):
        """
        Remove all monkey-patches.
        """

        for cls, func in self._patched:
            setattr(cls, func.__name__, func)

        self._patched.clear()


monkeypatch_method = MonkeyPatcher()


# The following classes are used to hack Distribution.command_options a bit
class DefaultGetDict(defaultdict):
    """Like defaultdict, but the get() method also sets and returns the default
    value.
    """

    def get(self, key, default=None):
        if default is None:
            default = self.default_factory()
        return super(DefaultGetDict, self).setdefault(key, default)


class IgnoreDict(dict):
    """A dictionary that ignores any insertions in which the key is a string
    matching any string in `ignore`.  The ignore list can also contain wildcard
    patterns using '*'.
    """

    def __init__(self, ignore):
        self.__ignore = re.compile(r'(%s)' % ('|'.join(
                                   [pat.replace('*', '.*')
                                    for pat in ignore])))

    def __setitem__(self, key, val):
        if self.__ignore.match(key):
            return
        super(IgnoreDict, self).__setitem__(key, val)
