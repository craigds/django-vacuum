import logging

from django.template import Template
from django.test import TestCase

from vacuum.loading import gen_all_templates
from vacuum import checker, rules

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
        original_rule_log = rules.Rule._log
        def _rule_log(rule, level, node, message):
            self.log_levels.append(level)
            self.log_messages.append(message)
            self.log_nodes.append(node)
            original_rule_log(rule, level, node, message)
        rules.Rule._log = _rule_log
        
        self.checker = checker.TemplateChecker()
        
        # override rules
        if self.rules is not None:
            self.checker.registered_rules = self.rules

class TestBlocks(TemplatesTestCase):
    rules = [
        rules.TextOutsideBlocksInExtended, rules.NonexistentBlockTagsInExtended
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
            {% extends "base1.html" %}{% block nonexistent %}this is bad{% endblock %}
        """))
        self.assertEqual(self.log_levels, [logging.WARN])
    
    def test_good_root_level_block(self):
        self.checker.check_template(Template("""
            {% extends "base1.html" %}{% block foo %}this is okay{% endblock %}
        """))
        self.assertEqual(self.log_levels, [])

    def test_extending_nonroot_block(self):
        self.checker.check_template(Template("""
            {% extends "base1.html" %}{% block bar %}this is okay{% endblock %}
        """))
        self.assertEqual(self.log_levels, [])

    def test_root_level_overridden_block(self):
        # extends1.html overrides block 'foo', so 'bar' doesnt exist anymore
        self.checker.check_template(Template("""
            {% extends "extends1.html" %}
            {% block bar %}this is bad{% endblock %}
        """))
        self.assertEqual(self.log_levels, [logging.WARN])
