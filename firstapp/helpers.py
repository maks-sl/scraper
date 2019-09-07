
from scrapyd_api import ScrapydAPI

scrapyd = ScrapydAPI('http://localhost:6800')


def get_task_status(task_id):
    return scrapyd.job_status('default', task_id)


def new_task_id(name, settings, url, domain):
    return scrapyd.schedule('default', name, settings=settings, url=url, domain=domain)
