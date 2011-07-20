import itertools
from lxml import etree

from django.db import models
from django.db.models import Q
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse

from mptt.models import MPTTModel

from .utils import date_filter
from .xslt import transform, xslattr
from . import data_model

NS = {'tei': 'http://www.tei-c.org/ns/1.0'}

IDNO_SCHEME_CHOICES = data_model.as_choices(data_model.Identifier.values())

RELATION_TYPE_CHOICES = data_model.as_choices(data_model.Relation.values(), 'forward')
RELATION_TYPE_INVERSE = data_model.as_choices(data_model.Relation.values(), 'backward')

RELATION_CONSTRAINTS = {
    #           active constraints       passive constraints     cardinality constraints
    'contains': ({'root_elem': 'place'}, {'root_elem': 'place'}, 1,    None),
    'owns':     ({'root_elem': 'org'  }, {'root_elem': 'place'}, 1,    None),
    'occupies': ({'root_elem': 'org'  }, {'root_elem': 'place'}, None, None),
    'controls': ({'root_elem': 'org'  }, {'root_elem': 'org'  }, 1,    None),
    'primary':  ({'root_elem': 'org'  }, {'root_elem': 'place'}, None, 1   ),
    'supplies': ({'type':      'Meter'}, Q(type='Meter') | Q(root_elem='place'), 1,    None),
}

URL_TYPE_CHOICES = (
    ('', '-'*20),
    ('url', 'Homepage'),
    ('iturl', 'IT Support'),
    ('weblearn', 'WebLearn'),
    ('liburl', 'Library'),
)

SPACE_CONFIGURATION_CHOICES = (
    ('Boardroom', 'Boardroom'),
    ('UShape', 'U-Shape'),
    ('Banquet', 'Banquet'),
    ('Cabaret', 'Cabaret'),
    ('Reception', 'Reception'),
    ('Theatre', 'Theatre'),
    ('Classroom', 'Classroom'),
)

PLACES = ('Room', 'Building', 'Space', 'Site', 'OpenSpace', 'Carpark')
ORGS = ('University', 'Unit', 'StudentGroup', 'Department', 'Faculty',
        'Division', 'Organization', 'College', 'Hall', 'Library',
        'SubLibrary', 'Museum')
OBJECTS = ('Meter',)

TYPE_CHOICES = {
    'org': ORGS,
    'place': PLACES,
    'object': OBJECTS,
}

SUB_RELATIONS = {
    'Room':         ('contains', ()),
    'Building':     ('contains', ('Space', 'Room')),
    'Space':        ('contains', ('Space', 'Room')),
    'Site':         ('contains', ('Site', 'Building', 'Carpark', 'OpenSpace')),
    'OpenSpace':    ('contains', ('OpenSpace',)),
    'Carpark':      ('contains', ()),
    'University':   ('controls', ('Division',)),
    'Unit':         ('controls', ('Unit', 'Library')),
    'StudentGroup': ('controls', ()),
    'Department':   ('controls', ('Department', 'Unit', 'Library')),
    'Faculty':      ('controls', ('Library',)),
    'Division':     ('controls', ('Department', 'Unit', 'Faculty')),
    'Organization': ('controls', ('Organization',)),
    'College':      ('controls', ('Library',)),
    'Hall':         ('controls', ('Library',)),
    'Library':      ('controls', ('SubLibrary',)),
    'SubLibrary':   ('controls', ()),
    'Museum':       ('controls', ('Library',)),
    'Meter':        ('supplies', ('Meter',)),
}
CREATE_IN_SAME_FILE = ('Space', 'Room', 'OpenSpace', 'Carpark', 'SubLibrary',)

