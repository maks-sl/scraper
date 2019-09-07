# -*- coding: utf-8 -*-

# Define here the models for your spider middleware
#
# See documentation in:
# https://doc.scrapy.org/en/latest/topics/spider-middleware.html

from scrapy import signals
from scrapy.http.response.html import HtmlResponse
import sys
import json
# import dryscrape
import tempfile
import pytesseract
from PIL import Image
import logging
import os
from time import sleep
from selenium import webdriver
from pyvirtualdisplay import Display
from selenium import webdriver
from io import BytesIO
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options

logger = logging.getLogger(__name__)


class EgrulMiddleware(object):

    def process_request(self, request, spider):
        spider.logger.info('GETTING URL: %s' % request.url)

        if spider.name == 'egrul':
            spider.logger.info('ITS EGRUL !')
            inn = spider.inn

            # USUALLY CHROME
            # browser = splinter.Browser('chrome')

            # FLASK
            # app = Flask(__name__)
            # browser = splinter.Browser('flask', app=app)

            # MOBILE EMULATION
            # mobile_emulation = {"deviceName": "Nexus 5"}
            # chrome_options = webdriver.ChromeOptions()
            # chrome_options.add_experimental_option("mobileEmulation",
            #                                        mobile_emulation)
            # browser = Browser('chrome', options=chrome_options)

            options = Options()
            options.add_argument("disable-infobars")
            options.add_argument("--disable-extensions")
            options.add_argument("--disable-dev-shm-usage")
            options.add_argument("--no-sandbox")

            # pyvirtualdisplay

            display = Display(visible=False, size=(640, 1024), color_depth=8)
            display.start()
            driver = webdriver.Chrome(chrome_options=options)
            spider.logger.info('now Chrome will run in a virtual display')

            try:

                # EGRUL WORKS KEYS
                driver.get('https://egrul.nalog.ru/')
                search_box = driver.find_element_by_id('ogrninnul')
                for x in inn:
                    search_box.send_keys(x)

                # driver.find_element_by_css_selector('.buttons button.float-right').send_keys(Keys.NULL)
                driver.execute_script("window.scrollTo(0, 400)")

                # now that we have the preliminary stuff out of the way time to get that image :D
                element = driver.find_element_by_css_selector('.captcha-field img')  # find part of the page you want image of
                location = element.location
                size = element.size
                png = driver.get_screenshot_as_png()  # saves screenshot of entire page

                im = Image.open(BytesIO(png))  # uses PIL library to open image in memory

                left = location['x']
                top = location['y'] - 400
                right = left + size['width']
                bottom = top + size['height']
                im.save('screenshot-full.png')  # saves full image
                im = im.crop((left, top, right, bottom))  # defines crop points
                im.save('screenshot.png')  # saves new cropped image

                # logger.debug(f'TRY SOLVE CAPTCHA')
                # captcha = pytesseract.image_to_string(im)
                # logger.debug(f'Solved captcha: "{captcha}"')

                # WAIT FOR CAPTCHA INPUT
                driver.find_element_by_css_selector('#captcha').click()
                # sleep(11)

                driver.find_element_by_css_selector('.buttons button.float-right').click()

                sleep(20)
                name = driver.find_element_by_css_selector('#resultContent tbody td:first-child a').text
                res = driver.find_elements_by_css_selector('#resultContent tbody td:not(:first-child)')
                addr = res[0].text
                ogrn = res[1].text
                inn = res[2].text
                kpp = res[3].text
                assign_date = res[4].text
                inspire_date = res[5].text
                uvvalid_date = res[6].text

                # NEW TASK INIT
                # driver.get('http://127.0.0.1:8000/go/')
                # search_box = driver.find_element_by_id('id_inn')
                # search_box.send_keys(int(inn)+1)
                # search_box.submit()

                # SPLINTER
                # asd = browser.visit('http://127.0.0.1:8000/go/')
                # spider.logger.info(asd)
                # shot = browser.screenshot('egrul-screenshots/')
                # spider.logger.info('SSHOT' + shot)
                # browser.find_by_id('id_inn').first.fill('7840486195')
                # browser.find_by_id('subm_inn').first.click()
                # browser.execute_script("$('body').empty()")
                
            finally:
                driver.quit()
                display.stop()


            dict1 = {
                "query":
                {
                    "captcha": "YES",
                },
                "rows":
                {
                    "INN": inn,
                    "NAME": name,
                    "OGRN": ogrn,
                    "ADRESTEXT": addr,
                    "DTREG": assign_date,
                    "KPP": kpp
                }
            }
            content = json.dumps(dict1)
            return HtmlResponse(request.url, body=content, encoding='UTF-8')

        return None

    def process_response(self, request, response, spider):
        return response

    @classmethod
    def from_crawler(cls, crawler):
        # This method is used by Scrapy to create your spiders.
        s = cls()
        crawler.signals.connect(s.spider_opened, signal=signals.spider_opened)
        return s

    def spider_opened(self, spider):
        spider.logger.info('Spider opened: %s' % spider.name)


