from collections import defaultdict
from datetime import datetime

from lxml import etree

from .models import File, Object, Relation, NS

class FileXMLCache(defaultdict):
    def __init__(self):
        self.files = {}
    def __missing__(self, key):
        file_obj = File.objects.get(pk=key)
        self.files[key] = file_obj
        xml = etree.fromstring(file_obj.xml)
        self[key] = xml
        return xml

class RelationWrangler(object):
    def __init__(self, user):
        self.files = FileXMLCache()
        self.user = user
        self.objects_modified = defaultdict(set)
    
    def norm(self, obj):
        if isinstance(obj, Object):
            return obj
        elif isinstance(obj, basestring):
            return Object.objects.get(oxpid=obj)

    def add(self, active, passive, relation_type, dt_from=None, dt_to=None):
        active, passive = map(self.norm, [active, passive])
        xml = self.files[active.in_file.pk]
        
        obj = xml.xpath("/descendant-or-self::*[@oxpID='%s']" % active.oxpid)[0]
        relation = etree.Element('relation',
                                 passive='#%s' % passive.oxpid,
                                 name=relation_type)
        if dt_from:
            relation.attrib['from'] = dt_from
        if dt_to:
            relation.attrib['to'] = dt_to
        
        obj.append(relation)
        self.objects_modified[active.in_file.pk].add(active.oxpid)
    
    def remove(self, active, passive, relation_type, dt_to=None):
        active, passive = map(self.norm, [active, passive])
        relation = Relation.objects.get(active=active, passive=passive, type=relation_type)
    
        if relation.inferred:
            self._remove_implicit(relation, dt_to)
        else:
            self._remove_explicit(relation, dt_to)

        self.objects_modified[active.in_file.pk].add(active.oxpid)
    
    def _remove_implicit(self, relation, dt_to):
        self.split_out(relation.passive)
        if dt_to:
            self.add(relation.active, relation.passive, relation.type, dt_to=dt_to)
    
    def _remove_explicit(self, relation, dt_to):
        xml = self.files[relation.in_file.pk]
        active, passive, relation_type = relation.active, relation.passive, relation.type

        elems = xml.xpath("ancestor-or-self::*[@oxpID='%s']/tei:relation[@passive='#%s']" % (active.oxpid, passive.oxpid),
                          namespaces=NS)
        elems.sort(key=lambda elem: elem.attrib.get('from', ''), reverse=True)
        for elem in elems:
            if elem.attrib.get('to'):
                continue
            if elem.attrib['name'] == relation_type:
                split_relation = False
                break
            if relation_type == 'primary' and 'primary' in elem.attrib.get('type', '').split():
                split_relation = True
                break
        else:
            raise AssertionError
        
        if split_relation:
            del elem.attrib['type']
            if dt_to:
                self.add(active, passive, relation_type, elem.attrib.get('from'), dt_to)
        else:
            if dt_to:
                elem.attrib['to'] = dt_to
            else:
                elem.getparent().remove(elem)

    def split_out(self, obj):
        oxpid = obj.oxpid
        old_xml = self.files[obj.in_file.pk]
        new_file = self.new_file(oxpid)
        
        obj_xml = old_xml.xpath(".//*[@oxpID='%s']" % obj.oxpid)[0]
        
        # Copy and @from and @to attributes from ancestors 
        for node in obj_xml.xpath('ancestor::*'):
            if node.attrib.get('from'):
                obj_xml.attrib['from'] = max(obj_xml.attrib.get('from', '0000-00-00'), node.attrib['from'])
            if node.attrib.get('to'):
                obj_xml.attrib['to'] = min(obj_xml.attrib.get('to', '9999-12-31'), node.attrib['to'])
    
        obj_xml.getparent().remove(obj_xml)
        
        # Recreate the Element for obj_xml, but with an nsmap.
        new_obj = etree.Element(obj_xml.tag, obj_xml.attrib, nsmap={None: NS['tei']})
        for node in obj_xml:
            new_obj.append(node)
    
        
        obj.in_file = new_file
        obj.save()
        
        self.files[new_file.pk] = new_obj
        self.objects_modified[new_file.pk].add(obj.oxpid)
        
    def new_file(self, oxpid):
        file_obj = File.objects.create(filename='%s.xml' % oxpid,
                                       user=self.user,
                                       last_modified=datetime.now(),
                                       xml='<empty/>')
        self.files[file_obj.pk]
        return file_obj

    def save(self):
        for pk, xml in self.files.iteritems():
            file_obj = self.files.files[pk]
            
            xml = etree.tostring(xml, pretty_print=True)
            if xml == file_obj.xml:
                continue
            
            file_obj.user = self.user
            file_obj.xml = xml
            file_obj.last_modified = datetime.now()
            file_obj.save(objects_modified=self.objects_modified[pk])