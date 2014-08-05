from __future__ import with_statement, unicode_literals

import io
import os
import shutil
import subprocess
import sys
import tempfile
import textwrap

import pkg_resources

from setuptools.sandbox import run_setup

from .util import rmtree, open_config
from ..util import monkeypatch_method


from ..extern import six

if six.PY3:
    StringIO = io.StringIO
else:
    # Use cStringIO on Python 2 to avoid some
    # fussy unicode issues
    import cStringIO
    StringIO = cStringIO.StringIO



SETUP_CFG_DIR = os.path.abspath(
    os.path.join(os.path.dirname(__file__), os.pardir, os.pardir, os.pardir))


def fake_setup_cfg_dist():
    # Fake a setup.cfg distribution from the setup.cfg package that these tests
    # reside in and make sure it's active on the path with the appropriate
    # entry points installed

    class _FakeProvider(pkg_resources.EmptyProvider):
        """A fake metadata provider that does almost nothing except to return
        entry point metadata.
        """

        def has_metadata(self, name):
            return name == 'entry_points.txt'

        def get_metadata(self, name):
            if name == 'entry_points.txt':
                return textwrap.dedent("""\
                    [distutils.setup_keywords]
                    setup_cfg = setup.cfg.core:setup_cfg
                """)
            else:
                return ''


    sys.path.insert(0, SETUP_CFG_DIR)
    if 'setup.cfg' in sys.modules:
        del sys.modules['setup.cfg']
    if 'setup.cfg' in pkg_resources.working_set.by_key:
        del pkg_resources.working_set.by_key['setup.cfg']
    dist = pkg_resources.Distribution(location=SETUP_CFG_DIR,
                                      project_name='setup.cfg',
                                      metadata=_FakeProvider())
    pkg_resources.working_set.add(dist)


class D2to1TestCase(object):
    def setup(self):
        self.temp_dir = tempfile.mkdtemp(prefix='setup.cfg-test-')
        self.package_dir = os.path.join(self.temp_dir, 'testpackage')
        shutil.copytree(os.path.join(os.path.dirname(__file__), 'testpackage'),
                        self.package_dir)
        self.oldcwd = os.getcwd()
        os.chdir(self.package_dir)

    def teardown(self):
        os.chdir(self.oldcwd)
        # Remove setup.cfg.testpackage from sys.modules so that it can be
        # freshly re-imported by the next test
        for k in list(sys.modules):
            if (k == 'setup_cfg_testpackage' or
                k.startswith('setup_cfg_testpackage.')):
                del sys.modules[k]
        rmtree(self.temp_dir)

        # Undo all monkey-patching that occurred during the test
        monkeypatch_method.unpatch_all()

    def run_setup(self, *args):
        old_stdout = sys.stdout
        old_stderr = sys.stderr
        stdout = sys.stdout = StringIO()
        stderr = sys.stderr = StringIO()
        try:
            run_setup('setup.py', args)
            returncode = 0
        except SystemExit as e:
            returncode = e.args[0]
        finally:
            sys.stdout = old_stdout
            sys.stderr = old_stderr

        return (stdout.getvalue().strip(), stderr.getvalue().strip(),
                returncode)

    def run_svn(self, *args):
        return self._run_cmd('svn', args)

    def _run_cmd(self, cmd, args):
        """
        Runs a command, with the given argument list, in the root of the test
        working copy--returns the stdout and stderr streams and the exit code
        from the subprocess.
        """

        os.chdir(self.package_dir)
        p = subprocess.Popen([cmd] + list(args), stdout=subprocess.PIPE,
                             stderr=subprocess.PIPE)

        streams = tuple(s.decode('latin1').strip() for s in p.communicate())
        print(streams)
        return (streams) + (p.returncode,)
