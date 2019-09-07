import requests
from django.core.management.base import BaseCommand, CommandError
from firstapp.models import Avito, AvitoResult
import pika
from bs4 import BeautifulSoup
from django.db.models import F
from django.db.models.aggregates import Max
from datetime import datetime, timedelta


class Command(BaseCommand):
    help = 'Start sending to check queue on localhost'

    def handle(self, *args, **options):
        connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
        channel = connection.channel()
        channel.queue_declare(queue='check')

        time_threshold = datetime.now() - timedelta(minutes=3)
        to_check = AvitoResult.objects.annotate(
            last_result_pk=Max('avito__avitoresult__pk')
        ).filter(pk=F('last_result_pk'), status=AvitoResult.STATUS_CHECK, created_at__lt=time_threshold)
        if not to_check.exists():
            self.stdout.write(self.style.SUCCESS('No outdated now'))
        for ar in to_check:
            channel.basic_publish(exchange='',
                                  routing_key='check',
                                  body=ar.avito.unique_id)
            self.stdout.write(self.style.SUCCESS('Avito "%s" go to check queue' % ar.avito.unique_id))
        connection.close()
