import itertools
from lxml import etree

from django.db import models
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse

from mptt.models import MPTTModel

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
    ('finance', 'Finance (two-letter) code'),
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
    ('liburl', 'Library'),
)

class File(models.Model):
    filename = models.TextField()
    user = models.ForeignKey(User, null=True, blank=True)
    last_modified = models.DateTimeField()

    xml = models.TextField()
    initial_xml = models.TextField(blank=True)

    def save(self, *args, **kwargs):
        relations_unmodified = kwargs.pop('relations_unmodified', False)

        xml = etree.fromstring(self.xml.replace('\r\n', '\n'))
        indent(xml)
        self.xml = etree.tostring(xml)
        super(File, self).save(*args, **kwargs)

        # Update the object metadata
        xml = date_filter(xml)
        seen_ids, seen_oxpids, rels = set(), set(), set()
        for entity in xml.xpath('descendant-or-self::*[@oxpID]'):
            oxpid = entity.attrib['oxpID']
            seen_oxpids.add(oxpid)
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

            for subentity in entity.xpath('*[@oxpID]', namespaces=NS):
                relation_type = {'place': 'contains', 'org': 'controls'}[entity.tag.split('}')[1]]
                rels.add((oxpid, subentity.attrib['oxpID'], relation_type, True))

            for relation in xml.xpath('tei:relation', namespaces=NS):
                active, passive = relation.getparent().attrib['oxpID'], relation.attrib['passive'][1:]
                relation_types = [relation.attrib['name']]
                if 'primary' in relation.attrib.get('type', '').split():
                    relation_types.append('primary')
                for relation_type in relation_types:
                    rels.add((active, passive, relation_type, False))

        for obj in Object.objects.filter(in_file=self):
            if not obj.oxpid in seen_oxpids:
                obj.active_relations.all().delete()
                obj.passive_relations.all().delete()
                obj.delete()

        if relations_unmodified:
            return

        relations = Relation.objects.filter(in_file=self).select_related('active', 'passive')
        relations = dict(((r.active.oxpid, r.passive.oxpid, r.type), r) for r in relations)

        for active, passive, relation_type, inferred in rels:
            seen_ids.add((active, passive, relation_type))
            try:
                relation = relations[(active, passive, relation_type)]
            except KeyError:
                active, _ = Object.objects.get_or_create(oxpid=active)
                passive, _ = Object.objects.get_or_create(oxpid=passive)
                relation = Relation(active=active,
                                    passive=passive,
                                    type=relation_type)
            if relation_type in ('controls', 'contains'):
                if relation.passive.parent != relation.active:
                    relation.passive.parent = relation.active
                    relation.passive.save()

            if not relation.pk or relation.inferred != inferred or relation.in_file != self:
                relation.inferred = inferred
                relation.in_file = self
                relation.save()

        Relation.objects.filter(in_file=self).update(user=self.user)

        for r in Relation.objects.filter(in_file=self):
            if (r.active.oxpid, r.passive.oxpid, r.type) not in seen_ids:
                if r.type in ('controls', 'contains'):
                    r.passive.parent = None
                    r.passive.save()
                r.delete()

    def delete(self, *args, **kwargs):
        self.object_set.all().delete()
        self.relation_set.all().delete()
        super(File, self).delete(*args, **kwargs)

    def __unicode__(self):
        return self.filename

    class Meta:
        ordering = ('filename',)
            
class Object(MPTTModel):
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

    idno_oucs = models.TextField(null=True, blank=True)
    idno_estates = models.TextField(null=True, blank=True)
    idno_finance = models.TextField(null=True, blank=True)

    parent = models.ForeignKey('self', null=True, blank=True)

    def __unicode__(self):
        return '%s (%s, %s)' % (self.title, self.type, self.oxpid)

    class Meta:
        ordering = ('sort_title', 'type')

    def get_absolute_url(self):
        return reverse('core:detail', args=[self.oxpid])

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
