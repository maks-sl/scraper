from django.http import HttpResponse
from django.urls import reverse
from django.views import generic

from firstapp.models import Scraper, Avito, AvitoResult
from uuid import uuid4
from urllib.parse import urlparse
from django.core.validators import URLValidator
from django.core.exceptions import ValidationError
from django.views.decorators.http import require_POST, require_http_methods
from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.http import HttpResponseRedirect
from django.views.decorators.csrf import csrf_exempt
from scrapyd_api import ScrapydAPI
# from firstapp.utils import URLUtil
from firstapp.models import WholePage, Task
from firstapp import helpers
from django import forms
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django_tables2 import RequestConfig
from firstapp.tables import TaskTable, AvitoTable, AvitoResultTable, AvitoViewHistory
from django.core.mail import send_mail, BadHeaderError
import pika

scrapyd = ScrapydAPI('http://localhost:6800')


class TaskList(LoginRequiredMixin, generic.ListView):
    """
    Generic class-based view listing books on loan to current user.
    """
    model = Task
    template_name = 'scrapy_tasks_list.html'
    paginate_by = 10

    def get_queryset(self):
        return Task.objects.filter(user=self.request.user).order_by('date')


class UrlForm(forms.Form):
    url = forms.CharField(max_length=50)


class InnForm(forms.Form):
    inn = forms.CharField(max_length=13)


class AksCallForm(forms.Form):
    name = forms.CharField(max_length=15)
    phone = forms.CharField(max_length=15)


class AvitoForm(forms.Form):
    url = forms.CharField(max_length=512)


def is_valid_url(url):
    validate = URLValidator()
    try:
        validate(url)  # check if url format is valid
    except ValidationError:
        return False
    return True


def index(request):
    crawler_inn_form = InnForm()
    return render(request, "index.html")


@csrf_exempt
@require_http_methods(['POST'])  # only post
def crawl(request):
    # url = request.POST.get('url', None)  # take url comes from client. (From an input may be?)
    inn = request.POST.get('inn', None)  # take inn comes from client.
    url = 'https://egrul.nalog.ru/'

    if not inn:
        return JsonResponse({'error': 'Missing  inn'})

    # if not is_valid_url(url):
    #     return JsonResponse({'error': 'URL is invalid'})

    domain = urlparse(url).netloc  # parse the url and extract the domain
    unique_id = str(uuid4())  # create a unique ID.

    # This is the custom settings for scrapy spider.
    # We can send anything we want to use it inside spiders and pipelines.
    # I mean, anything
    settings = {
        'unique_id': unique_id,  # unique ID for each record for DB
        'USER_AGENT': 'Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)'
    }
    # name = 'icrawler'
    name = 'egrul'

    # Here we schedule a new crawling task from scrapyd.
    # Notice that settings is a special argument name.
    # But we can pass other arguments, though.
    # This returns a ID which belongs and will be belong to this task
    # We are goint to use that to check task's status.

    # task = scrapyd.schedule('default', 'icrawler',
    #                         settings=settings, url=url, domain=domain)

    # task_id = helpers.new_task_id(name, settings, url, domain)
    task_id = scrapyd.schedule('default', name, settings=settings, url=url, domain=domain, inn=inn)

    new_task = Task(user=request.user, name=name, task_id=task_id, unique_id=unique_id)
    new_task.save()

    # return redirect('/api/crawl?task_id=' + task_id + '&unique_id=' + unique_id)

    # return JsonResponse(
    #     {
    #         'task_id': task,
    #         'unique_id': unique_id,
    #         'status': 'started',
    #         'url': '/crawl?task_id='+task_id+'&unique_id='+unique_id
    #     }
    # )

    return redirect('/list')


@require_http_methods(['GET'])  # only get
def task_info(request, task_id, unique_id):

    if not task_id or not unique_id:
        return JsonResponse({'error': 'Missing args'})

    # Here we check status of crawling that just started a few seconds ago.
    # If it is finished, we can query from database and get results
    # If it is not finished we can return active status
    # Possible results are -> pending, running, finished
    status = scrapyd.job_status('default', task_id)
    if status == 'finished' or status is '':
        try:
            # this is the unique_id that we created even before crawling started.
            item = WholePage.objects.get(unique_id=unique_id)
            return JsonResponse({'data': item.to_dict['data'], 'date': item.date, 'status': status})
        except Exception as e:
            return JsonResponse({'error': str(e)})
    else:
        return JsonResponse({'status': status})


@login_required
def job_list(request):
    table = TaskTable(Task.objects.filter(user=request.user).order_by('-date'))
    RequestConfig(request).configure(table)
    return render(request, "scrapy_list.html", {'table': table})


def inn_form(request):
    crawler_inn_form = InnForm()
    return render(request, "scrapy_inn_form.html", {"crawler_inn_form": crawler_inn_form})


@csrf_exempt
@login_required
def run_avito(request):
    form = AvitoForm()
    if request.method == 'POST':
        form = AvitoForm(request.POST)
        if form.is_valid():
            unique_id = str(uuid4())  # create a unique ID.
            new_avito = Avito(user=request.user, unique_id=unique_id, url=form.cleaned_data['url'])
            new_avito.save()
            avito_result = AvitoResult(avito=new_avito, status=AvitoResult.STATUS_NEW, price=None)
            avito_result.save()

            # go pika
            connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
            channel = connection.channel()
            channel.queue_declare(queue='avito')
            channel.basic_publish(exchange='', routing_key='avito', body=unique_id)
            connection.close()

            return redirect('avito-list')
    return render(request, "avito_form.html", {"avito_form": form})


@login_required
def list_avito(request):

    from django.db.models import F
    from django.db.models.aggregates import Max

    avito_results = AvitoResult.objects.annotate(last_result_pk=Max('avito__avitoresult__pk')).filter(pk=F('last_result_pk')).order_by('-id')

    # table = AvitoTable(Avito.objects.filter(user=request.user).order_by('-id'))
    table = AvitoResultTable(avito_results)
    RequestConfig(request).configure(table)
    return render(request, "avito_list.html", {'table': table})


@login_required
def view_avito(request, id):
    avito = Avito.objects.get(id=id)
    history_table = AvitoViewHistory(AvitoResult.objects.filter(avito__user=request.user, avito_id=id).order_by('-id'))
    RequestConfig(request).configure(history_table)
    return render(request, "avito_view.html", {'avito': avito, 'history_table': history_table})


@login_required
def start_check_avito(request, id):
    avito = Avito.objects.get(id=id)
    last_result = AvitoResult.objects.filter(avito__user=request.user, avito_id=id).order_by('-id').first()
    if last_result.status == AvitoResult.STATUS_NEW_RESULT:
        new_result = AvitoResult(avito=avito, status=AvitoResult.STATUS_CHECK, price=last_result.price)
        new_result.save()
    return redirect(reverse('avito-view', kwargs={'id': id}))
