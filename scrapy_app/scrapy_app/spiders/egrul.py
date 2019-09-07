# -*- coding: utf-8 -*-
from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule
from scrapy.spider import BaseSpider
import json


class EgrulSpider(BaseSpider):
    name = 'egrul'

    def __init__(self, *args, **kwargs):
        # We are going to pass these args from our django view.
        # To make everything dynamic, we need to override them inside __init__ method

        # self.url = kwargs.get('url')
        self.url = 'https://egrul.nalog.ru/'
        # self.domain = kwargs.get('domain')
        self.domain = 'egrul.nalog.ru'
        self.start_urls = [self.url]

        self.inn = kwargs.get('inn')
        # self.allowed_domains = [self.domain]

        # IcrawlerSpider.rules = [
        #     Rule(LinkExtractor(unique=True), callback='parse_item'),
        # ]
        super(EgrulSpider, self).__init__(*args, **kwargs)

    def parse(self, response):
        # WAIT JSON
        items = []
        jsonresponse = json.loads(response.body_as_unicode())
        used_captcha = jsonresponse["query"]["captcha"]
        rows = jsonresponse["rows"]
        item = {'used_captcha': used_captcha, 'rows': rows}
        items.append(item)
        return items