# class FirstMiddleware(object):
#
#     def __init__(self, settings):
#
#         # start xvfb to support headless scraping
#         # if 'linux' in sys.platform:
#         dryscrape.start_xvfb()
#
#         self.dryscrape_session = dryscrape.Session(base_url='https://egrul.nalog.ru/')
#
#         logger.debug(f'DRYSCRAPE: "{type(self.dryscrape_session)}"')
#
#         # for key, value in settings['DEFAULT_REQUEST_HEADERS'].items():
#         #     # seems to be a bug with how webkit-server handles accept-encoding
#         #     if key.lower() != 'accept-encoding':
#         #         self.dryscrape_session.set_header(key, value)
#
#     def bypass_threat_defense(self, url=None):
#         # only navigate if any explicit url is provided
#         if url:
#             self.dryscrape_session.visit(url)
#
#         # solve the captcha if there is one
#         # captcha_images = self.dryscrape_session.css('img[src *= captcha]')
#         captcha_images = self.dryscrape_session.css('.captcha-field img')
#         if len(captcha_images) > 0:
#             return self.solve_captcha(captcha_images[0])
#
#         # # click on any explicit retry links
#         # retry_links = self.dryscrape_session.css('a[href *= threat_defense]')
#         # if len(retry_links) > 0:
#         #     return self.bypass_threat_defense(retry_links[0].get_attr('href'))
#         #
#         # # otherwise, we're on a redirect page so wait for the redirect and try again
#         # self.wait_for_redirect()
#         # return self.bypass_threat_defense()
#
#     def solve_captcha(self, img, width=1280, height=800):
#         # take a screenshot of the page
#         self.dryscrape_session.set_viewport_size(width, height)
#         filename = tempfile.mktemp(suffix='.png')
#         self.dryscrape_session.render(filename, width, height)
#
#         # inject javascript to find the bounds of the captcha
#         js = 'document.querySelector(".captcha-field img").getBoundingClientRect()'
#         rect = self.dryscrape_session.eval_script(js)
#         box = (int(rect['left']), int(rect['top']), int(rect['right']), int(rect['bottom']))
#
#         # solve the captcha in the screenshot
#         logger.debug(f'TRY SOLVE CAPTCHA')
#         image = Image.open(filename)
#         os.unlink(filename)
#         captcha_image = image.crop(box)
#         captcha = pytesseract.image_to_string(captcha_image)
#         logger.debug(f'Solved the captcha: "{captcha}"')
#
#         # submit the captcha
#         input_f = self.dryscrape_session.css('#captcha')[0]
#         input_f.set(captcha)
#         button = self.dryscrape_session.css('.btn-ok')[0]
#         url = self.dryscrape_session.url()
#         button.click()
#
#         # # try again if it we redirect to a threat defense URL
#         # if self.is_threat_defense_url(self.wait_for_redirect(url)):
#         #     return self.bypass_threat_defense()
#
#         # otherwise return the cookies as a dict
#         # cookies = {}
#         # for cookie_string in self.dryscrape_session.driver.body():
#         #     if 'domain=zipru.to' in cookie_string:
#         #         key, value = cookie_string.split(';')[0].split('=')
#         #         cookies[key] = value
#         return self.dryscrape_session.driver.body()
#
#     def process_request(self, request, spider):
#         spider.logger.info('GETTING URL: %s' % request.url)
#
#         if (request.url == 'https://egrul.nalog.ru/'):
#             spider.logger.info('INTO SOLVING')
#             solve = self.bypass_threat_defense(request.url)
#             spider.logger.info('SOLVE: %s' % solve)
#             content = b'<a href="https://egrul.nalog.ru/">s</a>'
#             return HtmlResponse(request.url, body=content, encoding='UTF-8')
#             # return HtmlResponse(json.dumps({'key': '<a href="http://www.plans.ru/projects">s</a>'}))
#
#         return None
#
#     def process_response(self, request, response, spider):
#         return response
#
#     @classmethod
#     def from_crawler(cls, crawler):
#         # This method is used by Scrapy to create your spiders.
#         s = cls(crawler.settings)
#         crawler.signals.connect(s.spider_opened, signal=signals.spider_opened)
#         return s
#
#     def spider_opened(self, spider):
#         spider.logger.info('Spider opened: %s' % spider.name)


