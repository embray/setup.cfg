#!/usr/bin/env python
try:
    from setuptools import setup
except ImportError:
    from ez_setup import use_setuptools
    use_setuptools()
    from setuptools import setup

# setup.cfg basically installs itself!  See setup.cfg for the project metadata.
from setup.cfg import setup_cfg_to_setup


setup(**setup_cfg_to_setup())
