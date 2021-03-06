import logging

from django.core.management.base import BaseCommand

from vacuum.checker import TemplateChecker
from vacuum.loading import gen_all_templates


verbosity_map = {
    0: logging.ERROR,
    1: logging.WARNING,
    2: logging.INFO,
    3: logging.DEBUG,
}


class Command(BaseCommand):
    args = '[--verbosity]'
    help = 'Checks templates for badness'

    def handle(self, *args, **options):
        log_level = verbosity_map[int(options['verbosity'])]
        logging.basicConfig(format="%(levelname)s: %(message)s",
                            level=log_level)

        checker = TemplateChecker()

        for rel_path, abs_path in gen_all_templates():
            try:
                checker.check_template(rel_path)
            except (SystemExit, KeyboardInterrupt):
                raise
            except Exception, e:
                logging.error("%s exception while checking template %s: %s",
                                e.__class__.__name__, abs_path, e)
