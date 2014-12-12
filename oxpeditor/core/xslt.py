import os
import pkg_resources

from lxml import etree

from django.conf import settings

def transform(document, template_name):
    with pkg_resources.resource_stream('oxpeditor', 'config/' + template_name) as f:
        template = etree.XSLT(etree.parse(f))

    return template(document)

def xslattr(obj, document):
    for node in document.findall('*'):
        setattr(obj, node.tag, node.text or None)

