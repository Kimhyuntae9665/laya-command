import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / 'skills/ko-en-command/scripts'
spec = importlib.util.spec_from_file_location('translator', SCRIPTS / 'translate.py')
translator = importlib.util.module_from_spec(spec)
spec.loader.exec_module(translator)


class GuardTests(unittest.TestCase):
    def test_inclusive_and_exclusive_bounds(self):
        text, protected = translator.protect_source('3일 이상, 5회 초과, 10개 이하, 20% 미만')
        self.assertEqual(set(protected), {'at least 3 days', 'more than 5 times',
                                          'at most 10 items', 'less than 20%'})

    def test_backtick_content_is_not_normalized(self):
        literal = '`3일 이상 --no-delete C:/temp/test.txt`'
        text, protected = translator.protect_source(literal)
        self.assertEqual(text, literal)
        self.assertEqual(protected, {})

    def check_rejected_before_model_import(self, translation, message):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'translation.json'
            path.write_text(json.dumps(translation), encoding='utf-8')
            result = subprocess.run([sys.executable, str(SCRIPTS / 'laya_predict.py'),
                                     '--translation', str(path), '--questions', str(Path(tmp) / 'absent.json')],
                                    capture_output=True, text=True)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn(message, result.stderr)
            self.assertNotIn('No module named', result.stderr)

    def test_warning_blocks_handoff(self):
        self.check_rejected_before_model_import({'english': 'Delete it.', 'warnings': ['Negation changed']},
                                                'Resolve translation warnings')

    def test_empty_translation_blocks_handoff(self):
        self.check_rejected_before_model_import({'english': ' ', 'warnings': []}, 'translation is empty')


if __name__ == '__main__':
    unittest.main()
