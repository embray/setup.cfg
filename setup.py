#!/usr/bin/env python
try:
    from setuptools import setup as _setup
except ImportError:
    from ez_setup import use_setuptools
    use_setuptools()
    from setuptools import setup as _setup

# setup.cfg basically installs itself!  See setup.cfg for the project metadata.
import setup.cfg


_setup(**setup.cfg.to_setup())
