import logging
import os

from django.conf import settings
from django.template import loader

__all__ = ('gen_all_templates',)


def gen_all_templates():
    """
    Generator. Finds paths for all the templates accessible through the loaders in TEMPLATE_LOADERS.
    
    Yields tuples: (rel_path, abs_path)
    """
    from django.template.loaders.cached import Loader as CachedLoader
    
    if not loader.template_source_loaders:
        # force the template loaders to populate
        try:
            loader.find_template('foo')
        except loader.TemplateDoesNotExist:
            pass
    
    loaders = []
    for l in loader.template_source_loaders:
        if isinstance(l, CachedLoader):
            # flatten cached loaders, otherwise they're kinda complex
            loaders.extend(l.loaders)
        else:
            loaders.append(l)
    
    for l in loaders:
        for tupl in gen_loader_templates(l):
            yield tupl

def gen_loader_templates(l):
    """
    Generator. Yields paths to the templates for the given loader.
    """
    logging.info('Using loader: %r' % l)
    from django.template.loaders.app_directories import Loader as ADLoader
    from django.template.loaders.filesystem import Loader as FSLoader
    #from django.template.loaders.eggs import Loader as EggsLoader
    
    if isinstance(l, ADLoader):
        gen = _gen_AD_templates
    elif isinstance(l, FSLoader):
        gen = _gen_FS_templates
    else:
        #TODO EggsLoader (any others?)
        # TODO: should probably just raise a warning here, since any other loaders in settings will work fine.
        raise ValueError("django-tc doesn't support this loader: %s" % l.__class__.__name__)
    
    for tupl in gen(l):
        yield tupl

def _gen_AD_templates(l):
    """
    Generator. Takes an app_directories loader, and yields paths to the templates for it.
    """
    from django.template.loaders.app_directories import app_template_dirs
    for tupl in _gen_FS_templates(l, app_template_dirs):
        yield tupl

def _gen_FS_templates(l, template_dirs=settings.TEMPLATE_DIRS):
    """
    Generator. Takes a filesystem loader, and yields paths to the templates for it.
    """
    for template_dir in template_dirs:
        logging.info('Looking in template directory %r' % template_dir)
        for path, dirs, files in os.walk(template_dir, followlinks=True):
            for f in files:
                abs_path = os.path.join(path, f)
                rel_path = abs_path[len(template_dir):]
                if rel_path[0] == '/':
                    rel_path = rel_path[1:]
                
                logging.info('Found template %r' % rel_path)
                yield (rel_path, abs_path)
