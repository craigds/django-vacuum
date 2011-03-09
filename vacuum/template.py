from django.conf import settings
from django.template.base import Template, Lexer, Parser, StringOrigin, TemplateEncodingError
from django.template.debug import DebugLexer, DebugParser
from django.utils.encoding import smart_unicode

if settings.TEMPLATE_DEBUG:
    lexer_class, parser_class = DebugLexer, DebugParser
else:
    lexer_class, parser_class = Lexer, Parser

class LineNumberParser(parser_class):
    """
    Just like a regular parser but records node line numbers
    """
    def extend_nodelist(self, nodelist, node, token):
        node.lineno = token.lineno
        super(LineNumberParser, self).extend_nodelist(nodelist, node, token)

def _compile_string(template_string, origin):
    """
    Compiles template_string into NodeList ready for rendering
    
    Just like django.template.base.compile_string(), but this one records the
    line number for each node.
    """
    lexer = lexer_class(template_string, origin)
    parser = LineNumberParser(lexer.tokenize())
    return parser.parse()

# monkey-patch Template so it uses custom parser to record node line numbers
def template_init(self, template_string, origin=None, name='<Unknown Template>'):
    try:
        template_string = smart_unicode(template_string)
    except UnicodeDecodeError:
        raise TemplateEncodingError("Templates can only be constructed from unicode or UTF-8 strings.")
    if settings.TEMPLATE_DEBUG and origin is None:
        origin = StringOrigin(template_string)
    self.nodelist = _compile_string(template_string, origin)
    self.name = name
Template.__init__ = template_init
