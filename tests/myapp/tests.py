import collections
import logging

from django.template import Template
from django.test import TestCase

from tc.loading import gen_all_templates
from tc import checker

class TestLoading(TestCase):
    def test_app_directories_loader(self):
        templates = [tupl[0] for tupl in gen_all_templates()]
        self.assertTrue('base1.html' in templates)
        self.assertTrue('extends1.html' in templates)


class TemplatesTestCase(TestCase):
    rules = None
    
    def setUp(self):
        self.log_levels = []
        self.log_messages = []
        self.log_nodes = []
        
        # patch Rule so we know what's logged
        original_rule_log = checker.Rule._log
        def _rule_log(rule, level, node, message):
            self.log_levels.append(level)
            self.log_messages.append(message)
            self.log_nodes.append(node)
            original_rule_log(rule, level, node, message)
        checker.Rule._log = _rule_log
        
        self.checker = checker.TemplateChecker()
        
        # override rules
        if self.rules is not None:
            self.checker.registered_rules = self.rules

class TestBaseBlocks(TemplatesTestCase):
    rules = [
        checker.TextOutsideBlocksInExtended, checker.RootLevelBlockTagsInExtended
    ]
    def test_happy_templates(self):
        for t in ['base1.html', 'extends1.html']:
            self.checker.check_template(t)
        
        self.assertEqual(self.log_levels, [])

    def test_extends_template_extra_bits(self):
        self.checker.check_template('extends1-badblocks.html')
        
        self.assertEqual(self.log_levels, [logging.WARN])
    
    def test_bad_root_level_block(self):
        self.checker.check_template(Template("""
            {% extends "base1.html" %}
            {% block nonexistent %}this is bad{% endblock %}
        """))
        self.assertEqual(self.log_levels, [logging.WARN])
