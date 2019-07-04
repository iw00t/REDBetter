#!/usr/bin/env python2.7
# make me a conjob!

import os
import json
import argparse
import ConfigParser
import sys

lockfile = os.path.expanduser('~/.redactedbetter/parse.lock')


def main():
    if os.path.exists(lockfile):
        print "Found lockfile, exiting...."

    parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter, prog='redactedbetter')
    parser.add_argument('--cache', help='the location of the cache',
                        default=os.path.expanduser('~/.redactedbetter/cache-crawl'))

    args = parser.parse_args()
    while parse_stuff(args.cache) and not os.path.exists(lockfile):
        print "Done encoding cycle"


def parse_stuff(cache_file):
    open(lockfile, 'w').close()
    try:
        cache = json.load(open(cache_file))
    except:
        cache = []
        json.dump(cache, open(cache_file, 'wb'))

    permalinks = []
    cache_new = []
    for torrent in cache:
        if torrent['done']:
            permalinks.append('"https://redacted.ch/%s"' % torrent['permalink'])
        else:
            cache_new.append(torrent)

    if len(permalinks) == 0:
        return False

    cmdline = "python2 redactedbetter %s" % ' '.join(permalinks)
    json.dump(cache_new, open(cache_file, 'wb'))
    print "Executing... " + cmdline
    os.system(cmdline)
    os.remove(lockfile)
    return True


if __name__ == '__main__':
    main()
