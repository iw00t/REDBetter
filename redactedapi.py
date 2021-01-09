#!/usr/bin/env python
import re
import os
import json
import time
import requests
import mechanize
import HTMLParser
from cStringIO import StringIO

headers = {
    'Connection': 'keep-alive',
    'Cache-Control': 'max-age=0',
    'User-Agent': 'REDBetter crawler',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Encoding': 'gzip,deflate,sdch',
    'Accept-Language': 'en-US,en;q=0.8',
    'Accept-Charset': 'ISO-8859-1,utf-8;q=0.7,*;q=0.3'}

# gazelle is picky about case in searches with &media=x
media_search_map = {
    'cd': 'CD',
    'dvd': 'DVD',
    'vinyl': 'Vinyl',
    'soundboard': 'Soundboard',
    'sacd': 'SACD',
    'dat': 'DAT',
    'web': 'WEB',
    'blu-ray': 'Blu-ray'
    }

lossless_media = set(media_search_map.keys())

formats = {
    'FLAC': {
        'format': 'FLAC',
        'encoding': 'Lossless'
    },
    'V0': {
        'format' : 'MP3',
        'encoding' : 'V0 (VBR)'
    },
    '320': {
        'format' : 'MP3',
        'encoding' : '320'
    },
    'V2': {
        'format' : 'MP3',
        'encoding' : 'V2 (VBR)'
    },
}

def allowed_transcodes(torrent):
    """Some torrent types have transcoding restrictions."""
    preemphasis = re.search(r"""pre[- ]?emphasi(s(ed)?|zed)""", torrent['remasterTitle'], flags=re.IGNORECASE)
    if preemphasis:
        return []
    else:
        return formats.keys()

class LoginException(Exception):
    pass

class RequestException(Exception):
    pass

