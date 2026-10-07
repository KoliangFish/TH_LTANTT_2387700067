import logging
from pathlib import Path

LOG = logging.getLogger('netrecon')
LOG.setLevel(logging.INFO)
if not LOG.handlers:
    handler = logging.FileHandler(Path(__file__).resolve().parents[1] / 'netrecon.log', encoding='utf-8')
    handler.setFormatter(logging.Formatter('%(asctime)s %(levelname)s %(message)s'))
    LOG.addHandler(handler)
