from __future__ import with_statement

from itertools import chain
import difflib, urllib
from datetime import date, datetime
import json
from collections import defaultdict
import os, re

from xml.sax.saxutils import escape
from lxml import etree
from lxml.builder import ElementMaker

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.nonmultipart import MIMENonMultipart

from django.shortcuts import get_object_or_404
from django.contrib.auth.decorators import login_required, permission_required
from django.core.exceptions import PermissionDenied
from django.core.urlresolvers import reverse
from django.http import HttpResponseBadRequest, Http404, HttpResponse
from django.conf import settings
from django.db import connection
from django.views.generic import View
from django.utils.decorators import method_decorator
from django_conneg.http import HttpResponseSeeOther
from django_conneg.views import HTMLView, JSONView

from .models import Object, Relation, File, NS
from . import forms
from .xslt import transform
from .utils import date_filter, svn_lock, find_new_oxpid
from .subversion import perform_commit
from .forms import get_forms, UpdateTypeForm, CommitForm, RequestForm, CreateForm
from .relation import RelationWrangler
from . import data_model

class AuthedMixin(object):
    @method_decorator(login_required)
    def dispatch(self, request, *args, **kwargs):
        return super(AuthedMixin, self).dispatch(request, *args, **kwargs)

class EditingMixin(object):
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated():
            return HttpResponseSeeOther('%s?%s' % (settings.LOGIN_URL, urllib.urlencode({'next':request.get_full_path()})))
        elif not request.user.has_perm('core.change_object'):
            response = self.render(request, {}, 'insufficient-privileges')
            response.status_code = 403
            return response
        else:
            return super(EditingMixin, self).dispatch(request, *args, **kwargs)

class IndexView(HTMLView):
    template_name = 'index'
    def get(self, request):
        return self.render()

class CommitView(EditingMixin, HTMLView):
    template_name = 'commit'

    def get_initial_context(self):
        return {
            'form': CommitForm(self.request.POST or None),
            'done': self.request.GET.get('done') == 'true',
            'successful': Object.objects.filter(oxpid__in=self.request.GET.get('successful','').split(',')),
            'unsuccessful': Object.objects.filter(oxpid__in=self.request.GET.get('unsuccessful','').split(',')),
            'modified': Object.objects.filter(user=self.request.user, modified=True),
        }

    def get(self, request):
        self.context.update(self.get_initial_context())
        return self.render()

    def post(self, request):
        self.context.update(self.get_initial_context())
        if not self.context['form'].is_valid():
            return self.get(request)

        to_commit = set(File.objects.filter(user=request.user))
        edited = defaultdict(set)
        for obj in self.context['modified']:
            edited[obj.in_file].add(obj.oxpid)
            
        with svn_lock():
            successful = perform_commit(request.user, self.context['form'].cleaned_data['message'])
        unsuccessful = to_commit - successful

        return HttpResponseSeeOther('.?%s' % urllib.urlencode({
            'done': 'true',
            'successful': ','.join(chain(*(edited[f] for f in successful))),
            'unsuccessful': ','.join(chain(*(edited[f] for f in unsuccessful))),
        }))            

class DiffView(EditingMixin, HTMLView):
    template_name = 'diff'

    def get_initial_context(self):
        edited = File.objects.filter(user=self.request.user)

        objects, sm = [], difflib.SequenceMatcher()
        for obj in edited:
            l, r = obj.initial_xml.splitlines(), obj.xml.splitlines()
            sm = difflib.SequenceMatcher(None,
                                         [line.strip() for line in l],
                                         [line.strip() for line in r])

            lines = []
            for tag, i1, i2, j1, j2 in sm.get_opcodes():
                if tag == 'delete':
                    for i in range(i1, i2):
                        lines.append(('delete', (i+1, l[i]), (None, '')))
                elif tag == 'insert':
                    for j in range(j1, j2):
                        lines.append(('insert', (None, ''), (j+1, r[j])))
                elif tag in ('equal', 'replace'):
                    for i,j in zip(range(i1, i2), range(j1, j2)):
                        if i1 == 0: i1 = -3
                        if i2 == len(l): i2 = len(l)+3
                        if tag == 'replace':
                            lines.append((tag, (i+1, l[i]), (j+1, r[j])))
                        elif i1 + 3 == i and i < i2 - 3:
                            lines.append(('ellipsis', (None, ''),(None, '')))
                        elif i1 + 3 <= i < i2 - 3:
                            pass
                        else:
                            lines.append((tag, (i+1, l[i]), (j+1, r[j])))
            new_lines = []
            for tag, (l1, l2), (r1, r2) in lines:
                rem = len(l2) - len(l2.lstrip())
                l2 = '<div style="padding-left:%dpx">%s</div>' % (rem * 5, escape(l2.lstrip()))
                rem = len(r2) - len(r2.lstrip())
                r2 = '<div style="padding-left:%dpx">%s</div>' % (rem * 5, escape(r2.lstrip()))
                new_lines.append((tag, (l1, l2), (r1, r2)))
                    
            objects.append({'object': obj, 'diff': new_lines})

        return {
            'files': objects,
        }
        
    def get(self, request):
        self.context.update(self.get_initial_context())
        return self.render()

