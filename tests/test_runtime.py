import ctypes
import importlib.util
import os
from pathlib import Path
import runpy
import subprocess
import sys
import tempfile
import threading
import time
import unittest

ROOT = Path(__file__).resolve().parents[1]
api = runpy.run_path(str(ROOT / 'bin' / 'usage'))
installer = runpy.run_path(str(ROOT / 'install.py'))


def alive(pid):
    if os.name == 'nt':
        from ctypes import wintypes
        kernel = ctypes.WinDLL('kernel32', use_last_error=True)
        kernel.OpenProcess.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]
        kernel.OpenProcess.restype = wintypes.HANDLE
        kernel.WaitForSingleObject.argtypes = [wintypes.HANDLE, wintypes.DWORD]
        kernel.CloseHandle.argtypes = [wintypes.HANDLE]
        handle = kernel.OpenProcess(0x100000, False, pid)
        if not handle:
            return False
        try:
            return kernel.WaitForSingleObject(handle, 0) == 258
        finally:
            kernel.CloseHandle(handle)
    try:
        os.kill(pid, 0)
        return True
    except ProcessLookupError:
        return False


class RuntimeTests(unittest.TestCase):
    def test_capture_both_pipes(self):
        result = api['run_report']([sys.executable, '-c', 'import sys; print("hello"); print("error", file=sys.stderr)'])
        self.assertEqual(result.returncode, 0)
        self.assertEqual(result.stdout.strip(), 'hello')
        self.assertEqual(result.stderr.strip(), 'error')

    def test_timeout_and_output_limit_release_threads(self):
        before = set(threading.enumerate())
        with self.assertRaises(subprocess.TimeoutExpired):
            api['run_report']([sys.executable, '-c', 'import time; time.sleep(30)'], timeout=.5)
        with self.assertRaises(RuntimeError):
            api['run_report']([sys.executable, '-c', 'print("x" * 100000)'], output_limit=100)
        self.assertEqual(set(threading.enumerate()), before)

    def test_descendant_cleaned_after_launcher_exit(self):
        with tempfile.TemporaryDirectory() as directory:
            pidpath = Path(directory) / 'pid'
            child = 'import os,time; from pathlib import Path; Path(' + repr(str(pidpath)) + ').write_text(str(os.getpid())); time.sleep(30)'
            parent = 'import subprocess,sys,time; from pathlib import Path; subprocess.Popen([sys.executable,"-c",sys.argv[1]],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL); p=Path(sys.argv[2]);\nwhile not p.exists(): time.sleep(.01)'
            api['run_report']([sys.executable, '-c', parent, child, str(pidpath)], timeout=10)
            pid = int(pidpath.read_text())
            deadline = time.monotonic() + 3
            while alive(pid) and time.monotonic() < deadline:
                time.sleep(.02)
            self.assertFalse(alive(pid), 'Descendant was left running')

    def test_install_conflict_and_launcher_arguments(self):
        with tempfile.TemporaryDirectory(prefix='usage test ') as directory:
            target = Path(directory) / 'bin with spaces'
            launcher = installer['install'](target)
            command = [str(launcher), '--help'] if os.name != 'nt' else f'"{launcher}" --help'
            result = subprocess.run(command, shell=os.name == 'nt', capture_output=True, text=True, encoding='utf-8', timeout=15)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn('--details', result.stdout)
            (target / 'usage.py').write_text('unrelated file')
            with self.assertRaises(RuntimeError):
                installer['install'](target)
            installer['install'](target, force=True)
            self.assertEqual((target / 'usage.py').read_bytes(), (ROOT / 'bin' / 'usage').read_bytes())


if __name__ == '__main__':
    unittest.main()
