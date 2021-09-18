#!/usr/bin/env python

import os
from twilio.rest import Client
from twilio.base.exceptions import TwilioRestException
import sys
import time
import requests
import logging
from bs4 import BeautifulSoup


env = os.environ.get("ENV", "local")
if env == "production":
    level = logging.INFO
else:
    level = logging.DEBUG


logging.basicConfig(
    format="%(asctime)s %(levelname)s %(message)s", stream=sys.stdout, level=level
)

to_monitor = [
    "https://www.pap.fr/annonce/locations-appartement-paris-2e-g37769-du-2-pieces-au-4-pieces-a-partir-de-1-chambres-jusqu-a-1500-euros-a-partir-de-40-m2"
]


USER_AGENT = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/93.0.4577.82 Safari/537.36"

headers = {"user-agent": USER_AGENT}

base = "https://www.pap.fr"

NUM_OF_PAGES = 5

TIME_TO_SLEEP = 60


def watch():
    first = True
    logging.info("Starting watch process...")
    while True:
        for url in to_monitor:
            handle(url, first)
        first = False
        time.sleep(TIME_TO_SLEEP)


old_ads = set()


def handle(url, first):
    logging.debug(f"Handling {url}")
    count = 0
    ads = {}
    collect(url, ads)
    for page in range(2, NUM_OF_PAGES):
        collect(url + "-" + str(page), ads)
    for key, value in ads.items():
        if key not in old_ads and (not first or env != "production"):
            count += 1
            notify(value)
        old_ads.add(key)
    collected_ads = len(ads)
    logging.info(f"Collected {collected_ads} ads and notified {count} ads")


def collect(url, ads):
    logging.debug(f"Collecting {url}")
    r = requests.get(url, headers=headers)
    r.raise_for_status()
    html_doc = r.text
    soup = BeautifulSoup(html_doc, "html.parser")
    for link in soup.find_all("a", class_="item-thumb-link"):
        key = link["href"]
        if key in old_ads:
            ads[key] = {}
            continue
        ad = collect_ad(f"{base}{key}")
        ads[key] = ad


def collect_ad(url):
    logging.debug(f"Collecting ad {url}")
    r = requests.get(url, headers=headers)
    r.raise_for_status()
    html_doc = r.text
    soup = BeautifulSoup(html_doc, "html.parser")
    ad = {}
    ad["price"] = soup.find("span", class_="item-price").text
    ad["district"] = soup.find("h2", class_="margin-bottom-8").text
    ad["title"] = soup.title.text.rstrip(" | De Particulier à Particulier - PAP")
    ad["url"] = url
    logging.debug(ad)
    return ad


def notify(ad):
    logging.info(f"Notifying ad {ad['title']}")

    # Find your Account SID and Auth Token at twilio.com/console
    # and set the environment variables. See http://twil.io/secure
    account_sid = os.environ["TWILIO_ACCOUNT_SID"]
    auth_token = os.environ["TWILIO_AUTH_TOKEN"]
    client = Client(account_sid, auth_token)

    body = f"""
Nouvelle annonce pap: {ad['price']} / {ad['district']}

{ad['title']}

{ad['url']}
"""
    logging.debug(body)
    try:
        message = client.messages.create(
            body=body, from_="+33644601738", to="+33626485845"
        )
    except TwilioRestException:
        logging.error("Error while sending sms")


if __name__ == "__main__":

    watch()
