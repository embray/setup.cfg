try:
    __version__ = __import__('pkg_resources').get_distribution('setup.cfg').version
except:
    __version__ = ''
