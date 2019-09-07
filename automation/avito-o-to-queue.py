import requests
import json
cookies = {'sessionid': 'mmf1tfwzaw1nn0pxr80dtcd8o6n75wkg'}

with open('o.json', 'r') as in_file:
    data = json.load(in_file)

for item in data:
    req = requests.post("http://127.0.0.1:8000/avito-run/", cookies=cookies,
                        data={'url': 'https://www.avito.ru'+item['name']})
    print([req.status_code, req.url])

