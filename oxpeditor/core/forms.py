from collections import defaultdict
import itertools
import re
from lxml import etree

from django import forms
from django.forms.formsets import formset_factory, BaseFormSet
from django.forms.util import ErrorDict

from .models import IDNO_SCHEME_CHOICES, URL_TYPE_CHOICES, SPACE_CONFIGURATION_CHOICES
from .utils import date_filter
from .xslt import transform
import data_model

DATE_REGEX = r"""\d{1,4}(-\d{2}(-\d{2})?)?"""

nsmap = {None: 'http://www.tei-c.org/ns/1.0'}

class NameForm(forms.Form):
    path = forms.CharField(required=False, widget=forms.HiddenInput)
    value = forms.CharField(required=True)
    type_preferred = forms.BooleanField(required=False)
    type_sort = forms.BooleanField(required=False)
    type_alternate = forms.BooleanField(required=False)
    type_hidden = forms.BooleanField(required=False)

    def serialize(self, cd, obj):
        types = set()
        for t in ('preferred', 'sort', 'alternate', 'hidden'):
            if cd.get('type_%s' % t):
                types.add(t)
        n = etree.Element(obj.root_elem + 'Name', nsmap={None: 'http://www.tei-c.org/ns/1.0'}, type=' '.join(types))
        n.text = cd['value']
        return n

class IDNoForm(forms.Form):
    path = forms.CharField(required=False, widget=forms.HiddenInput)
    value = forms.CharField(required=True)
    scheme = forms.ChoiceField(choices=IDNO_SCHEME_CHOICES)

    def serialize(self, cd, obj):
        n = etree.Element('idno', nsmap={None: 'http://www.tei-c.org/ns/1.0'}, type=cd['scheme'])
        n.text = cd['value']
        return n

class SpaceConfigurationForm(forms.Form):
    path = forms.CharField(required=False, widget=forms.HiddenInput)
    type = forms.ChoiceField(choices=SPACE_CONFIGURATION_CHOICES)
    capacity = forms.IntegerField(required=False)
    comment = forms.CharField(required=False)

    def serialize(self, cd, obj):
        n = etree.Element('trait', nsmap=nsmap, type='configuration', subtype=cd['type'])
        if cd.get('capacity'):
            capacity = etree.SubElement(n, 'note', type='capacity')
            capacity.text = unicode(cd['capacity'])
        if cd.get('comment'):
            capacity = etree.SubElement(n, 'note', type='comment')
            capacity.text = cd['comment']
        return n

class AddressForm(forms.Form):
    path = forms.CharField(required=False, widget=forms.HiddenInput)
    street = forms.CharField(required=True, label="First line")
    extended = forms.CharField(required=False, label="Second line", help_text="(optional)")
    locality = forms.CharField(required=True, label="City")
    postcode = forms.CharField(required=False, label="Post code", help_text="(optional)")

    def serialize(self, cd, obj):
        n = etree.Element('location', nsmap={None: 'http://www.tei-c.org/ns/1.0'})
        a = etree.SubElement(n, 'address')
        for k in ('street', 'extended', 'locality'):
            if cd.get(k):
                al = etree.SubElement(a, 'addrLine')
                al.text = cd.get(k)
        if cd.get('postcode'):
            al = etree.SubElement(a, 'postCode')
            al.text = cd.get('postcode')
        return n

    max_num = 1

class URLForm(forms.Form):
    path = forms.CharField(required=False, widget=forms.HiddenInput)
    url = forms.URLField()
    ptype = forms.ChoiceField(choices=URL_TYPE_CHOICES)

    def serialize(self, cd, obj):
        r = etree.Element('trait', nsmap={None: 'http://www.tei-c.org/ns/1.0'}, type=cd['ptype'])
        n = etree.SubElement(r, 'desc')
        n = etree.SubElement(n, 'ptr', target=cd['url'])
        return r

