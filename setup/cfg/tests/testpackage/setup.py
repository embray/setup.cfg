#!/usr/bin/env python
try:
    from setuptools import setup
except ImportError:
    from distribute_setup import use_setuptools
    use_setuptools()
    from setuptools import setup

setup(
    setup_requires=['setup.cfg'],
    setup_cfg=True,
)
