from django_conneg.views import HTMLView
from oxpeditor.core.views import EditingMixin
from oxpeditor.linkcheck.models import Link


class LinkView(EditingMixin, HTMLView):
    template_name = 'links'

    def get(self, request):
        links = Link.objects.all().order_by('object__title', 'type')

        if 'state' in request.GET:
            links = links.filter(state__in=request.GET.getlist('state'))
        if 'problem' in request.GET:
            links = links.filter(problem__in=request.GET.getlist('problem'))

        self.context.update({
            'links': links,
        })
        return self.render()