class ScrapyAppSpiderMiddleware(object):
    # Not all methods need to be defined. If a method is not defined,
    # scrapy acts as if the spider middleware does not modify the
    # passed objects.

    @classmethod
    def from_crawler(cls, crawler):
        # This method is used by Scrapy to create your spiders.
        s = cls()
        crawler.signals.connect(s.spider_opened, signal=signals.spider_opened)
        return s

    def process_spider_input(self, response, spider):
        # Called for each response that goes through the spider
        # middleware and into the spider.

        # Should return None or raise an exception.
        return None

    def process_spider_output(self, response, result, spider):
        # Called with the results returned from the Spider, after
        # it has processed the response.

        # Must return an iterable of Request, dict or Item objects.
        for i in result:
            yield i

    def process_spider_exception(self, response, exception, spider):
        # Called when a spider or process_spider_input() method
        # (from other spider middleware) raises an exception.

        # Should return either None or an iterable of Response, dict
        # or Item objects.
        pass

    def process_start_requests(self, start_requests, spider):
        # Called with the start requests of the spider, and works
        # similarly to the process_spider_output() method, except
        # that it doesn’t have a response associated.

        # Must return only requests (not items).
        for r in start_requests:
            yield r

    def spider_opened(self, spider):
        spider.logger.info('Spider opened: %s' % spider.name)


class ScrapyAppDownloaderMiddleware(object):
    # Not all methods need to be defined. If a method is not defined,
    # scrapy acts as if the downloader middleware does not modify the
    # passed objects.

    @classmethod
    def from_crawler(cls, crawler):
        # This method is used by Scrapy to create your spiders.
        s = cls()
        crawler.signals.connect(s.spider_opened, signal=signals.spider_opened)
        return s

    def process_request(self, request, spider):
        # Called for each request that goes through the downloader
        # middleware.

        # Must either:
        # - return None: continue processing this request
        # - or return a Response object
        # - or return a Request object
        # - or raise IgnoreRequest: process_exception() methods of
        #   installed downloader middleware will be called
        return None

    def process_response(self, request, response, spider):
        # Called with the response returned from the downloader.

        # Must either;
        # - return a Response object
        # - return a Request object
        # - or raise IgnoreRequest
        return response

    def process_exception(self, request, exception, spider):
        # Called when a download handler or a process_request()
        # (from other downloader middleware) raises an exception.

        # Must either:
        # - return None: continue processing this exception
        # - return a Response object: stops process_exception() chain
        # - return a Request object: stops process_exception() chain
        pass

    def spider_opened(self, spider):
        spider.logger.info('Spider opened: %s' % spider.name)
