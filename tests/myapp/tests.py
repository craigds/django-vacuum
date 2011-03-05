import collections
import logging

from django.test import TestCase

from tc.loading import gen_all_templates
from tc.checker import TemplateChecker, Rule

class TestLoading(TestCase):
    def test_app_directories_loader(self):
        templates = [tupl[0] for tupl in gen_all_templates()]
        self.assertTrue('base1.html' in templates)
        self.assertTrue('extends1.html' in templates)


class TemplatesTestCase(TestCase):
    
    def setUp(self):
        self.log_levels = []
        self.log_messages = []
        self.log_nodes = []
        
        # patch Rule so we know what's logged
        original_rule_log = Rule._log
        def _rule_log(rule, level, node, message):
            self.log_levels.append(level)
            self.log_messages.append(message)
            self.log_nodes.append(node)
            original_rule_log(rule, level, node, message)
        Rule._log = _rule_log
        
        self.checker = TemplateChecker()

class TestBaseBlocks(TemplatesTestCase):
    def test_happy_templates(self):
        for t in ['base1.html', 'extends1.html']:
            self.checker.check_template(t)
        
        self.assertEqual(self.log_levels, [])

    def test_extends_template_extra_bits(self):
        self.checker.check_template('extends1-badblocks.html')
        
        self.assertEqual(self.log_levels, [logging.WARN])
