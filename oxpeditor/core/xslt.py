import os

from lxml import etree

from django.conf import settings

def transform(document, template_name):
    template = etree.XSLT(etree.parse(os.path.join(settings.CONFIG_PATH, template_name)))

    return template(document)

def xslattr(obj, document):
    for node in document.findall('*'):
        setattr(obj, node.tag, node.text or None)

