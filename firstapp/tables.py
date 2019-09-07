import django_tables2 as tables
from firstapp.models import Egrul, Task, Avito, AvitoResult
from django_tables2.utils import A

from django.utils.safestring import mark_safe
from django.utils.html import escape
from django.urls import reverse


class TaskTable(tables.Table):
    unique_id = tables.Column(orderable=False)
    task_id = tables.Column(orderable=False)
    get_task_status = tables.Column(orderable=False)
    is_has_stuff = tables.BooleanColumn(orderable=False)
    link = tables.LinkColumn('scrapy-task-info', text='static text', args=[A('unique_id'), A('task_id')])
    date = tables.DateTimeColumn()

    class Meta:
        model = Task
        # template_name = 'django_tables2/bootstrap.html'
        fields = ['get_task_status', 'is_has_stuff', 'date']


class AvitoTable(tables.Table):
    unique_id = tables.Column(orderable=False)
    url = tables.Column(orderable=False)
    # get_task_status = tables.Column(orderable=False)
    # link = tables.LinkColumn('task_info', text='static text', args=[A('unique_id'), A('task_id')])
    # date = tables.DateTimeColumn()

    class Meta:
        model = Avito
        # template_name = 'django_tables2/bootstrap.html'
        # fields = ['get_task_status', 'is_has_stuff', 'date']


class AvitoResultTable(tables.Table):
    link = tables.LinkColumn('avito-view', text='static text', args=[A('avito.id')])
    # created_at = tables.DateTimeColumn()

    class Meta:
        model = AvitoResult
        fields = ['avito.url', 'price', 'status']


class ActionsColumn(tables.Column):
    empty_values = list()

    def render(self, value, record):
        if record.status == AvitoResult.STATUS_NEW_RESULT and record.is_last:
            return mark_safe('<a href="' + reverse('avito-start-check', kwargs={'id': record.avito.id}) + '" id="%s" class="button is-primary is-block is-small">Start check</a>' % escape(record.id))
        return ''


class AvitoViewHistory(tables.Table):
    price = tables.Column(orderable=False)
    status = tables.Column(orderable=False)
    created_at = tables.DateTimeColumn()
    actions = ActionsColumn()

    class Meta:
        model = AvitoResult
        fields = ['price', 'status']