class File(models.Model):
    filename = models.TextField()
    user = models.ForeignKey(User, null=True, blank=True)
    last_modified = models.DateTimeField()

    xml = models.TextField()
    initial_xml = models.TextField(blank=True)

    def save(self, *args, **kwargs):
        relations_unmodified = kwargs.pop('relations_unmodified', False)
        objects_modified = kwargs.pop('objects_modified', frozenset())

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
            obj.modified |= oxpid in objects_modified
            xslattr(obj, transform(entity, 'metadata.xsl'))
            obj.save()
            
            if relations_unmodified:
                continue

            for subentity in entity.xpath('*[@oxpID]', namespaces=NS):
                relation_type = {'place': 'contains', 'org': 'controls', 'object': 'supplies'}[entity.tag.split('}')[1]]
                rels.add((oxpid, subentity.attrib['oxpID'], relation_type, True))

            for relation in entity.xpath('tei:relation', namespaces=NS):
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
    modified = models.BooleanField(default=False)
    
    oxpid = models.CharField(max_length = 8)

    title = models.TextField(null=True, blank=True)
    homepage = models.TextField(null=True, blank=True)
    address = models.TextField(null=True, blank=True)
    sort_title = models.TextField(null=True, blank=True)
    root_elem = models.TextField(null=True, blank=True)
    type = models.TextField(null=True, blank=True)
    dt_from = models.TextField(null=True, blank=True)
    dt_to = models.TextField(null=True, blank=True)

    idno_oucs = models.TextField(null=True, blank=True)
    idno_estates = models.TextField(null=True, blank=True)
    idno_finance = models.TextField(null=True, blank=True)
    
    longitude = models.FloatField(null=True)
    latitude = models.FloatField(null=True)

    parent = models.ForeignKey('self', null=True, blank=True)
    
    autosuggest_title = models.TextField(blank=True)

    def __unicode__(self):
        return '%s (%s, %s)' % (self.title, self.type, self.oxpid)
        
    def save(self, *args, **kwargs):
        parts = [self.oxpid]
        for name in ('title', 'idno_oucs', 'idno_estates', 'idno_finance'):
            if getattr(self, name, None):
                parts.append(getattr(self, name))
        self.autosuggest_title = ', '.join(parts)
        super(Object, self).save(*args, **kwargs)

    class Meta:
        ordering = ('sort_title', 'type')

    def get_absolute_url(self):
        return reverse('core:detail', args=[self.oxpid])
        
    def satisfies(self, constraint):
        if all('__' not in c for c in constraint):
            return all(getattr(self, c) == constraint[c] for c in constraint)
        elif isinstance(constraint, Q):
            return Object.objects.filter(constraint, pk=self.pk).count() == 1
        else:
            return Object.objects.filter(pk=self.pk, **constraint).count() == 1

            
    @property
    def child_relations(self):
        try:
            return data_model.Type.for_name(self.type).child_relations
        except KeyError:
            return ()
    
    @property
    def child_types(self):
        try:
            return data_model.Type.for_name(self.type).child_types
        except KeyError:
            return ()
    
    @property
    def type_description(self):
        return data_model.Type.for_name(self.type)

    def get_grouped_relations(self):
        for name, relation in data_model.Relation.items():
            if not name:
                continue
            yield (relation.forward, True, self.active_relations.filter(type=name).order_by('passive__sort_title'))
            yield (relation.backward, False, self.passive_relations.filter(type=name).order_by('active__sort_title'))

# Add some handy properties to our model for use from templates.
for name, label in RELATION_TYPE_CHOICES:
    if not name:
        continue
    for direction in ('active', 'passive'):
        def f(name, direction):
            def g(self): return getattr(self, '%s_relations' % direction).filter(type=name)
            g.__name__ = '%s_%s' % (name, direction)
            return g
        g = f(name, direction)
        setattr(Object, g.__name__, g)
del f
#raise Exception(Object.controls_passive)



class Relation(models.Model):
    user = models.ForeignKey(User, null=True, blank=True)
    inferred = models.BooleanField()
    in_file = models.ForeignKey(File)

    active = models.ForeignKey(Object, related_name="active_relations")
    passive = models.ForeignKey(Object, related_name="passive_relations")
    type = models.CharField(max_length=32, choices=RELATION_TYPE_CHOICES)

    def get_inverse_type_display(self):
        return dict(RELATION_TYPE_INVERSE).get(self.type, 'is %s of' % self.type)

def _indentation(s, level):
    if s and s.strip():
        return s
    else:
        return '\n' * max(1, (s or '').count('\n')) + '  ' * level

def indent(elem, level=0):
    if len(elem):
        elem.text = _indentation(elem.text, level+1)
        elem.tail = _indentation(elem.tail, level)
        for elem in elem:
            indent(elem, level+1)
        elem.tail = _indentation(elem.tail, level)
    elif level:
        elem.tail = _indentation(elem.tail, level)
