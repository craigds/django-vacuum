import logging
import os
import re

from django.template import loader_tags, defaulttags, defaultfilters, TextNode

# don't pyflakes this out; it monkey-patches django's Template.
from vacuum import template as _template
from vacuum import utils

registered_rules = []

class RuleMeta(type):
    """
    Automatically register rule classes
    """
    
    def __new__(meta, className, bases, classDict):
        cls = type.__new__(meta, className, bases, classDict)
        try:
            Rule
        except NameError:
            pass
        else:
            registered_rules.append(cls)
        return cls

class StopProcessingAncestorTemplate(Exception):
    pass

class Rule(object):
    """
    Determines when a node is legal and when it isn't.
    """
    __metaclass__ = RuleMeta
    
    def __init__(self, template):
        self.template = template
        self.finished = False
        
        # navigate up the template hierarchy and determine ancestors
        self.ancestor_templates = []
        while True:
            for node in template.nodelist:
                if isinstance(node, loader_tags.ExtendsNode):
                    if not node.parent_name:
                        self.warn(node, "Could determine parent template from extends tag. It might use a context variable.")
                        return
                    template = node.get_parent({})
                    self.ancestor_templates.insert(0, template)
                    break
            else:
                break
    
    def process_ancestor_templates(self):
        for template in self.ancestor_templates:
            try:
                self._recursive_process_ancestor_template(template.nodelist, None)
            except StopProcessingAncestorTemplate:
                pass
    
    def _recursive_process_ancestor_template(self, nodes, parent):
        for node in nodes:
            node.parent = parent
            children = []
            for child_nodelist in getattr(node, 'child_nodelists', []):
                children.extend(getattr(node, child_nodelist, []))
            
            if self.visit_node_in_ancestor(node) is False:
                raise StopProcessingAncestorTemplate
            if children:
                self._recursive_process_ancestor_template(children, node)
    
    def visit_node_in_ancestor(self, node):
        """
        Called for each node in an ancestor template.
        
        If return value is False, processing of the ancestor template will be
        stopped early. Otherwise, the whole ancestor template will be processed.
        
        Ancestor templates are processed from the top down (i.e., base.html will be
        processed before things that extend from it)
        """
        return False
    
    def visit_node(self, node):
        """
        Returns whether a node is valid in the current context.
        If False, the node's children will not be processed.
        This method should also call self.warn/error/etc if it finds anything invalid.
        """
        return None
    
    def format_node(self, node):
        if isinstance(node, TextNode):
            return node.s.strip()
        return unicode(node)
    
    def _log(self, level, node, message, *args, **kwargs):
        # We'll prefix the message with the template name and block and pass
        # through any other arguments which message might use for formatting
        prefix = self.template.name
        if hasattr(node, 'lineno'):
            prefix += ":%d" % node.lineno
        
        logging.log(level, "%s<%s>: %s" % (prefix, node.__class__.__name__, message),
                    extra={"node": node, "template": self.template},
                    *args, **kwargs)
    
    def info(self, node, message, *args, **kwargs):
        self._log(logging.INFO, node, message, *args, **kwargs)
    
    def warn(self, node, message, *args, **kwargs):
        self._log(logging.WARN, node, message, *args, **kwargs)
    
    def error(self, node, message, *args, **kwargs):
        self._log(logging.ERROR, node, message, *args, **kwargs)

### RULES - actual rules

class TextOutsideBlocksInExtended(Rule):
    """
    No point having text nodes outside of blocks in extended templates.
    """
    check_parent_templates = False
    
    def visit_node(self, node):
        if self.ancestor_templates:
            if not isinstance(node, (loader_tags.BlockNode, defaulttags.LoadNode, defaulttags.CommentNode)):
                if isinstance(node.parent, loader_tags.ExtendsNode):
                    self.warn(node, "Text outside of blocks in extended template: '%s'" % self.format_node(node))
                    return False


class NonexistentBlockTagsInExtended(Rule):
    """
    If there are root level block tags in an extended template, they should
    also be in a parent template. Otherwise, they'll never be rendered.

    This includes checks for inheritance of overridden blocks, e.g.:
        base.html:
            {% block foo %}{% block bar %}{% endblock %}{% endblock %}
        one.html:
            {% extends "base.html" %}{% block foo %}{% endblock %}
        two.html:
            {% extends "one.html" %}{% block bar %}{% endblock %}   <-- bad
    """

    def visit_node(self, node):
        if not isinstance(node, loader_tags.BlockNode):
            return

        if not self.ancestor_templates:
            return False

        ancestor_block_names = set()

        for template in self.ancestor_templates:
            names = self._recurse_nodelist(template.nodelist)

            ancestor_block_names.update(names)

            # Remove any blocks which were removed in this template by
            # overriding their containing block:
            for name in ancestor_block_names.difference(names):
                ancestor_block_names.remove(name)

        if node.name not in ancestor_block_names:
            self.warn(node, "Root-level block '%s' doesn't match any blocks in parent templates" % node.name)

        return False

    def _recurse_nodelist(self, nodelist):
        block_nodes = nodelist.get_nodes_by_type(loader_tags.BlockNode)
        names = set(i.name for i in block_nodes)

        for i in nodelist.get_nodes_by_type(loader_tags.ConstantIncludeNode):
            names.update(self._recurse_nodelist(i.template.nodelist))

        return names

class UnescapedAmpersands(Rule):
    html_extensions = set(['.html', '.htm'])
    entity_regex = re.compile(r'&([^\s;]*)')
    entities = set()
    
    @classmethod
    def _load_entities(cls):
        if not cls.entities:
            filepath = os.path.join(os.path.split(__file__)[0], 'entities.txt')
            entities = open(filepath).read().split()
            cls.entities = set(entities)
    
    def __init__(self, *args, **kwargs):
        super(UnescapedAmpersands, self).__init__(*args, **kwargs)
        self._load_entities()
        
        # don't do anything for non-html templates
        name = self.template.name
        if not (name and os.path.splitext(name)[-1].lower() in self.html_extensions):
            self.finished = True
    
    def visit_node(self, node):
        if isinstance(node, TextNode):
            
            notags = defaultfilters.striptags(node.s)
            matches = self.entity_regex.findall(notags)
            for match in matches:
                if match not in self.entities:
                    self.warn(node, "Unescaped entity '%s'" % match)
