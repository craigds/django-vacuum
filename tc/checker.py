import logging

from django.template import loader, base, loader_tags, defaulttags

class TemplateChecker(object):
    registered_rules = []
    
    def __init__(self):
        self.warnings = []
        self.errors = []
    
    def check_template(self, path):
        """
        Checks the given template for badness.
        """
        try:
            template = loader.get_template(path)
        except (base.TemplateSyntaxError, base.TemplateDoesNotExist), e:
            self.errors.append(e)
            return
        
        rules = [r(self, template) for r in self.registered_rules]
    
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
                if rule.visit_node(node) is False:
                    valid = False
                    rule.log(node)
            if valid and children:
                self._recursive_check(children, ancestors+[node], rules)
    
    def _log(self, level, node, message):
        # TODO get line number of node in template somehow
        logging.log(level, message)
    
    def info(self, node, message):
        self._log(logging.INFO, node, message)
    
    def warn(self, node, message):
        self.warnings.append(message)
        self._log(logging.WARN, node, message)
    
    def error(self, node, message):
        self.errors.append(message)
        self._log(logging.ERROR, node, message)


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

class Rule(object):
    """
    Determines when a node is legal and when it isn't.
    Nodes are visited in a breadth-first fashion.
    """
    __metaclass__ = RuleMeta
    def __init__(self, checker, template):
        """
        Create a Rule for the given checker and template.
        """
        self._info = {}
        self.checker = checker
        self.template = template
    
    def visit_node(self, node):
        """
        Returns whether a node is valid in the current context.
        If False, the node's children will not be processed.
        """
        return None
    
    def log(self, node):
        """
        Must be implemented to log an error or warning for the node.
        This is only called if visit_node() returns False.
        """
        raise NotImplementedError


### RULES - actual rules

class TextOutsideBlocksInExtended(Rule):
    """
    No point having text nodes outside of blocks in extended templates.
    """
    def visit_node(self, node):
        if isinstance(node, loader_tags.ExtendsNode):
            self._info['extends_node'] = node
        elif self._info.get('extends_node'):
            if not isinstance(node, (loader_tags.BlockNode, defaulttags.LoadNode, defaulttags.CommentNode)):
                if node.parent == self._info['extends_node']:
                    return False
    
    def log(self, node):
        self.checker.warn(node, 'Text outside of blocks in extended template')
