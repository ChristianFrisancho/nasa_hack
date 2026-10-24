"""Browser smoke tests for the most consequential interpretation paths."""
import socket
import subprocess
import sys
import time
import unittest
import shutil
from pathlib import Path
from urllib.request import urlopen

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[2]


class DashboardBrowserTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        with socket.socket() as sock:
            sock.bind(('127.0.0.1', 0))
            cls.port = sock.getsockname()[1]
        cls.server = subprocess.Popen(
            [sys.executable, '-m', 'http.server', str(cls.port), '--bind', '127.0.0.1'],
            cwd=ROOT, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
        )
        for _ in range(50):
            try:
                urlopen(f'http://127.0.0.1:{cls.port}/dashboard/', timeout=1).close()
                break
            except OSError:
                time.sleep(.1)
        else:
            raise RuntimeError('Local dashboard server did not start')
        cls.playwright = sync_playwright().start()
        system_browser = shutil.which('chromium') or shutil.which('google-chrome')
        cls.browser = cls.playwright.chromium.launch(headless=True, executable_path=system_browser,
                                                      args=['--no-sandbox'])

    @classmethod
    def tearDownClass(cls):
        cls.browser.close()
        cls.playwright.stop()
        cls.server.terminate()
        cls.server.wait(timeout=5)

    def setUp(self):
        self.page = self.browser.new_page(viewport={'width': 1280, 'height': 850})
        self.errors = []
        self.page.on('pageerror', lambda error: self.errors.append(str(error)))
        self.page.goto(f'http://127.0.0.1:{self.port}/dashboard/')
        self.page.wait_for_selector('#margin-chart svg')

    def tearDown(self):
        self.assertEqual(self.errors, [])
        self.page.close()

    def test_rice_to_pea_keeps_agronomic_warning(self):
        card = self.page.locator('#recommendation-card').inner_text()
        self.assertIn('Arroz', card)
        self.assertIn('Arveja', card)
        self.assertIn('floración', card)
        self.assertEqual(self.page.locator('#filter-list .filter-item').count(), 10)
        self.assertEqual(self.page.locator('.alternative').count(), 14)
        self.page.locator('#filter-list .filter-item').filter(has=self.page.locator('summary', has_text='Clima y calendario')).locator('details.technical-details > summary').click()
        self.assertIn('0 ha', self.page.locator('#filter-list').inner_text())

    def test_negative_margin_is_not_presented_as_safe(self):
        self.page.select_option('#parcel-select', 'tablazo_sur_ce_medida')
        card = self.page.locator('#recommendation-card').inner_text()
        self.assertIn('Caupí', card)
        self.assertIn('Pérdida estimada', card)
        self.assertIn('no conviene sembrarla', card.lower())

    def test_no_viable_crop_and_mobile_layout(self):
        self.page.select_option('#parcel-select', 'inviable')
        self.assertIn('ninguno viable', self.page.locator('#recommendation-card').inner_text().lower())
        self.assertEqual(self.page.locator('#margin-chart svg').count(), 0)
        self.page.set_viewport_size({'width': 390, 'height': 844})
        self.assertEqual(self.page.evaluate('document.documentElement.scrollWidth - document.documentElement.clientWidth'), 0)

    def test_evidence_loaded_on_demand(self):
        self.assertTrue(self.page.locator('#evidence-content').is_hidden())
        self.page.locator('#load-evidence').click()
        self.page.wait_for_function("document.querySelector('#evidence-count')?.textContent.includes('filas encontradas')", timeout=30000)
        self.assertIn('17,150', self.page.locator('#evidence-count').inner_text())
        self.page.locator('#evidence-query').fill('salinidad')
        self.page.wait_for_timeout(300)
        self.assertGreater(self.page.locator('#evidence-table tr').count(), 0)


if __name__ == '__main__':
    unittest.main()
