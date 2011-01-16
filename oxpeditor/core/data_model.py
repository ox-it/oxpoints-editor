import os

from lxml import etree

from django.conf import settings

model = etree.parse(os.path.join(settings.CONFIG_PATH, 'model.xml')).getroot()

def as_choices(xs, attr='label'):
    return (('', '-'*20),) + tuple(sorted(((x.name, getattr(x, attr)) for x in xs), key=lambda x:x[1].lower()))

class WithRegistry(object):
    _registry = {}
    def __init__(self, name, **kwargs):
        WithRegistry._registry[(type(self), name)] = self
        setattr(type(self), name, self)
        setattr(self, 'name', name)
        for key, value in kwargs.iteritems():
            setattr(self, key, value)
    
    @classmethod
    def keys(cls):
        return [n for (n, i) in cls.items()]
        
    @classmethod
    def values(cls):
        return [i for (n, i) in cls.items()]
        
    @classmethod
    def items(cls):
        return [(n, i) for ((c, n), i) in WithRegistry._registry.items() if c == cls]
    
    @classmethod
    def as_dict(cls):
        return dict(cls.items())
    
    @classmethod
    def for_name(cls, name, default=False):
        try:
            return WithRegistry._registry[(cls, name)]
        except KeyError:
            if default == False:
                raise
            else:
                return default
        
    def __repr__(self):
        return "<%s name=%r>" % (type(self).__name__, self.name)

class Identifier(WithRegistry):
    @classmethod
    def for_type(cls, t):
        return filter(lambda x:t in x.types, cls.values())

class Type(WithRegistry):
    @property
    def relation_types(self):
        return set(Relation.for_name(name) for (name, t) in  self.relations)

    @property
    def child_relations(self):
        return set(Relation.for_name(name) for ((name, t), child) in  self.relations.items() if child)

    @property
    def child_types(self):
        return set(Type.for_name(t) for ((name, t), child) in  self.relations.items() if child)

    def types_for_relation(self, relation_name):
        return set(v for k,v in self.relations if k == relation_name)
    
    @classmethod
    def get_child_relation(cls, active, passive):
        active = cls.for_name(active)
        for (relation, name), child in active.relations.items():
            if name == passive and child:
                return relation
        else:
            raise ValueError

class Relation(WithRegistry):
    pass


def parse_relations(rs):
    relation = {}
    for r in rs:
        for t in r.attrib['passive'].split(' '):
            relation[(r.attrib['name'], t)] = r.attrib.get('child', 'false') == 'true'
    return relation
    
relation_sets = {}
for relation_set in model.xpath('relation-sets/relation-set'):
    relation_sets[relation_set.attrib['name']] = parse_relations(relation_set.xpath('relation'))


for identifier in model.xpath('identifiers/identifier'):
    Identifier(name=identifier.attrib['name'],
               label=identifier.xpath('label')[0].text,
               types=identifier.attrib['types'].split(' '))


for type_ in model.xpath('types/type'):
    relations = {}
    for rs in type_.xpath('relations/relation-set'):
        relations.update(relation_sets[rs.attrib['name']])
    relations.update(parse_relations(type_.xpath('relations/relation')))
            
    Type(name=type_.attrib['name'],
         root_element=type_.attrib['root_element'],
         may_create=type_.attrib.get('may_create', 'true') == 'true',
         label=type_.xpath('label')[0].text,
         relations=relations)

for relation in model.xpath('relations/relation'):
    Relation(name=relation.attrib['name'],
             forward=relation.attrib['forward'],
             backward=relation.attrib['backward'])