import urllib.request

import requests
from django.core.management.base import BaseCommand, CommandError
from requests.exceptions import ProxyError

from firstapp.models import Avito, AvitoResult
import pika
from bs4 import BeautifulSoup
from time import sleep
import random


class Command(BaseCommand):
    help = 'Start listening avito queue on localhost'

    # def add_arguments(self, parser):
    #     parser.add_argument('poll_id', nargs='+', type=int)

    proxy_list = [
        '116.66.197.228:8080',
        '85.133.207.14:56728',
        '122.54.101.69:8080',
        '85.132.12.75:42627',
        '188.242.5.172:8080',
        '50.246.69.60:32767'
    ]

    headers = {
        'user-agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/71.0.3578.80 Safari/537.36'}

    good_proxies = []

    def callback(self, ch, method, properties, body):
        uq_id = body.decode("utf-8")

        try:
            avito = Avito.objects.get(unique_id=uq_id)
            avito_result = AvitoResult.objects.get(avito=avito, status=AvitoResult.STATUS_NEW)
        except (Avito.DoesNotExist, AvitoResult.DoesNotExist):
            self.stdout.write(self.style.ERROR('Can\' run new task "%s" db item does not exist' % uq_id))
            # raise CommandError('Avito "%s" does not exist' % uq_id)
            return
        try:
            proxy = random.choice(self.good_proxies)
            request = requests.get(avito.url, headers=self.headers, proxies={'https': 'https://'+proxy})
            if not request.status_code == 200:
                new_result = AvitoResult(avito=avito, status=AvitoResult.STATUS_NEW_NOT_OK, price=None)
                new_result.save()
                self.stdout.write(self.style.SUCCESS('Avito "%s" RESPONSE IS NOT OK (200)' % avito.unique_id))
                return
            html_soup = BeautifulSoup(request.content, features='html.parser')
        except requests.exceptions.ConnectionError:
            new_result = AvitoResult(avito=avito, status=AvitoResult.STATUS_NEW_ERROR, price=None)
            new_result.save()
            self.stdout.write(self.style.SUCCESS('Avito "%s" CONNECTION ERROR' % avito.unique_id))
            return
        try:
            price = int(html_soup.findAll("span", {"class": "js-item-price"})[0].get_text().replace(" ", ""))
            new_result = AvitoResult(avito=avito, status=AvitoResult.STATUS_CHECK, price=price)  # STATUS NEW ##
            new_result.save()
            self.stdout.write(self.style.SUCCESS('Avito "%s" price "%s"' % (avito.unique_id, price)))
        except IndexError as e:
            # self.stdout.write(self.style.ERROR(str(content)))
            self.stdout.write(self.style.ERROR(str(e)))
            new_result = AvitoResult(avito=avito, status=AvitoResult.STATUS_NEW_ERROR, price=None)
            new_result.save()
            self.stdout.write(self.style.SUCCESS('Avito "%s" ERROR' % avito.unique_id))
        sleep(random.randint(0, 70)*0.01)

    def handle(self, *args, **options):
        for addr in self.proxy_list:
            try:
                print('Check proxy '+addr+' ... ', end='')
                requests.get('https://ya.ru', proxies={'https': 'https://'+addr})
            except ProxyError:
                print("BAD")
            else:
                print("OK")
                self.good_proxies.append(addr)
        bad_percent = len(self.good_proxies)/len(self.proxy_list)*100
        print('Good proxies: '+str(bad_percent)+' % ('+str(len(self.good_proxies))+')')

        connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
        channel = connection.channel()
        channel.queue_declare(queue='avito')
        channel.basic_consume(self.callback,
                              queue='avito',
                              no_ack=True)
        self.stdout.write(self.style.SUCCESS(' [*] Waiting for new messages. To exit press CTRL+C'))
        channel.start_consuming()
