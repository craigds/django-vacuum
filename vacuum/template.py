
__all__ = ()

import django

# Django 1.3 exposes line numbers to tokenizer. <1.3 doesn't, so we ignore line numbers
if django.VERSION >= (1, 3):
    # monkey-patch django template so it uses our custom parser to record node line numbers
    
    from django.conf import settings
    from django import template
    from django.template.debug import DebugLexer, DebugParser
    
    if settings.TEMPLATE_DEBUG:
        lexer_class, parser_class = DebugLexer, DebugParser
    else:
        lexer_class, parser_class = template.Lexer, template.Parser
    
    class LineNumberParser(parser_class):
        """
        Just like a regular parser but records node line numbers
        """
        def extend_nodelist(self, nodelist, node, token):
            if hasattr(token, 'lineno'):
                node.lineno = token.lineno
            super(LineNumberParser, self).extend_nodelist(nodelist, node, token)
    
    def compile_string(template_string, origin):
        """
        Compiles template_string into NodeList ready for rendering
        
        Just like django.template.base.compile_string(), but this one records the
        line number for each node.
        """
        lexer = lexer_class(template_string, origin)
        parser = LineNumberParser(lexer.tokenize())
        return parser.parse()
    
    template.compile_string = compile_string
