import json
from pathlib import Path
import sys
import unittest
import yaml

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'app'))
from models import MODELS, options


class ManifestTests(unittest.TestCase):
    def test_options_and_bilingual_configuration_match(self):
        config=yaml.safe_load((ROOT/'config.yaml').read_text())
        self.assertEqual(config['version'],'0.1.0')
        self.assertEqual(set(config['options']),set(config['schema']))
        self.assertEqual(set(config['schema']['model'][5:-1].split('|')),set(MODELS))
        en=yaml.safe_load((ROOT/'translations/en.yaml').read_text())
        ru=yaml.safe_load((ROOT/'translations/ru.yaml').read_text())
        self.assertEqual(set(en['configuration']),set(config['options']))
        self.assertEqual(set(en['configuration']),set(ru['configuration']))
        self.assertEqual(set(en['network']),set(config['ports']))
        self.assertEqual(set(en['network']),set(ru['network']))
        for key in config['options']:
            for language in (en,ru):
                self.assertTrue(language['configuration'][key]['name'])
                self.assertTrue(language['configuration'][key]['description'])

    def test_runtime_versions_and_notices_are_explicit(self):
        import importlib.metadata
        self.assertEqual(importlib.metadata.version('vosk'),'0.3.45')
        self.assertEqual(importlib.metadata.version('wyoming'),'1.5.2')
        for name in ('VOSK-APACHE-2.0.txt','WYOMING-MIT.txt','WYOMING-VOSK-MIT.txt'):
            self.assertTrue((ROOT/'licenses'/name).is_file())
