from django.test import TestCase

from tc.loading import gen_all_templates
from tc.checker import TemplateChecker

class TestLoading(TestCase):
    def test_app_directories_loader(self):
        templates = [tupl[0] for tupl in gen_all_templates()]
        self.assertTrue('base1.html' in templates)
        self.assertTrue('extends1.html' in templates)


class TemplatesTestCase(TestCase):
    def setUp(self):
        self.checker = TemplateChecker()

class TestBaseBlocks(TemplatesTestCase):
    def test_happy_templates(self):
        for t in ['base1.html', 'extends1.html']:
            self.checker.check_template(t)
        
        self.assertEqual(len(self.checker.warnings), 0)
        self.assertEqual(len(self.checker.errors), 0)

    def test_extends_template_extra_bits(self):
        self.checker.check_template('extends1-badblocks.html')
        
        self.assertEqual(len(self.checker.warnings), 1)
        self.assertEqual(len(self.checker.errors), 0)
