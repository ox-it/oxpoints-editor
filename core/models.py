import itertools
from lxml import etree

from django.db import models
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse

from .utils import date_filter
from .xslt import transform, xslattr

NS = {'tei': 'http://www.tei-c.org/ns/1.0'}

IDNO_SCHEME_CHOICES = (
    ('', '-'*20),
    ('olis', 'OLIS'),
    ('oucs', 'OUCS'),
    ('obn', 'Estates'),
    ('rae', 'RAE'),
    ('ucas-institution', 'UCAS Institution Code'),
    ('ukrlp-ukprn', 'UK Register of Learning Providers Number'),
    ('edubase-urn', 'Edubase URN'),
    ('jiscmu', 'JISC Monitoring Unit identifier'),   
    ('osm', 'OSM feature'),   
)

RELATION_TYPE_CHOICES = (
    ('contains', 'contains'),
    ('owns', 'owns'),
    ('occupies', 'occupies'),
    ('controls', 'has sub-unit'),
    ('primary', 'has primary site'),
)

RELATION_TYPE_INVERSE = (
    ('contains', 'is contained by'),
    ('owns', 'is owned by'),
    ('occupies', 'is occupied by'),
    ('controls', 'is sub-unit of'),
    ('primary', 'primary site of'),
)

URL_TYPE_CHOICES = (
    ('', '-'*20),
    ('url', 'Homepage'),
    ('iturl', 'IT Support'),
    ('weblearn', 'WebLearn'),
    ('library', 'Library'),
)

class File(models.Model):
    filename = models.TextField()
    user = models.ForeignKey(User, null=True, blank=True)
    last_modified = models.DateTimeField()

    xml = models.TextField()
    initial_xml = models.TextField()

    def save(self, *args, **kwargs):
        relations_unmodified = kwargs.pop('relations_unmodified', False)

        xml = etree.fromstring(self.xml.replace('\r\n', '\n'))
        indent(xml)
        self.xml = etree.tostring(xml)
        super(File, self).save(*args, **kwargs)

        # Update the object metadata
        xml = date_filter(xml)
        seen_ids = set()
        for entity in xml.xpath('descendant-or-self::*[@oxpID]'):
            oxpid = entity.attrib['oxpID']
            try:
                obj = Object.objects.get(oxpid=oxpid)
            except Object.DoesNotExist:
                obj = Object(oxpid=oxpid)
            obj.user = self.user
            obj.in_file = self
            xslattr(obj, transform(entity, 'metadata.xsl'))
            obj.save()

            if relations_unmodified:
                continue

            rels = set()
            for subentity in entity.xpath('*[@oxpID]', namespaces=NS):
                print entity, subentity
                relation_type = {'place': 'contains', 'org': 'controls'}[entity.tag.split('}')[1]]
                rels.add((oxpid, subentity.attrib['oxpID'], relation_type, True))

            for relation in xml.xpath('tei:relation', namespaces=NS):
                active, passive = relation.getparent().attrib['oxpID'], relation.attrib['passive'][1:]
                relation_types = [relation.attrib['name']]
                if 'primary' in relation.attrib.get('type', '').split():
                    relation_types.append('primary')
                for relation_type in relation_types:
                    rels.add((active, passive, relation_type, False))

            for active, passive, relation_type, inferred in rels:
                seen_ids.add((active, passive, relation_type))
                try:
                    relation = Relation.objects.get(active__oxpid=active,
                                                    passive__oxpid=passive,
                                                    type=relation_type)
                except Relation.DoesNotExist:
                    active, _ = Object.objects.get_or_create(oxpid=active)
                    passive, _ = Object.objects.get_or_create(oxpid=passive)
                    relation = Relation(active=active,
                                        passive=passive,
                                        type=relation_type)
                relation.inferred = inferred
                relation.in_file = self
                relation.user = self.user
                relation.save()

        if relations_unmodified:
            return

        for r in Relation.objects.filter(in_file=self):
            if (r.active.oxpid, r.passive.oxpid, r.type) not in seen_ids:
                r.delete()

    def delete(self, *args, **kwargs):
        self.object_set.all().delete()
        self.relation_set.all().delete()
        super(File, self).delete(*args, **kwargs)

    def __unicode__(self):
        return self.filename

    class Meta:
        ordering = ('filename',)
            
class Object(models.Model):
    user = models.ForeignKey(User, null=True, blank=True)
    in_file = models.ForeignKey(File, null=True)
    oxpid = models.CharField(max_length = 8)

    title = models.TextField(blank=True)
    homepage = models.TextField(blank=True)
    address = models.TextField(blank=True)
    sort_title = models.TextField(blank=True)
    root_elem = models.TextField(blank=True)
    type = models.TextField(blank=True)
    dt_from = models.TextField(null=True, blank=True)
    dt_to = models.TextField(null=True, blank=True)


    def __unicode__(self):
        return '%s (%s, %s)' % (self.title, self.type, self.oxpid)

    class Meta:
        ordering = ('sort_title', 'type')

    def get_absolute_url(self):
        return reverse('detail', args=[self.oxpid])

class Relation(models.Model):
    user = models.ForeignKey(User, null=True, blank=True)
    inferred = models.BooleanField()
    in_file = models.ForeignKey(File)

    active = models.ForeignKey(Object, related_name="active_relations")
    passive = models.ForeignKey(Object, related_name="passive_relations")
    type = models.CharField(max_length=32, choices=RELATION_TYPE_CHOICES)

    def get_inverse_type_display(self):
        return dict(RELATION_TYPE_INVERSE).get(self.type, 'is %s of' % self.type)

def indent(elem, level=0):
    i = "\n" + level*"  "
    if len(elem):
        if not elem.text or not elem.text.strip():
            elem.text = i + "  "
        if not elem.tail or not elem.tail.strip():
            elem.tail = i
        for elem in elem:
            indent(elem, level+1)
        if not elem.tail or not elem.tail.strip():
            elem.tail = i
    else:
        if level and (not elem.tail or not elem.tail.strip()):
            elem.tail = i
