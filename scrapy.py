#!/usr/bin/env python
# coding: utf8

from __future__ import unicode_literals
from lxml import html
import requests, time

def scrap_upcoming():
	encore = True
	counter = 0
	IDs = []

	while encore:
		counter += 1
		page = requests.get("http://store.steampowered.com/search/?filter=comingsoon%23sort_by=ASC&filter=comingsoon&page={}".format(counter))
		tree = html.fromstring(page.text)
		steamIDs = tree.xpath("//@data-ds-appid")
		if steamIDs == []:
			encore = False
		else:
			IDs += steamIDs
			time.sleep(2)

	return IDs