class RedactedAPI:
    def __init__(self, username=None, password=None, session_cookie=None):
        self.session = requests.Session()
        self.session.headers.update(headers)
        self.username = username
        self.password = password
        self.session_cookie = session_cookie
        self.authkey = None
        self.passkey = None
        self.userid = None
        self.tracker = "https://flacsfor.me/"
        self.last_request = time.time()
        self.rate_limit = 2.0 # seconds between requests
        self._login()

    def _login(self):
        if self.session_cookie is not None:
            try:
                self._login_cookie()
            except:
                print "WARNING: session cookie attempted and failed"
                self._login_username_password()
        else:
            self._login_username_password()

    def _login_cookie(self):
        mainpage = 'https://redacted.ch/';
        cookiedict = {"session": self.session_cookie}
        cookies = requests.utils.cookiejar_from_dict(cookiedict)

        self.session.cookies.update(cookies)
        r = self.session.get(mainpage)
        try:
            accountinfo = self.request('index')
            self.authkey = accountinfo['authkey']
            self.passkey = accountinfo['passkey']
            self.userid = accountinfo['id']
        except:
            raise LoginException

    def _login_username_password(self):
        '''Logs in user and gets authkey from server'''

        if not self.username or self.username == "":
            print "WARNING: username authentication attempted, but username not set, skipping."
            raise LoginException
        loginpage = 'https://redacted.ch/login.php'
        data = {'username': self.username,
                'password': self.password}
        r = self.session.post(loginpage, data=data)
        if r.status_code != 200:
            raise LoginException
        accountinfo = self.request('index')
        self.authkey = accountinfo['authkey']
        self.passkey = accountinfo['passkey']
        self.userid = accountinfo['id']
        try:
            accountinfo = self.request('index')
            self.authkey = accountinfo['authkey']
            self.passkey = accountinfo['passkey']
            self.userid = accountinfo['id']
        except:
            raise LoginException

    def logout(self):
        self.session.get("https://redacted.ch/logout.php?auth=%s" % self.authkey)

    def request(self, action, **kwargs):
        '''Makes an AJAX request at a given action page'''
        while time.time() - self.last_request < self.rate_limit:
            time.sleep(0.1)

        ajaxpage = 'https://redacted.ch/ajax.php'
        params = {'action': action}
        if self.authkey:
            params['auth'] = self.authkey
        params.update(kwargs)
        r = self.session.get(ajaxpage, params=params, allow_redirects=False)
        self.last_request = time.time()
        try:
            parsed = json.loads(r.content)
            if parsed['status'] != 'success':
                #raise RequestException
                return None
            return parsed['response']
        except ValueError:
            raise RequestException

    def request_html(self, action, **kwargs):
        while time.time() - self.last_request < self.rate_limit:
            time.sleep(0.1)

        ajaxpage = 'https://redacted.ch/' + action
        if self.authkey:
            kwargs['auth'] = self.authkey
        r = self.session.get(ajaxpage, params=kwargs, allow_redirects=False)
        self.last_request = time.time()
        return r.content

    def get_artist(self, id=None, format='MP3', best_seeded=True):
        res = self.request('artist', id=id)
        torrentgroups = res['torrentgroup']
        keep_releases = []
        for release in torrentgroups:
            torrents = release['torrent']
            best_torrent = torrents[0]
            keeptorrents = []
            for t in torrents:
                if t['format'] == format:
                    if best_seeded:
                        if t['seeders'] > best_torrent['seeders']:
                            keeptorrents = [t]
                            best_torrent = t
                    else:
                        keeptorrents.append(t)
            release['torrent'] = list(keeptorrents)
            if len(release['torrent']):
                keep_releases.append(release)
        res['torrentgroup'] = keep_releases
        return res

    def snatched(self, skip=None, media=lossless_media):
        if not media.issubset(lossless_media):
            raise ValueError('Unsupported media type %s' % (media - lossless_media).pop())

        # gazelle doesn't currently support multiple values per query
        # parameter, so we have to search a media type at a time;
        # unless it's all types, in which case we simply don't specify
        # a 'media' parameter (defaults to all types).

        if media == lossless_media:
            media_params = ['']
        else:
            media_params = ['&media=%s' % media_search_map[m] for m in media]

        url = 'https://redacted.ch/torrents.php?type=snatched&userid=%s&format=FLAC' % self.userid
        for mp in media_params:
            page = 1
            done = False
            pattern = re.compile('torrents.php\?id=(\d+)&amp;torrentid=(\d+)')
            while not done:
                content = self.session.get(url + mp + "&page=%s" % page).text
                for groupid, torrentid in pattern.findall(content):
                    if skip is None or torrentid not in skip:
                        yield int(groupid), int(torrentid)
                done = 'Next &gt;' not in content
                page += 1

    def upload(self, group, torrent, new_torrent, format, description=[]):
        url = "https://redacted.ch/upload.php?groupid=%s" % group['group']['id']
        response = self.session.get(url)
        forms = mechanize.ParseFile(StringIO(response.text.encode('utf-8')), url)
        form = forms[-1]
        form.find_control('file_input').add_file(open(new_torrent), 'application/x-bittorrent', os.path.basename(new_torrent))
        #if torrent['remastered']:
        #    form.find_control('remaster').set_single('1')
        if torrent['remasterYear'] != 0:
            form['remaster_year'] = str(torrent['remasterYear'])
        else:
            form['remaster_year'] = str(group['group']['year'])
        form['remaster_title'] = torrent['remasterTitle']
        form['remaster_record_label'] = torrent['remasterRecordLabel']
        form['remaster_catalogue_number'] = torrent['remasterCatalogueNumber']
        form.find_control('format').set('1', formats[format]['format'])
        form.find_control('bitrate').set('1', formats[format]['encoding'])
        form.find_control('media').set('1', torrent['media'])

        release_desc = '\n'.join(description)
        if release_desc:
            form['release_desc'] = release_desc

        _, data, headers = form.click_request_data()
        return self.session.post(url, data=data, headers=dict(headers))

    def set_24bit(self, torrent):
        url = "https://redacted.ch/torrents.php?action=edit&id=%s" % torrent['id']
        response = self.session.get(url)
        forms = mechanize.ParseFile(StringIO(response.text.encode('utf-8')), url)
        form = forms[-3]
        form.find_control('bitrate').set('1', '24bit Lossless')
        _, data, headers = form.click_request_data()
        return self.session.post(url, data=data, headers=dict(headers))

    def release_url(self, group, torrent):
        return "https://redacted.ch/torrents.php?id=%s&torrentid=%s#torrent%s" % (group['group']['id'], torrent['id'], torrent['id'])

    def permalink(self, torrent):
        return "https://redacted.ch/torrents.php?torrentid=%s" % torrent['id']

    def get_better(self, search_type=3, tags=None):
        if tags is None:
            tags = []
        data = self.request('better', method='transcode', type=search_type, search=' '.join(tags))
        out = []
        for row in data:
            out.append({
                'permalink': 'torrents.php?id={}'.format(row['torrentId']),
                'id': row['torrentId'],
                'torrent': row['downloadUrl'],
            })
        return out

    def get_torrent(self, torrent_id):
        '''Downloads the torrent at torrent_id using the authkey and passkey'''
        while time.time() - self.last_request < self.rate_limit:
            time.sleep(0.1)

        torrentpage = 'https://redacted.ch/torrents.php'
        params = {'action': 'download', 'id': torrent_id}
        if self.authkey:
            params['authkey'] = self.authkey
            params['torrent_pass'] = self.passkey
        r = self.session.get(torrentpage, params=params, allow_redirects=False)

        self.last_request = time.time() + 2.0
        if r.status_code == 200 and 'application/x-bittorrent' in r.headers['content-type']:
            return r.content
        return None

    def get_torrent_info(self, id):
        return self.request('torrent', id=id)['torrent']

def unescape(text):
    return HTMLParser.HTMLParser().unescape(text)
