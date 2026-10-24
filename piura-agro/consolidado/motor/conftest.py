import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))


def pytest_configure(config):
    # los tmp_path de los tests van dentro de consolidado/motor/, no a /tmp
    if not config.option.basetemp:
        config.option.basetemp = str(Path(__file__).resolve().parent / ".pytest_tmp")
