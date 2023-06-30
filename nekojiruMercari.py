#!/usr/bin/python3.5
import json
import os
import sqlite3
import time
from datetime import datetime, timezone
from enum import Enum
from hashlib import md5

import mercari
import requests as r


def load_json_file():
    with open(json_file) as data_file:
        data = json.load(data_file)
        return data


def get_new_item_embed(item):
    m = md5()
    m.update(bytes(item.id, 'utf8'))
    # and then just pull the last 3 bytes and convert to int
    color = int.from_bytes(m.digest()[-3:], "little")
    embed = {
        'title':
        '【{}】'.format(item.id),
        'description':
        '{}\n'.format(item.productName),
        'url':
        '{}'.format(item.productURL),
        'fields': [
            {
                'name': 'Price:',
                'value': "{:,}円".format(int(item.price)),
                'inline': False
            },
        ],
        'color':
        color,
        'image': {
            'url': item.imageURL,
        },
    }
    return embed


def check_item(item):

    c.execute("SELECT productCode FROM mercari WHERE productCode=?",
              (item.id, ))
    if c.fetchone():
        return  # don't care if item has been seen before

    c.execute("INSERT INTO mercari (productCode, price) VALUES (?, ?)", (
        item.id,
        item.price,
    ))
    conn.commit()

    resp = get_new_item_embed(item)
    send_embeds(resp)


def send_embeds(embed):
    global discord_url
    if type(discord_url) is list:
        for url in discord_url:
            send_embed(embed, url)
    else:
        send_embed(embed, discord_url)


def send_embed(embed, url):

    payload = {'embeds': [embed], 'username': 'Mercari'}
    payload_json = json.dumps(payload)
    response = r.post(url,
                      payload_json,
                      headers={'Content-Type': 'application/json'})

    if response.status_code != 200 and response.status_code != 204:
        print("Error: ", response.text)
        jsonError = json.loads(response.text)
        sleepTime = jsonError['retry_after'] / 1000
        print("Sleeping for {}s".format(sleepTime))
        time.sleep(sleepTime)  # goodnight my prince
        send_embed(embed, url)  # attempt sending again


def main():
    print(datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
    query = 'ねこぢる'

    for item in mercari.search(query):
        check_item(item)


db_file = os.path.join(os.path.dirname(__file__), "nekojiru.db")
conn = sqlite3.connect(db_file)
c = conn.cursor()

schema = """
CREATE TABLE IF NOT EXISTS "mercari" (
    "productCode" TEXT NOT NULL,
    "price" INTEGER,
    "time" TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY ("productCode", "price")
);
"""
c.execute(schema)
conn.commit()

json_file = fn = os.path.join(os.path.dirname(__file__), "mercari.json")
data = load_json_file()  # we make this global cause life easier
discord_url = data['discord_webhook_url']
main()
conn.close()