from firstapp.models import WholePage, Egrul
import json


class ScrapyAppPipeline(object):
    def __init__(self, unique_id, *args, **kwargs):
        self.unique_id = unique_id
        self.items = []

    @classmethod
    def from_crawler(cls, crawler):
        return cls(
            unique_id=crawler.settings.get('unique_id'),  # this will be passed from django view
        )

    def close_spider(self, spider):
        # And here we are saving our crawled data with django models.
        item = WholePage()
        item.unique_id = self.unique_id
        item.data = json.dumps(self.items)
        item.save()

    def process_item(self, item, spider):
        self.items.append(item['url'])
        return item


class EgrulPipeline(object):
    def __init__(self, unique_id, *args, **kwargs):
        self.unique_id = unique_id
        self._inner_obj = Egrul(unique_id=unique_id)

    @classmethod
    def from_crawler(cls, crawler):
        return cls(
            unique_id=crawler.settings.get('unique_id'),  # this will be passed from django view
        )

    def close_spider(self, spider):
        # And here we are saving our crawled data with django models.
        self._inner_obj.save()

    def process_item(self, item, spider):
        self._inner_obj.inn = item['rows']['INN']
        self._inner_obj.name = item['rows']['NAME']
        self._inner_obj.ogrn = item['rows']['OGRN']
        return item
