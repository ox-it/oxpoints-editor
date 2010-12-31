from lxml import etree

from django.template import loader, Context

def transform(document, template_name, template_context=None):

    # Load a template and turn it into an XSL template
    template = loader.get_template(template_name)
    template = template.render(Context(template_context or {}))
    template = etree.XSLT(etree.XML(template))

    return template(document)

def xslattr(obj, document):
    for node in document.findall('*'):
        setattr(obj, node.tag, node.text or None)