class LocationForm(forms.Form):
    path = forms.CharField(required=False, widget=forms.HiddenInput)
    latitude = forms.FloatField()
    longitude = forms.FloatField()

    def serialize(self, cd, obj):
        l = etree.Element('location')
        g = etree.SubElement(l, 'geo')
        g.text = '%f %f' % (cd['longitude'], cd['latitude'])
        return l   

    max_num = 1

class DescriptionForm(forms.Form):
    path = forms.CharField(required=False, widget=forms.HiddenInput)
    description = forms.CharField(widget=forms.Textarea)

    def serialize(self, cd, obj):
        d = etree.Element('desc')
        d.text = cd['description']
        return d

    max_num = 1


UPDATE_TYPE_CHOICES = (
    ('correct', 'corrects information that has never been true'),
    ('update', 'updates OxPoints to reflect a change in the real world'),
)

class UpdateTypeForm(forms.Form):
    update_type = forms.ChoiceField(choices=UPDATE_TYPE_CHOICES, widget=forms.RadioSelect)
    when = forms.DateField(required=False)

    def clean(self):
        cleaned_data = self.cleaned_data
        if cleaned_data.get('update_type') != 'update':
            cleaned_data['when'] = None
        else:
            if not cleaned_data.get('when'):
                self._errors['when'] = self.error_class(['You must specify a date on which these changes took place'])
                if 'when' in cleaned_data:
                    del cleaned_data['when']
        return cleaned_data

class CommitForm(forms.Form):
    message = forms.CharField(widget=forms.Textarea, label='Commit description')

class RequestForm(forms.Form):
    subject = forms.CharField(label='Subject of request')
    message = forms.CharField(widget=forms.Textarea, label='Message')
    related_file = forms.FileField(required=False)

def CreateForm(*args, **kwargs):
    parent_type = kwargs.pop('parent_type', None)
    if parent_type:
        choices = data_model.Type.for_name(parent_type).child_types
    else:
        choices = (t for t in data_model.Type.values() if t.may_create)
    choices =  data_model.as_choices(choices)
    
    class form(forms.Form):
        type = forms.ChoiceField(choices=choices)
        title = forms.CharField(required=False, label='Name')
        dt_from = forms.RegexField(DATE_REGEX,
                                   error_messages={'invalid': 'Date must be in YYYY[-MM[-DD]] format'},
                                   required=False,
                                   label='When did this entity come into existence?')
    return form(*args, **kwargs)

class ImplicitDeleteFormSet(BaseFormSet):
    def is_valid(self):
        for i in range(self.total_form_count()):
            form = self.forms[i]
            prefix = form.prefix + '-'
            data = dict((k[len(prefix):], form.data[k]) for k in form.data if k.startswith(prefix))
            if all(not data[k] for k in data if not k in ('path', 'DELETE')):
                form.cleaned_data = {
                    'path': data['path'],
                    'DELETE': True,
                }
                form._errors = ErrorDict()
        return super(ImplicitDeleteFormSet, self).is_valid()

def get_forms(xml, post_data):
    xml = date_filter(xml, ignore=True)
    xml = transform(xml, 'forms.xsl')

    ret = {}

    for f in xml.getroot().xpath("form-types/form-type"):
        ret[f.attrib['name']] = []

    for f in xml.getroot().xpath("form[not(@ignore)]"):
        if f.attrib['name'] not in ret:
            continue
        initial_data = {'path': f.attrib['path']}
        for g in f:
            initial_data[g.tag] = g.text or ''
        ret[f.attrib['name']].append(initial_data)
    
    for k in ret:
        form_class = globals()[k]
        assert issubclass(form_class, forms.Form)
        formset = formset_factory(form_class,
                                  extra=2,
                                  can_delete=True,
                                  max_num=getattr(form_class, 'max_num', None),
                                  formset=ImplicitDeleteFormSet)
        ret[k] = formset(post_data,
                         initial=ret[k],
                         prefix='-'.join([xml.getroot().attrib['oxpid'], k]))

    return ret