class ListView(EditingMixin, HTMLView):
    template_name = 'list'

    def get_initial_context(self):
        objects = Object.objects.all() #.order_by('-user')
        if 'type' in self.request.GET:
             objects = objects.filter(type=self.request.GET['type'])
        if 'q' in self.request.GET:
             objects = objects.filter(title__icontains=self.request.GET['q'])
        for n in ('finance', 'oucs', 'estates'):
            if n in self.request.GET:
                 objects = getattr(objects, 'filter' if self.request.GET[n] != 'yes' else 'exclude')(**{'idno_%s' % n: ''})
        if 'sort' in self.request.GET:
             objects = objects.order_by(*self.request.GET['sort'].split(','))
        if self.request.GET.get('user') == 'true':
             objects = objects.filter(user__isnull=False)
        today = date.today().strftime('%Y-%m-%d')
        objects = (o for o in objects if not (o.dt_to and o.dt_to <= today))
        seen, filtered_objects = set(), []
        for obj in objects:
            if obj.oxpid in seen:
                continue
            filtered_objects.append(obj)
            seen.add(obj.oxpid)
#        [f.save(relations_unmodified=True) for f in File.objects.all()]
        
        return {
             'objects': list(filtered_objects),
             'types': sorted(set(o.type for o in Object.objects.all())),
        }

    def get(self, request):
        self.context.update(self.get_initial_context())
        return self.render()

class TreeView(EditingMixin, HTMLView):
    template_name = 'tree'
    root_elem = None

    def walk_tree(self, it, obj):
        obj.final = False
        if obj.rght == obj.lft + 1:
            obj.height = 1
            obj.final = True
            return 1
        obj.height = 0
        while True:
            try:
                child = it.next()
            except StopIteration:
                return max(1, obj.height)
            height = self.walk_tree(it, child)
            obj.height += height
            if child.rght == obj.rght - 1:
                return max(1, obj.height)

    def get_initial_context(self, oxpid=None):
        if oxpid:
            roots = Object.objects.filter(oxpid__in=oxpid.split(","))
            objects = list(chain(*(root.get_descendants(include_self=True) for root in roots)))
            root = roots[0]
        else:
            objects = Object.tree.filter(root_elem=self.root_elem)
            root = None

        it = iter(objects)
        for i in it:
            self.walk_tree(it, i)

        return {
            'objects': objects,
            'root': root,
        }

    def get(self, request, oxpid=None):
        self.context.update(self.get_initial_context(oxpid))
        return self.render()

