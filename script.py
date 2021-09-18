#!/usr/bin/env python

import os
from twilio.rest import Client
import sys
import time
import requests
import logging
from bs4 import BeautifulSoup

logging.basicConfig(
    format="%(asctime)s %(levelname)s %(message)s",
    stream=sys.stdout,
    level=logging.DEBUG,
)

to_monitor = [
    "https://www.pap.fr/annonce/locations-appartement-paris-2e-g37769-du-2-pieces-au-4-pieces-a-partir-de-1-chambres-jusqu-a-1500-euros-a-partir-de-40-m2"
]


COOKIE = """lang=fr; atuserid={"name":"atuserid","val":"8a6f5762-2443-4d05-8117-32825c84606e","options":{"end":"2022-09-22T14:06:01.373Z","path":"/"}}; euconsent-v2=CPMLQIVPMLQJCBcAIBFRBqCgAP_AAEPAAAqIIDwKAABQAKAAsACoAGQAQAAqABbADQANQAigBNAC3AGEAYgA5AB-gEGAQgAmABOgCkAFwAPQAhABFgCOgF1AM6AaIA14BtAEdgI9AS8An8BeYDFwGMgMkgcmBygD0gHqgQHBAeAAAgEgGAALAAqABkAEEANAA1ACKAH4AQgBtAF5gMkgcmBygQAEAaIBHoaACA5QRABAcoKgBALzAcoKAAgI9GQAgF5gOUGAAQEejoCQACwAKgAZABBADQANQAigBiAD8AIQATABFgC6gG0AXmAySByYHKAPSAeqOABgEIANeAj0hAEAAWABkAMQBtCAAEBHpKAMAAsADIAYgBCAF1AXmSABAGvAR6UgHAALAAqABkAEEANAA1ACKAGIAPwAhACLAG0AXmAySByYHKFAAYBdQDXgI9A.4U6gDgBZAKMAksCJIKDAUIgp1AAoAIABAACgAKACAAQAAoA; _ga=GA1.2.176224256.1631040362; email=gobadiah@gmail.com; crypt=12.OnOdML29J6; contact_annonceur[prenom]=Michaël; contact_annonceur[nom]=Journo; contact_annonceur[email]=gobadiah@gmail.com; contact_annonceur[telephone]=0626485845; contact_annonceur[message]=Bonjour,\r\rJe suis à la recherche d'un appartement meublé dans le centre de Paris, et votre annonce a attiré mon attention. \r\rJe suis actuellement célibataire, en CDI avec une rémunération mensuelle d'environ 6650€ net avant impôts. Je suis prêt à garantir les loyers au travers du service unkle, que je découvre (www.unkle.fr). \r\rJe peux emménager rapidement si mon dossier vous convient et que j'ai l'opportunité de visiter l'appartement en amont. \r\rBien cordialement,\r\rMichaël; consent_youtube=1; _gid=GA1.2.1325107343.1631956759; derniere_recherche={"produit":"location","typesbien":["appartement"],"nb_pieces":{"min":2,"max":4},"nb_chambres":{"min":1,"max":null},"prix":{"min":null,"max":1500},"surface":{"min":40,"max":null},"surface_terrain":{"min":null,"max":null},"geo_objets":[37769]}; a_ete_contacte={"410701475":[1631367570],"439100147":[1631371434],"196511124":[1631371638],"439100065":[1631371917],"425601321":[1631956893]}; atauthority={"name":"atauthority","val":{"authority_name":"cnil","visitor_mode":"exempt"},"options":{"end":"2022-10-20T14:13:57.600Z","path":"/"}}"""

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
    ads = {}
    collect(url, ads)
    for page in range(2, NUM_OF_PAGES):
        collect(url + "-" + str(page), ads)
    for key, value in ads:
        if key not in old_ads and first:
            notify(value)
        old_ads.add(key)


def collect(url, ads):
    logging.debug(f"Collecting {url}")
    html_doc = requests.get(url, headers=headers).text
    soup = BeautifulSoup(html_doc, "html.parser")
    for link in soup.find_all("a", class_="item-thumb-link"):
        key = link["href"]
        if key in old_ads:
            continue
        ad = collect_ad(f"{base}{key}")
        ads[key] = ad


def collect_ad(url):
    logging.debug(f"Collecting ad {url}")
    html_doc = requests.get(url, headers=headers).text
    soup = BeautifulSoup(html_doc, "html.parser")
    ad = {}
    ad["price"] = soup.find("span", class_="item-price").text
    ad["district"] = soup.find("h2", class_="margin-bottom-8").text
    ad["title"] = soup.title.text.rstrip(" | De Particulier à Particulier - PAP")
    ad["url"] = url
    return ad


def notify(ad):
    logging.info("Notifying ad {ad}")


if __name__ == "__main__":

    # Find your Account SID and Auth Token at twilio.com/console
    # and set the environment variables. See http://twil.io/secure
    account_sid = os.environ["TWILIO_ACCOUNT_SID"]
    auth_token = os.environ["TWILIO_AUTH_TOKEN"]
    print(account_sid, auth_token)
    client = Client(account_sid, auth_token)

    message = client.messages.create(
        body="Join Earth's mightiest heroes. Like Kevin Bacon.",
        from_="+33644601738",
        to="+33626485845",
    )

    print(message.sid)

    # watch()
