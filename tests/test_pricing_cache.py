import copy, fcntl, json, os, runpy, subprocess, tempfile, unittest
from pathlib import Path
from unittest.mock import patch

api = runpy.run_path(str(Path(__file__).resolve().parents[1] / 'bin' / 'usage'))
cache = api['cached_pricing']
g = cache.__globals__
CATALOGS = {'litellm': {'gpt-test': {'input_cost_per_token': .000002, 'output_cost_per_token': .000008}},
            'models.dev': {'openai': {'models': {'gpt-test': {'cost': {'input': 3, 'output': 9}}}}}}

class CacheTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.directory = Path(self.temp.name).resolve()
        self.calls = []
        self.now = 2_000_000_000
        def report(command, **kwargs):
            name = next(name for name, url in api['PRICE_URLS'].items() if url == command[-1] or (name == 'litellm' and 'cdn.jsdelivr.net/' in command[-1]))
            self.calls.append(name)
            return subprocess.CompletedProcess(command, 0, json.dumps(CATALOGS[name]), '')
        self.report = report
        self.p = patch.dict(g, run_report=report)
        self.p.start()
        self.clock = patch.object(g['time'], 'time', lambda: self.now)
        self.clock.start()
    def tearDown(self):
        self.clock.stop(); self.p.stop(); self.temp.cleanup()
    def get(self, **kwargs):
        return cache(cache_dir=self.directory, **kwargs)
    def test_initial_fresh_expired_force_offline(self):
        prices, _ = self.get()
        self.assertEqual(prices['gpt-test']['inputCostPerToken'], .000002)
        self.assertEqual(len(self.calls), 2)
        self.get(); self.assertEqual(len(self.calls), 2)
        self.now += 7 * 86400 + 1
        self.get(offline=True); self.assertEqual(len(self.calls), 2)
        self.get(); self.assertEqual(len(self.calls), 4)
        self.get(force=True); self.assertEqual(len(self.calls), 6)
    def test_failures_keep_prices_and_backoff(self):
        prices, _ = self.get()
        self.now += 7 * 86400 + 1
        def failure(*a, **k): self.calls.append('fail'); raise subprocess.TimeoutExpired('curl', 4)
        g['run_report'] = failure
        self.assertEqual(self.get()[0], prices)
        count = len(self.calls)
        self.get(); self.assertEqual(len(self.calls), count)
        self.now += 6 * 3600 + 1
        self.get(); self.assertEqual(len(self.calls), count + 3)
    def test_bad_response_not_success(self):
        g['run_report'] = lambda *a, **k: subprocess.CompletedProcess([], 0, '{}', '')
        self.get()
        state = json.loads((self.directory / 'pricing.json').read_text())
        self.assertTrue(all('updated_at' not in v for v in state['sources'].values()))
    def test_concurrent_refresh_does_not_wait(self):
        with (self.directory / 'refresh.lock').open('a') as lock:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
            self.get()
        self.assertEqual(self.calls, [])
    def test_temporary_config_cleanup_and_user_priority(self):
        current = Path.cwd()
        try:
            os.chdir(self.directory)
            Path('.ccusage').mkdir()
            Path('.ccusage/ccusage.json').write_text(json.dumps({'defaults': {'timezone': 'Asia/Shanghai', 'pricingOverrides': {'gpt-test': {'inputCostPerToken': .123}}}}))
            filename = None
            with self.assertRaises(RuntimeError):
                with api['pricing_config']({'gpt-test': {'inputCostPerToken': .456, 'outputCostPerToken': .789}}) as filename:
                    config = json.loads(Path(filename).read_text())
                    self.assertEqual(config['defaults']['timezone'], 'Asia/Shanghai')
                    self.assertEqual(config['defaults']['pricingOverrides']['gpt-test']['inputCostPerToken'], .123)
                    self.assertEqual(config['defaults']['pricingOverrides']['gpt-test']['outputCostPerToken'], .789)
                    raise RuntimeError('simulate interrupted report')
            self.assertFalse(Path(filename).exists())
        finally: os.chdir(current)
    def test_invalid_prices_ignored(self):
        prices = api['catalog_prices']('litellm', {'bad': {'input_cost_per_token': -1, 'output_cost_per_token': 2}})
        self.assertEqual(prices, {})

if __name__ == '__main__':
    unittest.main()