class DetailView(EditingMixin, HTMLView):
    template_name = 'detail'

    def get_initial_context(self, oxpid):
        try:
            obj = Object.objects.get(oxpid=oxpid, user__isnull=False)
        except Object.DoesNotExist:
            obj = get_object_or_404(Object, oxpid=oxpid)

        if not obj.in_file:
            raise PermissionDenied("This object is not yet available to edit.")

        xml = etree.fromstring(obj.in_file.xml).xpath("descendant-or-self::*[@oxpID='%s']" % oxpid)[0]
        forms = get_forms(xml, self.request.POST or None)
        
        relations = []
        for r in data_model.Type.for_name(obj.type).relation_types:
            relations.append({
                'types': data_model.Type.for_name(obj.type).types_for_relation(r.name),
                'name': r.name,
                'label': r.forward,
                'relations': obj.active_relations.filter(type=r.name).order_by('passive__sort_title').select_related('active', 'passive'),
            })

        return {
            'object': obj,
            'forms': forms,
            'management_forms': [fs.management_form for fs in forms.values()],
            'active_relations': obj.active_relations.order_by('type', 'passive__sort_title').select_related('passive'),
            'passive_relations': obj.passive_relations.order_by('type', 'active__sort_title').select_related('active'),
            'relations': relations,
            'update_type_form': UpdateTypeForm(self.request.POST or None),
            'editable': ('to' not in xml.attrib and not (obj.user and obj.user != self.request.user)) or self.request.user.is_superuser,
        }

    def get(self, request, oxpid):
        self.context.update(self.get_initial_context(oxpid))
        recent = request.session.get('recent', [])
        if oxpid in recent:
            recent.remove(oxpid)
        recent.insert(0, oxpid)
        request.session['recent'] = recent[:10]
        return self.render()

    def post(self, request, oxpid):
        self.context.update(self.get_initial_context(oxpid))
        if not self.context['editable']:
            return HttpResponseBadRequest()

        obj = self.context['object']
        root = etree.fromstring(obj.in_file.xml)
        xml = root.xpath("descendant-or-self::*[@oxpID='%s']" % oxpid)[0]

        if not (all([fs.is_valid() for fs in self.context['forms'].values()]) and self.context['update_type_form'].is_valid()):
            self.context['has_errors'] = True
            return self.get(request, oxpid)

        new_from = self.context['update_type_form'].cleaned_data['when']
        if new_from:
            new_from = new_from.strftime('%Y-%m-%d')

        additions, removals, replacements = [], [], []

        forms = chain(*[fs.forms for fs in self.context['forms'].values()])
        for form in forms:
            if not form.is_valid():
                continue
            cleaned_data = form.cleaned_data
            if not cleaned_data or not form.has_changed():
                continue

            if cleaned_data.get('path'):
                old = xml.xpath('tei:'+cleaned_data['path'].replace('/', '/tei:'), namespaces={'tei': 'http://www.tei-c.org/ns/1.0'})[0]
            else:
                old = None

            if cleaned_data.get('DELETE') and old is not None:
               removals.append(old)
               continue

            new = form.serialize(cleaned_data, self.context['object'])
#            if not new:
#                continue

            if old is not None:
                replacements.append((old, new))
            else:
                additions.append(new)

        for removal in removals:
            if new_from:
                removal.attrib['to'] = new_from
            else:
                removal.getparent().remove(removal)

        for addition in additions:
            if new_from:
                addition.attrib['from'] = new_from
            xml.append(addition)

        for old, new in replacements:
            if new_from:
                old.attrib['to'] = new_from
                new.attrib['from'] = new_from
                old.addnext(new)
            else:
                if 'from' in old.attrib:
                    new.attrib['from'] = old.attrib['from']
                if 'to' in old.attrib:
                    new.attrib['to'] = old.attrib['to']
                old.getparent().replace(old, new)

        file_obj = obj.in_file
        file_obj.user = request.user
        file_obj.xml = etree.tostring(root, pretty_print=True)
        file_obj.last_modified = datetime.now()
        file_obj.save(relations_unmodified=True, objects_modified=set([oxpid]))
        
        self.wrangle_relations(request, oxpid, new_from)

        return HttpResponseSeeOther('.')
    
    def wrangle_relations(self, request, oxpid, new_from):
        rw = RelationWrangler(request.user)

        for rel in self.context['relations']:
            to_add, to_remove = set(), set()
            name, types = rel['name'], rel['types']
            if 'as_values_%s' % name in request.POST:
                old = set(r.passive.oxpid for r in rel['relations'])
                new = set(request.POST['as_values_%s' % name].split(','))
                to_add |= (new - old)
                to_remove |= (old - new)
            if 'reladd-%s' % name in request.POST:
                to_add |= set(passive.strip() for passive in request.POST['reladd-%s' % name])
            to_remove |= set(r.split('-')[-1] for r in request.POST if r.startswith('reldel-%s-' % name))
        
            to_add = set(o.oxpid for o in Object.objects.filter(oxpid__in=to_add) if o.type in types) 
            to_remove = set(r.passive.oxpid for r in Relation.objects.filter(active__oxpid=oxpid, passive__oxpid__in=to_remove, type=name))
            
            for passive in to_add:
                rw.add(oxpid, passive, name, dt_from=new_from)
            for passive in to_remove:
                rw.remove(oxpid, passive, name, dt_to=new_from)
                
        rw.save()

