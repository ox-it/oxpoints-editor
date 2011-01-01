from __future__ import with_statement

from itertools import chain
import difflib
from datetime import date, datetime
import os, re

from xml.sax.saxutils import escape
from lxml import etree
from pprint import pprint

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.nonmultipart import MIMENonMultipart

from django.shortcuts import get_object_or_404
from django.contrib.auth.decorators import login_required, permission_required
from django.core.exceptions import PermissionDenied
from django.core.urlresolvers import reverse
from django.http import HttpResponseBadRequest
from django.conf import settings
from django.db import connection

from oxpeditor.utils.views import BaseView
from oxpeditor.utils.http import HttpResponseSeeOther
from .models import Object, Relation, File, RELATION_TYPE_CHOICES, RELATION_TYPE_INVERSE, RELATION_CONSTRAINTS
from . import forms
from .xslt import transform
from .utils import date_filter, svn_lock
from .commit import perform_commit
from .forms import get_forms, UpdateTypeForm, CommitForm, RequestForm
from .relation import RelationWrangler

class AuthedView(BaseView):
    def __call__(self, *args, **kwargs):
        return login_required(super(AuthedView, self).__call__)(*args, **kwargs)

class EditingView(BaseView):
    def __call__(self, request, *args, **kwargs):
        if not request.user.is_authenticated():
            return HttpResponseSeeOther(reverse(settings.LOGIN_URL))
        elif not request.user.has_perm('core.change_object'):
            response = self.render(request, {}, 'insufficient-privileges')
            print dir(response)
            response.status_code = 403
            return response
        else:
            return super(EditingView, self).__call__(request, *args, **kwargs)

class IndexView(BaseView):
    def handle_GET(self, request, context):
        return self.render(request, context, 'index')

class CommitView(EditingView):
    def initial_context(self, request):
        return {
            'form': CommitForm(request.POST or None),
        }

    def handle_GET(self, request, context):
        return self.render(request, context, 'commit')

    def handle_POST(self, request, context):
        if not context['form'].is_valid():
            return self.handle_GET(request, context)

        with svn_lock():
            perform_commit(request.user, context['form'].cleaned_data['message'])

        return HttpResponseSeeOther('.')

class DiffView(EditingView):
    def initial_context(self, request):
        edited = File.objects.filter(user=request.user)

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
        
    def handle_GET(self, request, context):
        return self.render(request, context, 'diff')

class ListView(EditingView):
    def initial_context(self, request):
        objects = Object.objects.all() #.order_by('-user')
        if 'type' in request.GET:
             objects = objects.filter(type=request.GET['type'])
        if 'q' in request.GET:
             objects = objects.filter(title__icontains=request.GET['q'])
        for n in ('finance', 'oucs', 'estates'):
            if n in request.GET:
                 objects = getattr(objects, 'filter' if request.GET[n] != 'yes' else 'exclude')(**{'idno_%s' % n: ''})
        if 'sort' in request.GET:
             objects = objects.order_by(*request.GET['sort'].split(','))
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

    def handle_GET(self, request, context):
        return self.render(request, context, 'list')

class TreeView(EditingView):
    def __init__(self, root_elem=None):
        self.root_elem = root_elem
        super(TreeView, self).__init__()

    def initial_context(self, request, oxpid=None):
        if oxpid:
            roots = Object.objects.filter(oxpid__in=oxpid.split(","))
            objects = chain(*(root.get_descendants(include_self=True) for root in roots))
            root = roots[0]
        else:
            objects = Object.tree.filter(root_elem=self.root_elem)
            root = None
        return {
            'objects': objects,
            'root': root,
        }

    def handle_GET(self, request, context, oxpid=None):
        return self.render(request, context, 'tree')

