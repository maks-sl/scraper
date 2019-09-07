import json
from django.db import models
from django.utils import timezone
from firstapp import helpers
from django.contrib.auth.models import User


class Scraper(models.Model):
    name = models.CharField(max_length=64)
    status = models.CharField(max_length=64)
    site = models.CharField(max_length=64)


class Avito(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=False)
    unique_id = models.CharField(max_length=100, null=False)
    url = models.CharField(max_length=512)

    # @property
    # def latest_result(self):
    #     if hasattr(self, 'result_list') and len(self.result_list) > 0:
    #         return self.result_list[0]
    #     return None


class AvitoResult(models.Model):
    STATUS_NEW = 'NEW'
    STATUS_NEW_RESULT = 'NEW_RESULT'
    STATUS_NEW_ERROR = 'NEW_ERROR'
    STATUS_NEW_NOT_OK = 'NEW_NOT_OK'
    STATUS_NEW_CANCELLED = 'NEW_CANCELLED'
    STATUS_CHECK = 'CHECK'
    STATUS_CHECK_ERROR = 'CHECK_ERROR'
    STATUS_CHECK_NOT_OK = 'CHECK_NOT_OK'
    STATUS_CHOICES = (
        (STATUS_NEW, 'New'),
        (STATUS_NEW_RESULT, 'New Result'),
        (STATUS_NEW_ERROR, 'New With Error'),
        (STATUS_NEW_NOT_OK, 'New Not OK'),
        (STATUS_NEW_CANCELLED, 'New Cancelled'),
        (STATUS_CHECK, 'In check'),
        (STATUS_CHECK_ERROR, 'Check Error'),
        (STATUS_CHECK_NOT_OK, 'Check Not OK'),
    )
    created_at = models.DateTimeField(auto_now_add=True)
    avito = models.ForeignKey(Avito, on_delete=models.CASCADE, null=False)
    status = models.CharField(max_length=16, choices=STATUS_CHOICES)
    price = models.IntegerField(null=True, blank=True)
    repeat_every = models.IntegerField(default=5)

    @property
    def is_last(self):
        next_o = AvitoResult.objects.filter(avito__user=self.avito.user, avito_id=self.avito.id, pk__gt=self.pk)
        return False if next_o.exists() else True


class WholePage(models.Model):
    unique_id = models.CharField(max_length=100, null=True)
    data = models.TextField()  # this stands for our crawled data
    date = models.DateTimeField(default=timezone.now)

    # This is for basic and custom serialisation to return it to client as a JSON.
    @property
    def to_dict(self):
        data = {
            'data': json.loads(self.data),
            'date': self.date
        }
        return data

    def __str__(self):
        return self.unique_id


class Task(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=False)
    name = models.CharField(max_length=100, null=True, blank=True)
    task_id = models.CharField(max_length=100, null=False)
    unique_id = models.CharField(max_length=100, null=False)
    date = models.DateTimeField(default=timezone.now)

    class Meta:
        permissions = (("can_run", "Can run task"),)

    # Scrapyd task status.
    @property
    def get_task_status(self):
        try:
            item = WholePage.objects.get(unique_id=self.unique_id)
            if len(item.to_dict['data']) != 0:
                return 'has stuff'
            return 'empty finished'
        except Exception as e:
            return helpers.get_task_status(self.task_id)

    # Is has stuff
    @property
    def is_has_stuff(self):
        return self.get_task_status == 'has stuff'

    @property
    def is_overdue(self):
        return True


class Egrul(models.Model):
    unique_id = models.CharField(max_length=100, null=True)
    inn = models.CharField(max_length=30, null=True)
    name = models.CharField(max_length=255, null=True)
    ogrn = models.CharField(max_length=30, null=True)
    # adrestext = models.CharField(max_length=1024, null=True)
    # kpp = models.CharField(max_length=30, null=True)
    # dtreg = models.CharField(max_length=100, null=True)
    resp_body = models.TextField()  # this stands for our crawled data
    date = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return self.unique_id
