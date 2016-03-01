import datetime
import logging
import ssl
import urllib2
from optparse import make_option

from lxml import etree

from django.core.management import BaseCommand

from oxpeditor.core.models import File, Object
from oxpeditor.core.utils import date_filter
from oxpeditor.linkcheck.models import Link

NS = {'tei': 'http://www.tei-c.org/ns/1.0'}

logger = logging.getLogger('oxpeditor.linkchecker')

class Command(BaseCommand):
    option_list = BaseCommand.option_list + (
        make_option('--gather',
            action='store_true',
            dest='gather',
            default=False,
            help='Gather links before validating'),
        make_option('--force',
            action='store_true',
            dest='force',
            default=False,
            help='Force-check all links'),
        )

    def handle(self, *args, **options):
        if options['gather']:
            self.gather_links()
        self.validate_links(force=options['force'])



    def gather_links(self):
        for file in File.objects.all():
            self.gather_links_for_file(file)

    def gather_links_for_file(self, file):
        file_xml = etree.fromstring(file.xml)
        date_filter(file_xml)
        for xml in file_xml.xpath("descendant-or-self::*[@oxpID]"):
            oxpid = xml.attrib['oxpID']
            object = Object.objects.get(oxpid=oxpid)

            traits = xml.xpath('.//tei:trait[@type and tei:desc/tei:ptr/@target]', namespaces=NS)
            traits = [t for t in traits if t.xpath('ancestor::*[@oxpID]')[-1].attrib['oxpID'] == oxpid]
            types = set(t.attrib['type'] for t in traits)
            Link.objects.filter(object=object).exclude(type__in=types).delete()

            for trait in traits:
                link, _ = Link.objects.get_or_create(object=object, type=trait.attrib['type'])
                if link.target != trait[0][0].attrib['target']:
                    link.state = 'new'
                    link.target = trait[0][0].attrib['target']
                    link.status_code = None
                    link.redirects_to = ''
                    link.last_checked = None
                    link.problem = 'new'
                    link.save()

    def validate_links(self, links=None, force=False):
        now = datetime.datetime.utcnow()
        check_threshold = now - datetime.timedelta(7)

        if links is None:
            links = Link.objects.all()

        for link in links:
            type_ = link.type
            target = link.target
            initial_problem = link.problem
            initial_redirects_to = link.redirects_to
            initial_status_code = link.status_code
            if not force and (link.state != 'new' and link.last_checked and link.last_checked > check_threshold):
                continue

            request = urllib2.Request(target,
                                      headers={'User-Agent': 'oxpoints-link-checker (oxpoints@it.ox.ac.uk)'})
            try:
                response = urllib2.urlopen(request)
            except urllib2.HTTPError as e:
                link.status_code = e.code
                link.redirects_to = ''
                link.problem = 'error'
            except urllib2.URLError:
                link.status_code = None
                link.redirects_to = ''
                link.problem = 'url'
            except ssl.CertificateError:
                link.status_code = None
                link.redirects_to = ''
                link.problem = 'cert'
            else:
                link.status_code = response.code
                link.redirects_to = response.url if response.url != target else ''
                if link.redirects_to:
                    link.problem = 'redirect'
                else:
                    link.problem = 'ok'

            if link.problem == 'ok':
                link.state = 'ok'
            else:
                if initial_problem != link.problem or \
                    initial_redirects_to != link.redirects_to or \
                    initial_status_code != link.status_code:
                    link.state = 'broken'

            logger.info('%s %s %3s %s',
                        link.state.center(10), link.problem.center(8), link.status_code or '', link.target)

            link.last_checked = now
            link.save()