class RequestView(AuthedMixin, HTMLView):
    template_name = 'request'

    def get_initial_context(self):
        return {
            'form': RequestForm(self.request.POST or None, self.request.FILES or None),
            'sent': self.request.GET.get('sent') == 'true',
        }

    def get(self, request):
        self.context.update(self.get_initial_context())
        return self.render()

    def post(self, request):
        self.context.update(self.get_initial_context())
        form, user = self.context['form'], request.user
        if not form.is_valid():
            return self.get(request)

        s = smtplib.SMTP(settings.EMAIL_HOST, settings.EMAIL_PORT)
        s.starttls()
        if settings.EMAIL_HOST_USER:
            s.login(settings.EMAIL_HOST_USER, settings.EMAIL_HOST_PASSWORD)

        sender = "%s %s (via OxPoints Editor) <%s>" % (user.first_name, user.last_name, user.email)
        recipients = ['%s <%s>' % manager for manager in settings.MANAGERS]

        msg = MIMEMultipart()
        msg['Subject'] = form.cleaned_data['subject']
        msg['From'] = sender
        msg['To'] = ', '.join(recipients)
        msg.attach(MIMEText(form.cleaned_data['message'], 'plain'))

        if request.FILES.get('related_file'):
            related_file = request.FILES['related_file']
            attachment = MIMENonMultipart(*related_file.content_type.split('/', 1))
            attachment.add_header('Content-Disposition', 'attachment', filename=related_file.name)
            attachment.set_payload(related_file.read())
            msg.attach(attachment)

        s.sendmail(sender, recipients, msg.as_string())

        return HttpResponseSeeOther(reverse('core:request') + '?sent=true')

class AutoSuggestView(EditingMixin, View):
    def get(self, request, active_type, relation_name):
        active_type = data_model.Type.for_name(active_type, None)
        if not active_type:
            raise Http404
        types = active_type.types_for_relation(relation_name)
        if not types:
            raise Http404
        
        suggestions = [{
                 'value': obj.oxpid,
                 'name': obj.autosuggest_title,
            } for obj in Object.objects.filter(autosuggest_title__icontains=self.request.GET.get('q', ''), type__in=types)]

        return HttpResponse(json.dumps(suggestions, indent=2), content_type='application/json')

class CreateView(EditingMixin, HTMLView):
    template_name = 'create'

    def get_initial_context(self, oxpid=None):
        if oxpid:
            parent = get_object_or_404(Object, oxpid=oxpid)
            if not parent.child_types:
                raise Http404
            form = CreateForm(self.request.POST or None,
                              initial={'dt_from': parent.dt_from}, parent_type=parent.type)
        else:
            parent = None
            form = CreateForm(self.request.POST or None)
        
        return {
            'form': form,
            'parent': parent,
        }
    
    def get(self, request, oxpid=None):
        self.context.update(self.get_initial_context(oxpid))
        return self.render()
    
    def post(self, request, oxpid=None):
        self.context.update(self.get_initial_context(oxpid))
        form, parent = self.context['form'], self.context['parent']
        if not form.is_valid():
            return self.get(request, oxpid)
            
        ptype, title, dt_from = map(form.cleaned_data.get, ['type', 'title', 'dt_from'])
        
        new_oxpid = find_new_oxpid()
        root_elem = data_model.Type.for_name(ptype).root_element
        file_obj = File(filename='%s.xml' % new_oxpid,
                        user=request.user,
                        last_modified=datetime.now())
                        
        E = ElementMaker(namespace=NS['tei'], nsmap={None: NS['tei']})
        
        xml = getattr(E, root_elem)(type=ptype, oxpID=new_oxpid)
        if dt_from:
            xml.attrib['from'] = dt_from
        if title:
            xml.append(getattr(E, '%sName' % root_elem)(title))
        
        file_obj.initial_xml = '<empty/>'
        file_obj.xml = etree.tostring(xml)
        file_obj.save(objects_modified=(new_oxpid,))
        
        if parent:
            rw = RelationWrangler(request.user)
            relation_name = data_model.Type.get_child_relation(parent.type, ptype)
            rw.add(parent.oxpid, new_oxpid, relation_name, dt_from)
            rw.save()
        
        return HttpResponseSeeOther(reverse('core:detail', args=[new_oxpid]))
            
