# Metadata tag support for redactedbetter.
#
# Copyright (c) 2013 Milky Joe <milkiejoe@gmail.com>
#
# Permission is hereby granted, free of charge, to any person
# obtaining a copy of this software and associated documentation files
# (the "Software"), to deal in the Software without restriction,
# including without limitation the rights to use, copy, modify, merge,
# publish, distribute, sublicense, and/or sell copies of the Software,
# and to permit persons to whom the Software is furnished to do so,
# subject to the following conditions:
#
# The above copyright notice and this permission notice shall be
# included in all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
# EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
# MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
# NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS
# BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN
# ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN
# CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

"""Simple tagging for redactedbetter.
"""

import os.path
import re
import mutagen
import mutagen.flac
import mutagen.mp3
from mutagen.easyid3 import EasyID3

numeric_tags = set([
        'tracknumber',
        'discnumber',
        'tracktotal',
        'totaltracks',
        'disctotal',
        'totaldiscs',
        ])

class TaggingException(Exception):
    pass

def valid_fractional_tag(value):
    # m or m/n
    if re.match(r"""\d+(/(\d+))?$""", value):
        return True
    else:
        return False

def scrub_tag(name, value):
    """Strip whitespace (and other common problems) from tag values.

    May return the empty string ''.
    """
    scrubbed_value = value.strip().strip('\x00')

    # Strip trailing '/' or '/0' from numeric tags.
    if name in numeric_tags:
        scrubbed_value = re.sub(r"""/(0+)?$""", '', scrubbed_value)

    # Remove leading '/' from numeric tags.
    if name in numeric_tags:
        scrubbed_value = scrubbed_value.lstrip('/')

    # Numeric tags should not be '0' (but tracknumber 0 is OK, e.g.,
    # hidden track).
    if name in numeric_tags - set(['tracknumber']):
        if re.match(r"""0+(/.*)?$""", scrubbed_value):
            return ''

    return scrubbed_value

def check_tags(filename, check_tracknumber_format=True):
    """Verify that the file has the required redacted.ch tags.

    Returns (True, None) if OK, (False, msg) if a tag is missing or
    invalid.

    """
    info = mutagen.File(filename, easy=True)
    for tag in ['artist', 'album', 'title', 'tracknumber']:
        if tag not in info.keys():
            return (False, '"%s" has no %s tag' % (filename, tag))
        elif info[tag] == [u'']:
            return (False, '"%s" has an empty %s tag' % (filename, tag))

    if check_tracknumber_format:
        tracknumber = info['tracknumber'][0]
        if not valid_fractional_tag(tracknumber):
            return (False, '"%s" has a malformed tracknumber tag ("%s")' % (filename, tracknumber))

    return (True, None)

def copy_tags(flac_file, transcode_file):
    flac_info = mutagen.flac.FLAC(flac_file)
    transcode_info = None
    valid_key_fn = None
    transcode_ext = os.path.splitext(transcode_file)[1].lower()

    if transcode_ext == '.flac':
        transcode_info = mutagen.flac.FLAC(transcode_file)
        valid_key_fn = lambda k: True

    elif transcode_ext == '.mp3':
        transcode_info = mutagen.mp3.EasyMP3(transcode_file)
        valid_key_fn = lambda k: k in EasyID3.valid_keys.keys()

    else:
        raise TaggingException('Unsupported tag format "%s"' % transcode_file)

    for tag in filter(valid_key_fn, flac_info):
        # scrub the FLAC tags, just to be on the safe side.
        values = map(lambda v: scrub_tag(tag,v), flac_info[tag])
        if values and values != [u'']:
            transcode_info[tag] = values

    if transcode_ext == '.mp3':
        # Support for TRCK and TPOS x/y notation, which is not
        # supported by EasyID3.
        #
        # These tags don't make sense as lists, so we just use the head
        # element when fixing them up.
        #
        # totaltracks and totaldiscs may also appear in the FLAC file
        # as 'tracktotal' and 'disctotal'. We support either tag, but
        # in files with both we choose only one.

        if 'tracknumber' in transcode_info.keys():
            totaltracks = None
            if 'totaltracks' in flac_info.keys():
                totaltracks = scrub_tag('totaltracks', flac_info['totaltracks'][0])
            elif 'tracktotal' in flac_info.keys():
                totaltracks = scrub_tag('tracktotal', flac_info['tracktotal'][0])

            if totaltracks:
                transcode_info['tracknumber'] = [u'%s/%s' % (transcode_info['tracknumber'][0], totaltracks)]

        if 'discnumber' in transcode_info.keys():
            totaldiscs = None
            if 'totaldiscs' in flac_info.keys():
                totaldiscs = scrub_tag('totaldiscs', flac_info['totaldiscs'][0])
            elif 'disctotal' in flac_info.keys():
                totaldiscs = scrub_tag('disctotal', flac_info['disctotal'][0])

            if totaldiscs:
                transcode_info['discnumber'] = [u'%s/%s' % (transcode_info['discnumber'][0], totaldiscs)]

    transcode_info.save()

# EasyID3 extensions for redactedbetter.

for key, frameid in {
    'albumartist': 'TPE2',
    'album artist': 'TPE2',
    'grouping': 'TIT1',
    'content group': 'TIT1',
    }.iteritems():
    EasyID3.RegisterTextKey(key, frameid)

def comment_get(id3, _):
    return [comment.text for comment in id3['COMM'].text]

def comment_set(id3, _, value):
    id3.add(mutagen.id3.COMM(encoding=3, lang='eng', desc='', text=value))

def originaldate_get(id3, _):
    return [stamp.text for stamp in id3['TDOR'].text]

def originaldate_set(id3, _, value):
    id3.add(mutagen.id3.TDOR(encoding=3, text=value))

EasyID3.RegisterKey('comment', comment_get, comment_set)
EasyID3.RegisterKey('description', comment_get, comment_set)
EasyID3.RegisterKey('originaldate', originaldate_get, originaldate_set)
EasyID3.RegisterKey('original release date', originaldate_get, originaldate_set)