class DetailView(EditingView):
    def initial_context(self, request, oxpid):
        try:
            obj = Object.objects.get(oxpid=oxpid, user__isnull=False)
        except Object.DoesNotExist:
            obj = get_object_or_404(Object, oxpid=oxpid)

        if not obj.in_file:
            raise PermissionDenied("This object is not yet available to edit.")

        xml = etree.fromstring(obj.in_file.xml).xpath("descendant-or-self::*[@oxpID='%s']" % oxpid)[0]
        forms = get_forms(xml, request.POST or None)
        
        relations = []
        for name, label in RELATION_TYPE_CHOICES:
            active_constraint, passive_constraint, _, passive_cardinality = RELATION_CONSTRAINTS[name]
            if obj.satisfies(active_constraint): 
                relations.append({
                    'name': name,
                    'label': label,
                    'relations': obj.active_relations.filter(type=name).order_by('passive__sort_title').select_related('active', 'passive'),
                    'cardinality': passive_cardinality,
                    'constraint': passive_constraint,
                })

        return {
            'object': obj,
            'forms': forms,
            'management_forms': [fs.management_form for fs in forms.values()],
            'active_relations': obj.active_relations.order_by('type', 'passive__sort_title').select_related('passive'),
            'passive_relations': obj.passive_relations.order_by('type', 'active__sort_title').select_related('active'),
            'relations': relations,
            'update_type_form': UpdateTypeForm(request.POST or None),
            'editable': 'to' not in xml.attrib or (obj.user and obj.user != request.user),
        }

    def handle_GET(self, request, context, oxpid):
        recent = request.session.get('recent', [])
        if oxpid in recent:
            recent.remove(oxpid)
        recent.insert(0, oxpid)
        request.session['recent'] = recent[:10]
        return self.render(request, context, 'detail')

    def handle_POST(self, request, context, oxpid):
        if not context['editable']:
            return HttpResponseBadRequest()

        obj = context['object']
        root = etree.fromstring(obj.in_file.xml)
        xml = root.xpath("descendant-or-self::*[@oxpID='%s']" % oxpid)[0]

        if not (all([fs.is_valid() for fs in context['forms'].values()]) and context['update_type_form'].is_valid()):
            print [(fs.__class__, fs.is_valid()) for fs in context['forms'].values()], context['update_type_form'].is_valid()
            context['has_errors'] = True
            return self.handle_GET(request, context, oxpid)

        new_from = context['update_type_form'].cleaned_data['when']

        additions, removals, replacements = [], [], []

        forms = chain(*[fs.forms for fs in context['forms'].values()])
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

            new = form.serialize(cleaned_data, context['object'])

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
        
        self.wrangle_relations(request, context, oxpid, new_from)

        return HttpResponseSeeOther('.')
    
    def wrangle_relations(self, request, context, oxpid, new_from):
        rw = RelationWrangler(request.user)

        for rel in context['relations']:
            to_add, to_remove = set(), set()
            name = rel['name']
            if 'as_values_%s' % name in request.POST:
                old = set(r.passive.oxpid for r in rel['relations'])
                new = set(request.POST['as_values_%s' % name].split(','))
                to_add |= (new - old)
                to_remove |= (old - new)
            if 'reladd-%s' % name in request.POST:
                to_add |= set(passive.strip() for passive in request.POST['reladd-%s' % name])
            to_remove |= set(r.split('-')[-1] for r in request.POST if r.startswith('reldel-%s-' % name))
        
            to_add = set(o.oxpid for o in Object.objects.filter(oxpid__in=to_add, **rel['constraint'])) 
            to_remove = set(r.passive.oxpid for r in Relation.objects.filter(active__oxpid=oxpid, passive__oxpid__in=to_remove, type=name))
            
            for passive in to_add:
                rw.add(oxpid, passive, name, dt_from=new_from)
            for passive in to_remove:
                rw.remove(oxpid, passive, name, dt_to=new_from)
                
        rw.save()

class RequestView(AuthedView):
    def initial_context(self, request):
        return {
            'form': RequestForm(request.POST or None, request.FILES or None),
            'sent': request.GET.get('sent') == 'true',
        }

    def handle_GET(self, request, context):
        return self.render(request, context, 'request')

    def handle_POST(self, request, context):
        form, user = context['form'], request.user
        if not form.is_valid():
            return self.handle_GET(request, context)

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

class AutoSuggestView(EditingView):
    def initial_context(self, request, name):
        try:
            _, constraint, _, _ = RELATION_CONSTRAINTS[name]
        except KeyError:
            raise Http404
        
        return [{
                 'value': obj.oxpid,
                 'name': obj.autosuggest_title,
            } for obj in Object.objects.filter(autosuggest_title__icontains=request.GET.get('q', ''), **constraint)]

    def handle_GET(self, request, context, name):
        return self.render_json(request, context, None)
