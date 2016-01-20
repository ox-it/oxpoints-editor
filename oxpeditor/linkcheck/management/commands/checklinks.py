import ssl
import urllib

import datetime
import urllib2

from lxml import etree

from django.core.management import BaseCommand

from oxpeditor.core.models import File, Object
from oxpeditor.linkcheck.models import Link

NS = {'tei': 'http://www.tei-c.org/ns/1.0'}


class Command(BaseCommand):
    def handle(self, *args, **options):
        self.gather_links()
        self.validate_links()

    def gather_links(self):
        for file in File.objects.all():
            file_xml = etree.fromstring(file.xml)
            for xml in file_xml.xpath("descendant-or-self::*[@oxpID]"):
                oxpid = xml.attrib['oxpID']
                object = Object.objects.get(oxpid=oxpid)

                traits = xml.xpath('.//tei:trait[@type and tei:desc/tei:ptr/@target]', namespaces=NS)
                traits = [t for t in traits if t.xpath('ancestor::*[@oxpID]')[0].attrib['oxpID'] == oxpid]
                types = set(t.attrib['type'] for t in traits)
                Link.objects.filter(object=object).exclude(type__in=types).delete()

                for trait in traits:
                    link, _ = Link.objects.get_or_create(object=object, type=trait.attrib['type'])
                    if link.target != trait[0][0].attrib['target']:
                        link.state = 'new'
                        link.target = trait[0][0].attrib['target']
                        link.status_code = None
                        link.redirects_to = ''
                        link.save()

    def validate_links(self):
        now = datetime.datetime.utcnow()
        check_threshold = now - datetime.timedelta(7)

        for link in Link.objects.all():
            type_ = link.type
            target = link.target
            initial_problem = link.problem
            initial_redirects_to = link.redirects_to
            initial_status_code = link.status_code
            if link.state != 'new' and link.last_checked and link.last_checked > check_threshold:
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

            link.last_checked = now
            link.save()
