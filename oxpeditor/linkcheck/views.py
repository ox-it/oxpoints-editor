from django.views.generic import TemplateView

from oxpeditor.core.views import EditingMixin
from oxpeditor.linkcheck.models import Link, STATE_CHOICES, PROBLEM_CHOICES


class LinkView(EditingMixin, TemplateView):
    template_name = 'links.html'

    def get_context_data(self, **kwargs):
        links = Link.objects.all().order_by('object__title', 'type').select_related('object')

        if 'state' in self.request.GET:
            links = links.filter(state__in=self.request.GET.getlist('state'))
        if 'problem' in self.request.GET:
            links = links.filter(problem__in=self.request.GET.getlist('problem'))

        return {
            'links': links,
            'state_choices': STATE_CHOICES,
            'problem_choices': PROBLEM_CHOICES,
        }
