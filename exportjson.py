# -*- coding: utf-8 -*-
from config import algolia_id, algolia_secret
import os
import sys
import json

from algoliasearch import algoliasearch
from selenium import webdriver
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup

# Init algolia
algolia = algoliasearch.Client(algolia_id, algolia_secret)
algolia_index = algolia.init_index("groups")
res = algolia_index.search("", {"filters": "enabled = 1", "hitsPerPage": 99999})


def telegram(url):
    dcap = dict(DesiredCapabilities.PHANTOMJS)
    dcap["phantomjs.page.settings.userAgent"] = (
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36"
        " (KHTML, like Gecko) Chrome/61.0.3163.100 Safari/537.36"
    )
    driver = webdriver.Remote(
        command_executor="http://seleniumaddr:seleniumport", desired_capabilities=dcap
    )
    driver.get(url)
    try:
        WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.CLASS_NAME, "tgme_page_extra"))
        )
        req = driver.page_source
        soup = BeautifulSoup(req, "lxml")
        members = soup.find("div", {"class": "tgme_page_extra"})
        members = members.text.replace(" members", "").replace(" ", "")
    except:
        members = 0
    return members


fout = open("error.log", "w")
groups = {}
for group in res["hits"]:
    if telegram(group["url"]) != 0:
        if group["category"] in groups:
            groups[group["category"]].append(group)
        else:
            groups[group["category"]] = [group]
    else:
        fout.write("[ERROR] %s" % group["name"])
fout.close()
htmlout = ""
htmlhead = (
    '<table class="table table-striped table-hover text-center">'
    "<thead><tr><th>Nome Gruppo</th>"
    "<th>Descrizione</th><th>Link</th></tr>"
    "</thead><tbody>"
)

for category in sorted(groups):
    htmlout += "<h2>%s</h2>%s" % (category, htmlhead)
    for group in groups[category]:
        htmlout += (
            "<tr><td>%s</td><td>%s</td><td>" '<a href="%s">Click</a></td></tr>'
        ) % (group["name"], group["desc"], group["url"])
    htmlout += "</tbody></table>"

print(htmlout.encode("utf-8"))