class HelpView(HTMLView):
    template_name = 'help'
    def get(self, request):
        return self.render()

class RevertView(EditingMixin, HTMLView):
    template_name = 'revert'

    def get_initial_context(self, oxpid):
        obj = get_object_or_404(Object, oxpid=oxpid)
        file_obj = obj.in_file
        try:
            old = etree.fromstring(file_obj.initial_xml).xpath("descendant-or-self::*[@oxpID='%s']" % oxpid)[0]
        except (etree.XMLSyntaxError, IndexError):
            old = None
        new = etree.fromstring(file_obj.xml).xpath("descendant-or-self::*[@oxpID='%s']" % oxpid)[0]
        return {
            'obj': obj,
            'old': old,
            'new': new,
            'editable': not (obj.user and obj.user != self.request.user),
            'done': self.request.GET.get('done') == 'true',
        }

    def get(self, request, oxpid):
        self.context.update(self.get_initial_context(oxpid))
        return self.render()

    def post(self, request, oxpid):
        self.context.update(self.get_initial_context(oxpid))
        if not self.context['editable']:
            return HttpResponseBadRequest()
        obj, old, new = map(self.context.get, ['obj', 'old', 'new'])
        file_obj = obj.in_file

        if old is None:
            file_obj.delete()
            return HttpResponseSeeOther(reverse('core:detail-revert', args=[oxpid]) + '?done=true')
            raise NotImplementedError

        for c in old:
            if 'oxpID' in c.attrib:
                child_object = Object.objects.get(oxpid=c.attrib['oxpID'])
                if child_object.in_file == file_obj:
                    child_xml = new.xpath("*[@oxpID='%s']" % c.attrib['oxpID'])[0]
                else:
                    child_file = child_object.in_file
                    child_object.in_file = file_obj
                    child_object.save()
                    child_xml = etree.fromstring(child_file.xml)
                    if child_xml.attrib['oxpID'] == c.attrib['oxpID']:
                        child_file.delete()
                    else:
                        child_xml = child_xml.xpath(".//*[@oxpID='%s']" % oxpID)
                        child_xml.getparent().remove(child_xml)
                c.getparent().replace(c, child_xml)

        file_obj.xml = etree.tostring(old)
        file_obj.user = None
        obj.modified = False

        file_obj.save()
        obj.save()

        return HttpResponseSeeOther(reverse('core:detail-revert', args=[oxpid]) + '?done=true')

class LinkingYouView(EditingMixin, HTMLView):
    template_name = 'linking-you.html'

    def get(self, request):
        objects = Object.objects.filter(linking_you__isnull=False).exclude(linking_you='').order_by('title')
        if 'type' in self.request.GET:
             objects = objects.filter(type=self.request.GET['type'])
        terms = [{'name': k, 'label': v.label, 'help_text': v.help_text}
                 for k, v in forms.LinkingYouForm.base_fields.items()
                 if k != 'path']
        seen_terms = set()
        for o in objects:
            seen = []
            object_terms = set(o.linking_you.split())
            for term in terms:
                seen.append((term, term['name'] in object_terms))
            seen_terms.update(object_terms)
            o.seen_terms = seen
        for term in terms:
            if term['name'] not in seen_terms:
                term['hide'] = True
        self.context.update({
            'objects': objects,
            'types': sorted(set(o.type for o in Object.objects.filter(linking_you__isnull=False).exclude(linking_you=''))),
            'terms': terms,
        })
        return self.render()
