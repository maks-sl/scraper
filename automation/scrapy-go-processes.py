from selenium import webdriver
import random
import argparse
from time import sleep

parser=argparse.ArgumentParser()
parser.add_argument('-n', '--num_proc', help='Number of processes', default=False)
args=parser.parse_args()
n = args.num_proc

if (n):
	driver = webdriver.Chrome()
	for x in range(int(n)):
		# sleep(2)
		inn = random.randint(1000000000000,9999999999999)
		# NEW TASK INIT
		driver.get('http://127.0.0.1:8000/scrapy-go/')
		search_box = driver.find_element_by_id('id_inn')
		search_box.send_keys(inn)
		search_box.submit()
	driver.close()
	print('Completed')
else:
	print('Using -n argument required! (-h to help)')
