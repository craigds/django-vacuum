import logging

from django.template import loader, base, loader_tags, defaulttags, Template

class TemplateChecker(object):
    registered_rules = []
    
    def check_template(self, template):
        """
        Checks the given template for badness.
        """
        if not isinstance(template, Template):
            try:
                template = loader.get_template(template)
            except (base.TemplateSyntaxError, base.TemplateDoesNotExist), e:
                self.errors.append(e)
                return
        
        rules = [r(template) for r in self.registered_rules]
        
        for rule in rules:
            rule.process_ancestor_templates()
        
        # depth-first search of the template nodes
        #TODO should probably use deque, since we're doing popleft() a lot?
        nodes = template.nodelist
        self._recursive_check(nodes, [], rules)
    
    def _recursive_check(self, nodes, ancestors, rules):
        for node in nodes:
            node.parent = ancestors[-1] if ancestors else None
            children = None
            if isinstance(node, base.TextNode):
                if not node.s.strip():
                    # skip further processing for blank text nodes
                    continue
            elif getattr(node, 'nodelist', None):
                children = node.nodelist
            
            valid = True
            for rule in rules:
                if rule.finished:
                    continue
                if rule.visit_node(node) is False:
                    valid = False
            if valid and children:
                self._recursive_check(children, ancestors+[node], rules)


### RULES - base classes

class RuleMeta(type):
    """
    Automatically register rule classes with TemplateChecker
    """
    def __new__(meta, className, bases, classDict):
        cls = type.__new__(meta, className, bases, classDict)
        try:
            Rule
        except NameError:
            pass
        else:
            TemplateChecker.registered_rules.append(cls)
        return cls

class StopProcessingAncestorTemplate(Exception):
    pass

class Rule(object):
    """
    Determines when a node is legal and when it isn't.
    Nodes are visited in a breadth-first fashion.
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
            children = None
            if getattr(node, 'nodelist', None):
                children = node.nodelist
            
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
        if isinstance(node, base.TextNode):
            return node.s.strip()
        return unicode(node)
    
    def _log(self, level, node, message):
        # TODO get line number of node in template somehow
        logging.log(level, message)
    
    def info(self, node, message):
        self._log(logging.INFO, node, message)
    
    def warn(self, node, message):
        self._log(logging.WARN, node, message)
    
    def error(self, node, message):
        self._log(logging.ERROR, node, message)

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

class RootLevelBlockTagsInExtended(Rule):
    """
    If there are root level block tags in an extended template, they should
    also be in a parent template. Otherwise, they'll never be rendered.
    """
    def __init__(self, *args, **kwargs):
        super(RootLevelBlockTagsInExtended, self).__init__(*args, **kwargs)
        self._blocks_in_ancestors = set()
    
    def visit_node_in_ancestor(self, node):
        if isinstance(node, loader_tags.BlockNode):
            self._blocks_in_ancestors.add(node.name)
    
    def visit_node(self, node):
        if self.ancestor_templates:
            if isinstance(node, loader_tags.BlockNode) and isinstance(node.parent, loader_tags.ExtendsNode):
                if node.name not in self._blocks_in_ancestors:
                    self.warn(node, "Root-level block ('%s') doesn't match any blocks in parent templates" % node.name)
                    return False
