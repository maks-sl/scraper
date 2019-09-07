import random

import requests
from django.core.management.base import BaseCommand, CommandError
from firstapp.models import Avito, AvitoResult
import pika
from bs4 import BeautifulSoup
from django.db.models import F
from django.db.models.aggregates import Max


class Command(BaseCommand):
    help = 'Start listening check queue on localhost'

    good_proxies = [
        '116.66.197.228:8080',
        '85.133.207.14:56728',
        '122.54.101.69:8080',
        '85.132.12.75:42627',
        '188.242.5.172:8080',
        '50.246.69.60:32767'
    ]

    headers = {
        'user-agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/71.0.3578.80 Safari/537.36'}

    # def add_arguments(self, parser):
    #     parser.add_argument('poll_id', nargs='+', type=int)

    def callback(self, ch, method, properties, body):
        uq_id = body.decode("utf-8")
        try:
            avito_result = AvitoResult.objects.annotate(last_result_pk=Max('avito__avitoresult__pk')).filter(
                pk=F('last_result_pk'), avito__unique_id=uq_id, status=AvitoResult.STATUS_CHECK).first()
            avito = avito_result.avito
        except (Avito.DoesNotExist, AvitoResult.DoesNotExist):
            self.stdout.write(self.style.ERROR('Can\' run check task properly. "%s"' % uq_id))
            # raise CommandError('Avito "%s" does not exist' % uq_id)
            return
        try:
            proxy = random.choice(self.good_proxies)
            request = requests.get(avito.url, headers=self.headers, proxies={'https': 'https://'+proxy})
            if not request.status_code == 200:
                new_result = AvitoResult(avito=avito, status=AvitoResult.STATUS_CHECK_NOT_OK, price=None)
                new_result.save()
                self.stdout.write(self.style.SUCCESS('Avito "%s" RESPONSE IS NOT OK (200)' % avito.unique_id))
                return
            html_soup = BeautifulSoup(request.content, features='html.parser')
        except requests.exceptions.ConnectionError:
            new_result = AvitoResult(avito=avito, status=AvitoResult.STATUS_CHECK_ERROR, price=None)
            new_result.save()
            self.stdout.write(self.style.SUCCESS('Avito "%s" CONNECTION ERROR' % avito.unique_id))
            return
        try:
            price = int(html_soup.findAll("span", {"class": "js-item-price"})[0].get_text().replace(" ", ""))
            new_result = AvitoResult(avito=avito, status=AvitoResult.STATUS_CHECK, price=price)
            new_result.save()
            self.stdout.write(self.style.SUCCESS('Avito "%s" price "%s"' % (avito.unique_id, price)))
        except IndexError as e:
            # self.stdout.write(self.style.ERROR(str(content)))
            self.stdout.write(self.style.ERROR(str(e)))
            new_result = AvitoResult(avito=avito, status=AvitoResult.STATUS_CHECK_ERROR, price=None)
            new_result.save()
            self.stdout.write(self.style.SUCCESS('Avito "%s" ERROR' % avito.unique_id))

    def handle(self, *args, **options):
        connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
        channel = connection.channel()
        channel.queue_declare(queue='check')
        channel.basic_consume(self.callback,
                              queue='check',
                              no_ack=True)
        self.stdout.write(self.style.SUCCESS(' [*] Waiting for check messages. To exit press CTRL+C'))
        channel.start_consuming()
