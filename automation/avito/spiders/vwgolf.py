# -*- coding: utf-8 -*-
import scrapy
from scrapy.selector.unified import Selector


class VwgolfSpider(scrapy.Spider):

    name = 'vwgolf'
    allowed_domains = ['avito.ru']
    # start_urls = ['http://avito.ru/']

    def start_requests(self):
        urls = [
            'https://www.avito.ru/rossiya/avtomobili/volkswagen/golf_gti',
        ]
        for url in urls:
            yield scrapy.Request(url=url, callback=self.parse)

    def parse(self, response):
        for item in response.css('div.item'):
            yield {
                'name': item.css('.item-description-title-link::attr(href)').extract_first(),
            }
        next_page = response.css('.js-pagination-next::attr(href)').extract_first()
        if next_page is not None:
            next_page = response.urljoin(next_page)
            print(next_page)
            yield scrapy.Request(next_page, callback=self.parse)
