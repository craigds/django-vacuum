from django.template import loader, base, Template

from tc.rules import registered_rules

class TemplateChecker(object):
    
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
        
        rules = [r(template) for r in registered_rules]
        
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
