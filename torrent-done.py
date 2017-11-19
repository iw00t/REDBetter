#!/usr/bin/env python2.7

from sys import argv, exit
import json


def main():
    torrent_hash = argv[5].upper()

    # find the hash and set done = true
    cache = json.load(open('~/.redactedbetter/cache-crawl'))
    for torrent in cache:
        if torrent['hash'] == torrent_hash:
            torrent['done'] = True
            json.dump(cache, open('~/.redactedbetter/cache-crawl', 'wb'))
            exit(0)

    exit(1)
