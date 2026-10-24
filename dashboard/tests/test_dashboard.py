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
            [sys.executable, 'dashboard/server.py', '--port', str(cls.port)],
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

    def test_unranked_semiperennial_is_never_shown_as_next_recommendation(self):
        self.page.locator('#alternatives-list .alternative').filter(has_text='Frijol de palo').click()
        card = self.page.locator('#recommendation-card').inner_text().lower()
        self.assertIn('cultivo explorado · sin puesto', card)
        self.assertIn('fuera del ranking', card)
        self.assertIn('semiperenne', card)
        self.assertNotIn('podría seguir', card)

    def test_local_crop_catalog_and_basin_soil_classes_render(self):
        self.assertIn('80 de 80 cultivos registrados', self.page.locator('#drap-crop-count').inner_text())
        self.page.select_option('#soil-region-select', 'cuencas')
        self.assertEqual(self.page.locator('#soil-cards .soil-card').count(), 3)
        self.assertEqual(self.page.locator('#soil-cards tbody tr').count(), 22)

    def test_all_drap_crops_are_selectable_without_reusing_an_unrelated_ranking(self):
        self.assertEqual(self.page.locator('#previous-select option').count(), 81)
        mango = self.page.locator('#previous-select option').filter(has_text='Mango · ficha agronómica')
        self.page.select_option('#previous-select', mango.get_attribute('value'))
        card = self.page.locator('#recommendation-card').inner_text()
        self.assertIn('Mango', card)
        self.assertIn('se puede evaluar con tus datos', card)
        self.assertNotIn('Caupí', card)
        self.assertTrue(self.page.locator('#comparar').is_hidden())

    def test_soil_unit_can_be_selected_from_the_starting_panel(self):
        self.page.select_option('#soil-unit-select', 'Cerezal')
        self.assertIn('Cerezal', self.page.locator('#soil-selection-summary').inner_text())
        self.assertIn('Regosol', self.page.locator('#soil-selection-summary').inner_text())
        self.assertEqual(self.page.locator('#soil-cards .soil-card').count(), 1)
        self.page.select_option('#soil-condition-select', 'agrietado')
        self.assertIn('por confirmar', self.page.locator('#soil-selection-summary').inner_text())

    def test_live_motor_ranks_candidates_from_user_inputs(self):
        mango = self.page.locator('#previous-select option').filter(has_text='Mango · ficha agronómica')
        self.page.select_option('#previous-select', mango.get_attribute('value'))
        self.page.select_option('#soil-unit-select', 'Cerezal')
        self.page.select_option('#soil-condition-select', 'arenoso')
        self.page.fill('#live-water', '20000')
        self.page.fill('#live-budget', '50000')
        self.page.locator('.advanced-inputs > summary').click()
        self.page.fill('#live-efficiency', '0.75')
        self.page.fill('#live-fertilizer-n', '80')
        self.page.locator('#run-live-model').click()
        self.page.wait_for_function("!document.querySelector('#live-results').hidden")
        self.assertIn('Siguiente mejor:', self.page.locator('#live-results-title').inner_text())
        self.assertGreaterEqual(self.page.locator('#live-ranking .live-candidate').count(), 3)
        self.assertIn('Cómo se ordenó:', self.page.locator('#live-notes').inner_text())
        self.assertIn('Cerezal', self.page.locator('#live-results-summary').inner_text())
        self.assertIn('arenoso', self.page.locator('#live-results-summary').inner_text())
        self.assertEqual(self.page.locator('#live-ranking .rank-bubble').all_text_contents()[:3], ['1', '2', '3'])

    def test_no_history_is_a_calculable_scenario_not_a_sample_parcel(self):
        self.page.select_option('#previous-select', '__unregistered__')
        self.assertIn('Sin cultivo anterior especificado', self.page.locator('#recommendation-card').inner_text())
        self.assertTrue(self.page.locator('#example-picker').is_hidden())
        self.page.fill('#live-water', '20000')
        self.page.locator('#run-live-model').click()
        self.page.wait_for_function("!document.querySelector('#live-results').hidden")
        self.assertIn('sin historial', self.page.locator('#live-results-summary').inner_text().lower())

    def test_evidence_loaded_on_demand(self):
        self.assertTrue(self.page.locator('#evidence-content').is_hidden())
        self.page.locator('#load-evidence').click()
        self.page.wait_for_function("document.querySelector('#evidence-count')?.textContent.includes('filas encontradas')", timeout=30000)
        self.assertIn('17,150', self.page.locator('#evidence-count').inner_text())
        self.page.locator('#evidence-query').fill('salinidad')
        self.page.wait_for_timeout(300)
        self.assertGreater(self.page.locator('#evidence-table tr').count(), 0)

    def test_standalone_bundles_charts_and_evidence(self):
        requests = []
        self.page.on('request', lambda request: requests.append(request.url))
        self.page.goto(f'http://127.0.0.1:{self.port}/dashboard/standalone.html')
        self.page.wait_for_selector('#margin-chart svg')
        self.page.locator('#load-evidence').click()
        self.page.wait_for_function("document.querySelector('#evidence-count')?.textContent.includes('filas encontradas')", timeout=30000)
        local_requests = [url for url in requests if url.startswith(f'http://127.0.0.1:{self.port}/')]
        self.assertEqual(local_requests, [f'http://127.0.0.1:{self.port}/dashboard/standalone.html'])
        self.assertIn('17,150', self.page.locator('#evidence-count').inner_text())


if __name__ == '__main__':
    unittest.main()
