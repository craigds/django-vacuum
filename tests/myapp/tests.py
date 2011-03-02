from django.test import TestCase

from tc.loading import gen_all_templates

class TestLoading(TestCase):
    def test_app_directories_loader(self):
        templates = [tupl[0] for tupl in gen_all_templates()]
        self.assertTrue('base1.html' in templates)
        self.assertTrue('extends1.html' in templates)