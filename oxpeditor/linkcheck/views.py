from django.views.generic import TemplateView

from oxpeditor.core.views import EditingMixin
from oxpeditor.linkcheck.models import Link, STATE_CHOICES, PROBLEM_CHOICES


class LinkView(EditingMixin, TemplateView):
    template_name = 'links.html'

    def get(self, request):
        links = Link.objects.all().order_by('object__title', 'type').select_related('object')

        if 'state' in request.GET:
            links = links.filter(state__in=request.GET.getlist('state'))
        if 'problem' in request.GET:
            links = links.filter(problem__in=request.GET.getlist('problem'))

        self.context.update({
            'links': links,
            'state_choices': STATE_CHOICES,
            'problem_choices': PROBLEM_CHOICES,
        })
        return self.render()