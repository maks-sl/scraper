"""scraper URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/2.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path
from django.conf.urls import url, include
from firstapp.views import index, job_list, crawl, \
    task_info, inn_form, TaskList, run_avito, list_avito, view_avito, start_check_avito

urlpatterns = [
    path('', index, name='home'),
    url(r'^accounts/', include('django.contrib.auth.urls')),
    path('admin/', admin.site.urls),

    path('scrapy-go/', inn_form, name='scrapy-go'),
    url(r'^api/crawl/', crawl),
    path('scrapy-job-list/', job_list, name='scrapy-job-list'),
    url(r'^tlist/$', TaskList.as_view(), name='scrapy-tlist'),
    url(r'^task/(?P<task_id>[\w+|-]+)/(?P<unique_id>[\w+|-]+)/$', task_info, name='scrapy-task-info'),

    url(r'^avito-run/$', run_avito, name='avito-run'),
    url(r'^avito-list/', list_avito, name='avito-list'),
    url(r'^avito-view/(?P<id>[\w+|-]+)/$', view_avito, name='avito-view'),
    url(r'^avito-start-check/(?P<id>[\w+|-]+)/$', start_check_avito, name='avito-start-check'),
]
