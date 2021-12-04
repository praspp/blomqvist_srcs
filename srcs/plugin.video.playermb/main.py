# -*- coding: UTF-8 -*-

import sys, re, os
import time
from collections import namedtuple


if sys.version_info >= (3, 0):
    # for Python 3

    from urllib.parse import parse_qs, parse_qsl, urlencode, quote_plus, unquote_plus
    import http.cookiejar as cookielib

    # pickle is faster for Python3
    import pickle

    def save_ints(path, seq):
        with open(path, 'wb') as f:
            pickle.dump(seq, f, pickle.HIGHEST_PROTOCOL)

    def load_ints(path):
        with open(path, 'rb') as f:
            return pickle.load(f)

    basestring = str
    unicode = str
    xrange = range

else:
    # for Python 2

    from urllib import urlencode, quote_plus, unquote_plus

    import cookielib
    from urlparse import parse_qsl, parse_qs

    try:
        import urllib3
    except ImportError:
        pass
    else:
        urllib3.disable_warnings()

    # struct is faster for Python2
    import struct

    def save_ints(path, seq):
        if seq:
            with open(path, 'wb') as f:
                f.write(struct.pack('=%sQ' % len(seq), *seq))

    def load_ints(path):
        with open(path, 'rb') as f:
            data = f.read()
            return struct.unpack('=%sQ' % (len(data) // 8), data)


from threading import Thread
import requests
from requests.exceptions import SSLError
import urllib3  # already used by "requests"
from urllib3.exceptions import MaxRetryError, SSLError as SSLError3
from certifi import where
import xbmcgui
import xbmcplugin
import xbmcaddon
import xbmc, xbmcvfs
import json
import inputstreamhelper

from resources.lib.udata import AddonUserData
# from resources.lib.tools import U, uclean, NN, fragdict


MetaDane = namedtuple('MetaDane', 'tytul opis foto sezon epizod fanart thumb landscape poster allowed')
MetaDane.__new__.__defaults__ = 5*(None,)
MetaDane.art = property(lambda self: {k: v for k in 'fanart thumb landscape poster'.split()
                                      for v in (getattr(self, k),) if v})

UA = 'okhttp/3.3.1 Android'
# UA = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:87.0) Gecko/20100101 Firefox/87.0'
PF = 'ANDROID_TV'
# PF = 'BROWSER

base_url = sys.argv[0]
addon_handle = int(sys.argv[1])
params = dict(parse_qsl(sys.argv[2][1:]))
addon = xbmcaddon.Addon(id='plugin.video.playermb')

PATH = addon.getAddonInfo('path')
try:
    DATAPATH = xbmcvfs.translatePath(addon.getAddonInfo('profile'))
except:
    DATAPATH = xbmc.translatePath(addon.getAddonInfo('profile')).decode('utf-8')
CACHEPATH = os.path.join(DATAPATH, 'cache')

RESOURCES = os.path.join(PATH, 'resources')
COOKIEFILE = os.path.join(DATAPATH, 'player.cookie')
SUBTITLEFILE = os.path.join(DATAPATH, 'temp.sub')
MEDIA = os.path.join(RESOURCES, 'media')

ADDON_ICON = os.path.join(RESOURCES, '../icon.png')
FANART = os.path.join(RESOURCES, '../fanart.jpg')
sys.path.append(os.path.join(RESOURCES, 'lib'))

HISTORY_SIZE = 50

addon_data = AddonUserData(os.path.join(DATAPATH, 'data.json'))
exlink = params.get('url')
# name = params.get('name')
# page = params.get('page', '')
# rys = params.get('image')
kukz = ''

slug_blacklist = {
    'pobierz-i-ogladaj-offline',
}

kanalydata = [
    {"id": 97, "name": "dla dzieci"},
    {"id": 142, "name": "sport"},
    {"id": 143, "name": "programy"},
    {"id": 144, "name": "filmy"},
    {"id": 145, "name": "seriale"},
    {"id": 146, "name": "informacje"}
]

menudata = [
    {'url': 1, 'slug': 'seriale-online', 'title': 'Seriale'},
    {'url': 2, 'slug': 'programy-online', 'title': 'Programy'},
    {'url': 3, 'slug': 'filmy-online', 'title': 'Filmy'},
    {'url': 4, 'slug': 'bajki-dla-dzieci', 'title': 'Dla dzieci'},
    {'url': 5, 'slug': 'strefa-sport', 'title': 'Sport'},
    {'url': 24, 'slug': 'eurosport', 'title': 'Eurosport'},
    {'url': 7, 'slug': 'canal-plus', 'title': 'CANAL+'},
    {'url': 8, 'slug': 'hbo', 'title': 'HBO'},
    {'url': 17, 'slug': 'live', 'title': 'Kanały TV'},
    {'url': 21, 'slug': 'motortrend', 'title': 'MotorTrend'},
    {'url': 22, 'slug': 'hotel-paradise', 'title': 'Hotel Paradise'},
    {'url': 23, 'slug': 'discovery-plus', 'title': 'Discovery+'}
]

serialemenu = {
    "1": [{"id":7,"name":"Bajki","externalId":11},{"id":8,"name":"Obyczajowy","externalId":12},{"id":9,"name":"Komedia","externalId":13},{"id":10,"name":"Sensacyjny","externalId":14},{"id":11,"name":"Dokumentalny","externalId":16},{"id":17,"name":"Thriller","externalId":31},{"id":18,"name":"Horror","externalId":32},{"id":19,"name":"Dramat","externalId":33},{"id":20,"name":"Science Fiction","externalId":34},{"id":22,"name":"Familijny","externalId":36},{"id":26,"name":"Inne","externalId":41},{"id":30,"name":"Akcja","externalId":50},{"id":31,"name":"Animowany","externalId":51},{"id":32,"name":"Biograficzny","externalId":52},{"id":34,"name":"Fantasy","externalId":54},{"id":35,"name":"Historyczny","externalId":55},{"id":36,"name":"Kostiumowy","externalId":56},{"id":37,"name":"Kryminalny","externalId":57},{"id":38,"name":"Melodramat","externalId":58},{"id":39,"name":"Musical","externalId":59},{"id":40,"name":"Przygodowy","externalId":60},{"id":41,"name":"Psychologiczny","externalId":61},{"id":42,"name":"Western","externalId":62},{"id":43,"name":"Wojenny","externalId":63},{"id":46,"name":"Komediodramat","externalId":66},{"id":47,"name":"Telenowela","externalId":67},{"id":52,"name":"Programy edukacyjne","externalId":72},{"id":53,"name":"Filmy animowane","externalId":73}],
    "2":[{"id":1,"name":"Rozrywka","externalId":5},{"id":2,"name":"Poradniki","externalId":6},{"id":3,"name":"Kuchnia","externalId":7},{"id":4,"name":"Zdrowie i Uroda","externalId":8},{"id":5,"name":"Talk-show","externalId":9},{"id":6,"name":"Motoryzacja","externalId":10},{"id":7,"name":"Bajki","externalId":11},{"id":8,"name":"Obyczajowy","externalId":12},{"id":11,"name":"Dokumentalny","externalId":16},{"id":12,"name":"Informacje","externalId":18},{"id":13,"name":"Podróże i Przyroda","externalId":19},{"id":14,"name":"Dokument i Reportaż","externalId":20},{"id":23,"name":"Motorsport","externalId":38},{"id":26,"name":"Inne","externalId":41},{"id":27,"name":"Muzyka","externalId":42},{"id":29,"name":"Dom i Ogród","externalId":48},{"id":31,"name":"Animowany","externalId":51},{"id":32,"name":"Biograficzny","externalId":52},{"id":48,"name":"Hobby","externalId":68},{"id":49,"name":"Kultura","externalId":69},{"id":50,"name":"Moda","externalId":70},{"id":51,"name":"Popularno-naukowe","externalId":71},{"id":52,"name":"Programy edukacyjne","externalId":72},{"id":53,"name":"Filmy animowane","externalId":73}],
    "5":[{"id":6,"name":"Motoryzacja","externalId":10},{"id":12,"name":"Informacje","externalId":18},{"id":23,"name":"Motorsport","externalId":38},{"id":24,"name":"Piłka nożna","externalId":39},{"id":25,"name":"Sporty ekstremalne","externalId":40},{"id":26,"name":"Inne","externalId":41},{"id":59,"name":"Sporty zimowe","externalId":79}],
    "22":[{"id":1,"name":"Rozrywka","externalId":5}],
    "21":[{"id":1,"name":"Rozrywka","externalId":5},{"id":2,"name":"Poradniki","externalId":6},{"id":6,"name":"Motoryzacja","externalId":10},{"id":13,"name":"Podróże i Przyroda","externalId":19},{"id":14,"name":"Dokument i Reportaż","externalId":20},{"id":23,"name":"Motorsport","externalId":38},{"id":48,"name":"Hobby","externalId":68},{"id":49,"name":"Kultura","externalId":69}],
    "7":[{"id":45,"name":"Dokument","externalId":65},{"id":60,"name":"Film","externalId":80},{"id":61,"name":"Serial","externalId":81},{"id":62,"name":"Sport","externalId":82},{"id":63,"name":"Dla dzieci","externalId":83}],
    "8":[{"id":45,"name":"Dokument","externalId":65},{"id":60,"name":"Film","externalId":80},{"id":61,"name":"Serial","externalId":81},{"id":63,"name":"Dla dzieci","externalId":83},{"id":64,"name":"Disney","externalId":84},{"id":65,"name":"Styl życia","externalId":85}],
    "17":[{"id":97,"name":"dla dzieci"},{"id":142,"name":"sport"},{"id":143,"name":"programy"},{"id":144,"name":"filmy"},{"id":145,"name":"seriale"},{"id":146,"name":"informacje"}],
    "3":[{"id":1,"name":"Rozrywka","externalId":5},{"id":3,"name":"Kuchnia","externalId":7},{"id":7,"name":"Bajki","externalId":11},{"id":8,"name":"Obyczajowy","externalId":12},{"id":9,"name":"Komedia","externalId":13},{"id":10,"name":"Sensacyjny","externalId":14},{"id":11,"name":"Dokumentalny","externalId":16},{"id":14,"name":"Dokument i Reportaż","externalId":20},{"id":16,"name":"Piosenki","externalId":30},{"id":17,"name":"Thriller","externalId":31},{"id":18,"name":"Horror","externalId":32},{"id":19,"name":"Dramat","externalId":33},{"id":20,"name":"Science Fiction","externalId":34},{"id":22,"name":"Familijny","externalId":36},{"id":26,"name":"Inne","externalId":41},{"id":30,"name":"Akcja","externalId":50},{"id":31,"name":"Animowany","externalId":51},{"id":32,"name":"Biograficzny","externalId":52},{"id":33,"name":"Erotyczny","externalId":53},{"id":34,"name":"Fantasy","externalId":54},{"id":35,"name":"Historyczny","externalId":55},{"id":36,"name":"Kostiumowy","externalId":56},{"id":37,"name":"Kryminalny","externalId":57},{"id":38,"name":"Melodramat","externalId":58},{"id":39,"name":"Musical","externalId":59},{"id":40,"name":"Przygodowy","externalId":60},{"id":41,"name":"Psychologiczny","externalId":61},{"id":42,"name":"Western","externalId":62},{"id":43,"name":"Wojenny","externalId":63},{"id":44,"name":"Filmy na życzenie","externalId":64},{"id":53,"name":"Filmy animowane","externalId":73}],
    "4":[{"id":7,"name":"Bajki","externalId":11},{"id":9,"name":"Komedia","externalId":13},{"id":10,"name":"Sensacyjny","externalId":14},{"id":16,"name":"Piosenki","externalId":30},{"id":22,"name":"Familijny","externalId":36},{"id":26,"name":"Inne","externalId":41},{"id":30,"name":"Akcja","externalId":50},{"id":31,"name":"Animowany","externalId":51},{"id":34,"name":"Fantasy","externalId":54},{"id":39,"name":"Musical","externalId":59},{"id":40,"name":"Przygodowy","externalId":60},{"id":44,"name":"Filmy na życzenie","externalId":64},{"id":52,"name":"Programy edukacyjne","externalId":72},{"id":53,"name":"Filmy animowane","externalId":73}],
    "23":[{"id":1,"name":"Rozrywka","externalId":5},{"id":2,"name":"Poradniki","externalId":6},{"id":3,"name":"Kuchnia","externalId":7},{"id":4,"name":"Zdrowie i Uroda","externalId":8},{"id":6,"name":"Motoryzacja","externalId":10},{"id":11,"name":"Dokumentalny","externalId":16},{"id":13,"name":"Podróże i Przyroda","externalId":19},{"id":14,"name":"Dokument i Reportaże","externalId":20},{"id":26,"name":"Inne","externalId":41},{"id":29,"name":"Dom i Ogród","externalId":48},{"id":48,"name":"Hobby","externalId":68},{"id":49,"name":"Kultura","externalId":69},{"id":50,"name":"Moda","externalId":70},{"id":51,"name":"Popularno-naukowe","externalId":71}],
}


TIMEOUT = 15

sess = requests.Session()
sess.cookies = cookielib.LWPCookieJar(COOKIEFILE)


def get_bool(key):
    return addon.getSetting(key).lower() == 'true'


def set_bool(key, value):
    return addon.setSetting(key, 'true' if value else 'false')


# URL to test: https://wrong.host.badssl.com
class GlobalOptions(object):
    """Global options."""

    def __init__(self):
        self._session_level = 0
        self.verify_ssl = get_bool('verify_ssl')
        self.use_urllib3 = get_bool('use_urllib3')
        self.ssl_dialog_launched = get_bool('ssl_dialog_launched')

    def ssl_dialog(self, using_urllib3=False):
        if self.ssl_dialog_launched and self._session_level == 0:
            return
        using_urllib3 = bool(using_urllib3)
        options = [u'Wyłącz weryfikację SSL', u'Bez zmian']
        if using_urllib3:
            options.insert(0, u'Użyj wolniejszego połączenia (zalecane)')
        num = xbmcgui.Dialog().select(u'Problem z połączeniem SSL, co teraz?', options)
        if using_urllib3:
            # getRequests3() error
            if num == 0:  # Użyj wolniejszego połączenia
                self.use_urllib3 = False
            elif num == 1:  # Wyłącz weryfikację SSL
                self.verify_ssl = False
        else:
            # getRequests() error
            if num == 0:  # Wyłącz weryfikację SSL
                self.verify_ssl = False
        set_bool('use_urllib3', self.use_urllib3)
        set_bool('verify_ssl', self.verify_ssl)
        set_bool('ssl_dialog_launched', True)
        self.ssl_dialog_launched = True

    def __enter__(self):
        self._session_level += 1
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self._session_level -= 1


goptions = GlobalOptions()


def media(name, fallback=None):
    """Returns full path to media file."""
    path = os.path.join(MEDIA, name)
    if fallback and not os.path.exists(path):
        return fallback
    return path


def build_url(query):
    query = deunicode_params(query)
    return base_url + '?' + urlencode(query)


def add_item(url, name, image, mode, folder=False, isPlayable=False, infoLabels=None, movie=True,
             itemcount=1, page=1, fanart=None, moviescount=0, properties=None, thumb=None,
             contextmenu=None, art=None, linkdata=None, fallback_image=ADDON_ICON):
    list_item = xbmcgui.ListItem(label=name)
    if isPlayable:
        list_item.setProperty("isPlayable", 'True')
    if not infoLabels:
        infoLabels = {'title': name, 'plot': name}
    list_item.setInfo(type="video", infoLabels=infoLabels)
    if not image:
        image = fallback_image
    if image and image.startswith('//'):
        image = 'https:' + image
    art = {} if art is None else dict(art)
    if fanart:
        art['fanart'] = fanart
    if thumb:
        art['thumb'] = fanart
    art.setdefault('thumb', image)
    art.setdefault('poster', image)
    art.setdefault('banner', art.get('landscape', image))
    art.setdefault('fanart', FANART)
    art = {k: 'https:' + v if v and v.startswith('//') else v for k, v in art.items()}
    list_item.setArt(art)
    if properties:
        list_item.setProperties(properties)
    if contextmenu:
        list_item.addContextMenuItems(contextmenu, replaceItems=False)
    # link data used to build link,to support old one
    linkdata = {} if linkdata is None else dict(linkdata)
    linkdata.setdefault('name', name)
    linkdata.setdefault('image', image)
    linkdata.setdefault('page', page)
    # add item
    ok = xbmcplugin.addDirectoryItem(
        handle=addon_handle,
        url=build_url({'mode': mode, 'url': url, 'page': linkdata['page'], 'moviescount': moviescount,
                       'movie': movie, 'name': linkdata['name'], 'image': linkdata['image']}),
        listitem=list_item,
        isFolder=folder)
    return ok


def setView(typ):
    if addon.getSetting('auto-view') == 'false':
        xbmcplugin.setContent(addon_handle, 'videos')
    else:
        xbmcplugin.setContent(addon_handle, typ)


def getmenu():
    for menu in menudata:
        mud="listcateg"
        if menu['slug']=='live':
            mud='listcateg'
        add_item(str(menu['url'])+':'+menu['slug'], menu['title'], ADDON_ICON, mud, folder=True)


def remove_html_tags(text, nice=True):
    """Remove html tags from a string"""
    if nice:
        if re.match(r'^<table .*<td [^>]+$', text, re.DOTALL):
            return ''  # remove player.pl lead fackup
        text = re.sub(r'<p\b[^>]*?>\s*</p>|<br/?>', '\n', text, 0, re.DOTALL)
    return re.sub('<.*?>', '', text, 0, re.DOTALL)


def home():
    playerpl = PLAYERPL()
    playerpl.sprawdzenie1()
    playerpl.sprawdzenie2()
    add_item('', '[B][COLOR khaki]Ulubione[/COLOR][/B]', ADDON_ICON, "favors", folder=True)
    playerpl.root()
    # getmenu()
    add_item('', 'Kolekcje', ADDON_ICON, "collect", folder=True)
    add_item('', '[B][COLOR khaki]Szukaj[/COLOR][/B]', ADDON_ICON, "search", folder=True)
    add_item('', '[B][COLOR blue]Opcje[/COLOR][/B]', ADDON_ICON, "opcje", folder=False)
    if playerpl.LOGGED == 'true':
        add_item('', '[B][COLOR blue]Wyloguj[/COLOR][/B]', ADDON_ICON, "logout", folder=False)


def get_addon():
    return addon


def set_setting(key, value):
    return get_addon().setSetting(key, value)


def dialog_progress():
    return xbmcgui.DialogProgress()


def xbmc_sleep(time):
    return xbmc.sleep(time)


def deunicode_params(params):
    if sys.version_info < (3,) and isinstance(params, dict):
        def encode(s):
            return s.encode('utf-8') if isinstance(s, unicode) else s
        params = {encode(k): encode(v) for k, v in params.items()}
    return params


def _getRequests(url, data=None, headers=None, params=None):
    xbmc.log('PLAYER.PL: getRequests(%r, data=%r, headers=%r, params=%r)'
             % (url, data, headers, params), xbmc.LOGWARNING)
    params = deunicode_params(params)
    if data:
        if headers.get('Content-Type', '').startswith('application/json'):
            content = sess.post(url, headers=headers, json=data, params=params, verify=goptions.verify_ssl)
        else:
            content = sess.post(url, headers=headers, data=data, params=params, verify=goptions.verify_ssl)
    else:
        content = sess.get(url, headers=headers, params=params, verify=goptions.verify_ssl)
    return content.json()


def _getRequests3(url, data=None, headers=None, params=None):
    # urllib3 seems to be faster in some cases
    xbmc.log('PLAYER.PL: getRequests3(%r, data=%r, headers=%r, params=%r)'
             % (url, data, headers, params), xbmc.LOGWARNING)
    if params:
        params = deunicode_params(params)
        encoded_args = urlencode(params)
        url += '&' if '?' in url else '?'
        url += encoded_args
    pool_kwargs = {}
    if goptions.verify_ssl is False:
        pool_kwargs['cert_reqs'] = 'CERT_NONE'
    elif goptions.verify_ssl is True:
        pool_kwargs['ca_certs'] = where()
    http = urllib3.PoolManager(**pool_kwargs)
    if data:
        if headers.get('Content-Type', '').startswith('application/json'):
            data = json.dumps(data).encode('utf-8')
        resp = http.request('POST', url, headers=headers, body=data)
    else:
        resp = http.request('GET', url, headers=headers)
    text = resp.data.decode('utf-8')
    return json.loads(text)


def getRequests(url, data=None, headers=None, params=None):
    try:
        return _getRequests(url, data=data, headers=headers, params=params)
    except SSLError:
        goptions.ssl_dialog()
    return _getRequests(url, data=data, headers=headers, params=params)


def getRequests3(url, data=None, headers=None, params=None):
    if not goptions.use_urllib3:
        # force use requests
        return getRequests(url, data=data, headers=headers, params=params)
    try:
        return _getRequests3(url, data=data, headers=headers, params=params)
    except MaxRetryError as exc:
        if not isinstance(exc.reason, SSLError3):
            raise
        with goptions:
            goptions.ssl_dialog(using_urllib3=True)
            if not goptions.use_urllib3:
                return getRequests(url, data=data, headers=headers, params=params)
    return _getRequests3(url, data=data, headers=headers, params=params)


class ThreadCall(Thread):
    """
    Async call. Create thread for func(*args, **kwargs), should be started.
    Result will be in thread.result after therad.join() call.
    """

    def __init__(self, func, *args, **kwargs):
        super(ThreadCall, self).__init__()
        self.func = func
        self.args = args
        self.kwargs = kwargs
        self.result = None

    def run(self):
        self.result = self.func(*self.args, **self.kwargs)


def idle():

    if float(xbmcaddon.Addon('xbmc.addon').getAddonInfo('version')[:4]) > 17.6:
        xbmc.executebuiltin('Dialog.Close(busydialognocancel)')
    else:
        xbmc.executebuiltin('Dialog.Close(busydialog)')


def busy():

    if float(xbmcaddon.Addon('xbmc.addon').getAddonInfo('version')[:4]) > 17.6:
        xbmc.executebuiltin('ActivateWindow(busydialognocancel)')
    else:
        xbmc.executebuiltin('ActivateWindow(busydialog)')


def PLchar(*args, **kwargs):
    sep = kwargs.pop('sep', ' ')
    if kwargs:
        raise TypeError('Unexpected keywoard arguemnt(s): %s' % ' '.join(kwargs.keys()))
    out = ''
    for i, char in enumerate(args):
        if type(char) is not str:
            char = char.encode('utf-8')
        char = char.replace('\\u0105','\xc4\x85').replace('\\u0104','\xc4\x84')
        char = char.replace('\\u0107','\xc4\x87').replace('\\u0106','\xc4\x86')
        char = char.replace('\\u0119','\xc4\x99').replace('\\u0118','\xc4\x98')
        char = char.replace('\\u0142','\xc5\x82').replace('\\u0141','\xc5\x81')
        char = char.replace('\\u0144','\xc5\x84').replace('\\u0144','\xc5\x83')
        char = char.replace('\\u00f3','\xc3\xb3').replace('\\u00d3','\xc3\x93')
        char = char.replace('\\u015b','\xc5\x9b').replace('\\u015a','\xc5\x9a')
        char = char.replace('\\u017a','\xc5\xba').replace('\\u0179','\xc5\xb9')
        char = char.replace('\\u017c','\xc5\xbc').replace('\\u017b','\xc5\xbb')
        char = char.replace('&#8217;',"'")
        char = char.replace('&#8211;',"-")
        char = char.replace('&#8230;',"...")
        char = char.replace('&#8222;','"').replace('&#8221;','"')
        char = char.replace('[&hellip;]',"...")
        char = char.replace('&#038;',"&")
        char = char.replace('&#039;',"'")
        char = char.replace('&quot;','"')
        char = char.replace('&nbsp;',".").replace('&amp;','&')
        if i:
            out += sep
        out += char
    return out


def historyLoad():
    return addon_data.get('history.items', [])


def historyAdd(entry):
    if not isinstance(entry, unicode):
        entry = entry.decode('utf-8')
    history = historyLoad()
    history.insert(0, entry)
    addon_data.set('history.items', history[:HISTORY_SIZE])


def historyDel(entry):
    if not isinstance(entry, unicode):
        entry = entry.decode('utf-8')
    history = [item for item in historyLoad() if item != entry]
    addon_data.set('history.items', history[:HISTORY_SIZE])


def historyClear():
    addon_data.remove('history.items')


class PLAYERPL(object):

    MaxMax = 10000

    def __init__(self):

        self._mylist = None

        self.api_base = 'https://player.pl/playerapi/'
        self.login_api = 'https://konto.tvn.pl/oauth/'

        self.GETTOKEN = self.login_api + 'tvn-reverse-onetime-code/create'
        self.POSTTOKEN = self.login_api + 'token'
        self.SUBSCRIBER = self.api_base + 'subscriber/login/token'
        self.SUBSCRIBERDETAIL = self.api_base + 'subscriber/detail'
        self.JINFO = self.api_base + 'info'
        self.TRANSLATE = self.api_base + 'item/translate'
        self.KATEGORIE = self.api_base + 'item/category/list'

        self.PRODUCTVODLIST = self.api_base + 'product/vod/list'
        self.PRODUCTLIVELIST = self.api_base + 'product/list/list'

        self.PARAMS = {'4K': 'true', 'platform': PF}

        self.HEADERS3 = {
            'Host': 'konto.tvn.pl',
            'user-agent': UA,
            'content-type': 'application/x-www-form-urlencoded; charset=UTF-8'
        }

        self.ACCESS_TOKEN = addon.getSetting('access_token')
        self.USER_PUB = addon.getSetting('user_pub')
        self.USER_HASH = addon.getSetting('user_hash')
        self.REFRESH_TOKEN = addon.getSetting('refresh_token')
        self.DEVICE_ID = addon.getSetting('device_id')
        self.TOKEN = addon.getSetting('token')
        self.MAKER = addon.getSetting('maker_id')
        self.USAGENT = addon.getSetting('usagent_id')
        self.USAGENTVER = addon.getSetting('usagentver_id')
        self.SELECTED_PROFILE = addon.getSetting('selected_profile')
        self.SELECTED_PROFILE_ID = addon.getSetting('selected_profile_id')
        self.ENABLE_SUBS = addon.getSetting('subtitles')
        self.SUBS_DEFAULT = addon.getSetting('subtitles_lang_default')
        self.LOGGED = addon.getSetting('logged')

        self.update_headers2()

        self.MYLIST_CACHE_TIMEOUT = 3 * 3600  # cache valid time for mylist: 3h
        self.skip_unaviable = get_bool('avaliable_only')
        self.fix_api = get_bool('fix_api')
        self.remove_duplicates = get_bool('remove_duplicates')
        self.partial_size = int(addon.getSetting('partial_size') or 1000)
        # self.force_media_fanart = get_bool('self.force_media_fanart')
        self.force_media_fanart = True
        self.force_media_fanart_width = 1280
        self.force_media_fanart_quality = 85
        self._precessed_vid_list = set()
        self.dywiz = '–'

    def params(self, maxResults=False, **kwargs):
        """
        Get default query params. Extend self.PARAMS.

        maxResults : bool or int
            False to skip, Ftrue for auto or integer
        kwargs : dict(str, any)
            Extra pamars appended to result
        """
        params = dict(self.PARAMS)
        if maxResults:
            if maxResults is True:
                maxResults = self.MaxMax if self.skip_unaviable else self.partial_size
            params['maxResults'] = maxResults or 0
            params['firstResult'] = 0
        params.update(kwargs)
        return params

    def update_headers2(self):
        self.HEADERS2 = {
            'Authorization': 'Basic',
            'API-DeviceInfo': '%s;%s;Android;9;%s;1.0.38(62);' % (
                self.USAGENT, self.USAGENTVER, self.MAKER),
            'API-DeviceUid': self.DEVICE_ID,
            'User-Agent': UA,
            'Host': 'player.pl',
            'X-NewRelic-ID': 'VQEOV1JbABABV1ZaBgMDUFU=',
            'API-Authentication': self.ACCESS_TOKEN,
            'API-SubscriberHash': self.USER_HASH,
            'API-SubscriberPub': self.USER_PUB,
            'API-ProfileUid': self.SELECTED_PROFILE_ID,
        }

    def get_meta_data(self, data):
        if not data.get('active', True):
            return '', '', '', None, None
        tytul = data['title']
        if data.get('uhd'):
            tytul = '%s [4K]' % (tytul or '')
        opis = data.get("description")
        if not opis:
            opis = data.get("lead")
        if opis:
            opis = remove_html_tags(opis).strip()
        images = {}
        # See: https://kodi.wiki/view/Artwork_types
        # New art images must be added to MetaDane
        for prop, (iname, uname) in {'foto': ('smart_tv', 'mainUrl'),
                                     'fanart': ('smart_tv', 'mainUrl'),
                                     'thumb': ('smart_tv', 'miniUrl'),
                                     'poster': ('vertical', 'mainUrl'),
                                     'landscape': ('smart_tv', 'mainUrl')}.items():
            try:
                images[prop] = data['images'][iname][0][uname]
            except (KeyError, IndexError) as exc:
                xbmc.log('PLAYER.PL: no image %s.%s %r in %r' % (
                    iname, uname, exc, data.get('images')), xbmc.LOGDEBUG)
                images[prop] = None
        if self.force_media_fanart and images['fanart']:
            iurl, _, iparams = images['fanart'].partition('?')
            iparams = dict(parse_qsl(iparams))
            if iparams.get('dstw', '').isdigit() and iparams.get('dstw', '').isdigit():
                w, h = int(iparams['dstw']), int(iparams['dsth'])
                if w != self.force_media_fanart_width:
                    iparams['dstw'] = self.force_media_fanart_width
                    iparams['dsth'] = h * self.force_media_fanart_width // (w or 1)
                iparams['quality'] = self.force_media_fanart_quality
            images['fanart'] = '%s?%s' % (iurl, urlencode(iparams))
        sezon = bool(data.get('showSeasonNumber')) or data.get('type') == 'SERIAL'
        epizod = bool(data.get("showEpisodeNumber"))
        allowed = self.is_allowed(data)
        return MetaDane(tytul, opis, sezon=sezon, epizod=epizod, allowed=allowed, **images)

    def createDatas(self):

        def gen_hex_code(myrange=6):
            import random
            return ''.join([random.choice('0123456789abcdef') for x in xrange(myrange)])


        def uniq_usagent():
            usagent_id = ''

            if addon.getSetting('usagent_id'):
                usagent_id = addon.getSetting('usagent_id')
            else:
                usagent_id = '2e520525f3'+ gen_hex_code(6)
            set_setting('usagent_id', usagent_id)
            return usagent_id


        def uniq_usagentver():
            usagentver_id = ''

            if addon.getSetting('usagentver_id'):
                usagentver_id = addon.getSetting('usagentver_id')
            else:
                usagentver_id = '2e520525f2'+ gen_hex_code(6)
            set_setting('usagentver_id', usagentver_id)
            return usagentver_id

        def uniq_maker():
            maker_id = ''

            if addon.getSetting('maker_id'):
                maker_id = addon.getSetting('maker_id')
            else:
                maker_id = gen_hex_code(16)
            set_setting('maker_id', maker_id)
            return maker_id

        def uniq_id():
            device_id = ''

            if addon.getSetting('device_id'):
                device_id = addon.getSetting('device_id')
            else:
                device_id = gen_hex_code(16)
            set_setting('device_id', device_id)
            return device_id
        self.DEVICE_ID =uniq_id()
        self.MAKER = uniq_maker()
        self.USAGENT = uniq_usagent()
        self.USAGENTVER = uniq_usagentver()
        return

    def sprawdzenie1(self):

        if not self.DEVICE_ID or not self.MAKER or not self.USAGENT or not self.USAGENTVER:
            self.createDatas()
        if not self.REFRESH_TOKEN and self.LOGGED == 'true':
            self.remove_mylist()
            POST_DATA = 'scope=/pub-api/user/me&client_id=Player_TV_Android_28d3dcc063672068'
            data = getRequests(self.GETTOKEN, data = POST_DATA, headers=self.HEADERS3)
            kod = data.get('code')
            dg = dialog_progress()
            dg.create('Uwaga','Przepisz kod: [B]%s[/B]\n Na stronie https://player.pl/zaloguj-tv'%kod)

            time_to_wait=340
            secs = 0
            increment = 100 // time_to_wait
            cancelled = False
            b= 'acces_denied'
            while secs <= time_to_wait:
                if (dg.iscanceled()): cancelled = True; break
                if secs != 0: xbmc_sleep(3000)
                secs_left = time_to_wait - secs
                if secs_left == 0: percent = 100
                else: percent = increment * secs
                POST_DATA = 'grant_type=tvn_reverse_onetime_code&code=%s&client_id=Player_TV_Android_28d3dcc063672068'%kod
                data = getRequests(self.POSTTOKEN, data=POST_DATA, headers=self.HEADERS3)
                token_type = data.get("token_type",None)
                errory = data.get('error',None)
                if token_type == 'bearer': break
                secs += 1


                dg.update(percent)
                secs += 1
            dg.close()

            if not cancelled:
                self.ACCESS_TOKEN = data.get('access_token',None)
                self.USER_PUB = data.get('user_pub',None)
                self.USER_HASH = data.get('user_hash',None)
                self.REFRESH_TOKEN = data.get('refresh_token',None)

                set_setting('access_token', self.ACCESS_TOKEN)
                set_setting('user_pub', self.USER_PUB)
                set_setting('user_hash', self.USER_HASH)
                set_setting('refresh_token', self.REFRESH_TOKEN)

    def sprawdzenie2(self):

        if self.REFRESH_TOKEN:

            PARAMS = {'4K': 'true','platform': PF}
            self.HEADERS2['Content-Type'] =  'application/json; charset=UTF-8'

            POST_DATA = {"agent":self.USAGENT,"agentVersion":self.USAGENTVER,"appVersion":"1.0.38(62)","maker":self.MAKER,"os":"Android","osVersion":"9","token":self.ACCESS_TOKEN,"uid":self.DEVICE_ID}
            data = getRequests(self.SUBSCRIBER, data = POST_DATA, headers=self.HEADERS2,params=PARAMS)


            self.SELECTED_PROFILE = data.get('profile',{}).get('name',None)
            self.SELECTED_PROFILE_ID = data.get('profile',{}).get('externalUid',None)

            self.HEADERS2['API-ProfileUid'] =  self.SELECTED_PROFILE_ID


            set_setting('selected_profile_id', self.SELECTED_PROFILE_ID)
            set_setting('selected_profile', self.SELECTED_PROFILE)
        if self.LOGGED != 'true':
            add_item('', '[B][COLOR blue]Zaloguj[/COLOR][/B]', ADDON_ICON, "login", folder=False)

    def getTranslate(self,id_):

        PARAMS = {'4K': 'true','platform': PF, 'id': id_}
        data = getRequests(self.TRANSLATE,headers=self.HEADERS2, params=PARAMS)
        return data

    def getPlaylist(self,id_):
        self.refreshTokenTVN()

        data = self.getTranslate(str(id_))
        rodzaj = "LIVE" if data.get("type_", "MOVIE") == "LIVE" else "MOVIE";

        HEADERSz = {
            'Authorization': 'Basic',
            # 'API-DeviceInfo': '%s;%s;Android;9;%s;1.0.38(62);'%(self.USAGENT, self.USAGENTVER, self.MAKER ),
            'API-Authentication': self.ACCESS_TOKEN,
            'API-DeviceUid': self.DEVICE_ID,
            'API-SubscriberHash': self.USER_HASH,
            'API-SubscriberPub': self.USER_PUB,
            'API-ProfileUid': self.SELECTED_PROFILE_ID,
            'User-Agent': 'okhttp/3.3.1 Android',
            'Host': 'player.pl',
            'X-NewRelic-ID': 'VQEOV1JbABABV1ZaBgMDUFU=',
        }

        urlk = 'https://player.pl/playerapi/product/%s/player/configuration' % id_
        data = getRequests(urlk, headers=HEADERSz, params=self.params(type=rodzaj))

        try:
            vidsesid = data["videoSession"]["videoSessionId"]
            prolongvidses = data["prolongVideoSessionUrl"]
        except:
            vidsesid=False
            pass

        PARAMS = {'type': rodzaj, 'platform': PF}
        data = getRequests(self.api_base+'item/%s/playlist' % id_, headers=HEADERSz, params=PARAMS)

        if not data:
            urlk = 'https://player.pl/playerapi/item/%s/playlist' % id_
            PARAMS = {'type': rodzaj, 'platform': UA, 'videoSessionId': vidsesid}
            data = getRequests(urlk, headers=HEADERSz, PARAMS=PARAMS)

        xbmc.log('PLAYER.PL: getPlaylist(%r): data: %r' % (id_, data), xbmc.LOGWARNING)
        vid = data['movie']
        outsub = []
        try:
            subs = vid['video']['subtitles']
            for lan, sub in subs.items():
                lang = sub['label']

                srcsub = sub['src']
                outsub.append({'lang':lang, 'url':srcsub})
        except:
            pass

        src = vid['video']['sources']['dash']['url']
        tshiftl = vid.get('video', {}).get('time_shift', {}).get('total_length', 0)
        if tshiftl > 0:
            src += '&dvr=' + str(tshiftl * 1000 + 1000)
        xbmc.log('PLAYER.PL: video protections: %s' % vid['video'], xbmc.LOGWARNING)
        protect = vid['video']['protections']
        if 'widevine' not in protect:
            xbmcgui.Dialog().ok(u'[B]DRM[/B]', u'Nieobsługiwany DRM:[CR]%s' % u', '.join(protect.keys()))
        widev = protect['widevine']['src']
        if vidsesid:
            widev += '&videoSessionId=%s' % vidsesid
        return src, widev, outsub

    def refreshTokenTVN(self):
        POST_DATA = 'grant_type=refresh_token&refresh_token=%s&client_id=Player_TV_Android_28d3dcc063672068'%self.REFRESH_TOKEN
        data = getRequests(self.POSTTOKEN,data = POST_DATA, headers=self.HEADERS3)
        if data.get('error_description') == 'Token is still valid.':
            return
        self.ACCESS_TOKEN = data.get('access_token')
        self.USER_PUB = data.get('user_pub')
        self.USER_HASH = data.get('user_hash')
        self.REFRESH_TOKEN = data.get('refresh_token')
        set_setting('access_token', self.ACCESS_TOKEN)
        set_setting('user_pub', self.USER_PUB)
        set_setting('user_hash', self.USER_HASH)
        set_setting('refresh_token', self.REFRESH_TOKEN)
        self.update_headers2()
        return data

    def playvid(self, id):

        stream_url, license_url, subtitles = self.getPlaylist(str(id))
        subt = ''
        if subtitles and self.ENABLE_SUBS =='true':
            t = [ x.get('lang') for x in subtitles]
            u = [ x.get('url') for x in subtitles]
            al = "subtitles"

            if len(subtitles)>1:

                if self.SUBS_DEFAULT != '' and self.SUBS_DEFAULT in t:
                    subt = next((x for x in subtitles if x.get('lang') == self.SUBS_DEFAULT), None).get('url')
                else:
                    select = xbmcgui.Dialog().select(al, t)
                    if select > -1:
                       subt = u[select];
                       addon.setSetting(id='subtitles_lang_default', value=str(t[select]))

                    else:
                       subt =''
            else:
                subt = u[0];



        import inputstreamhelper

        PROTOCOL = 'mpd'
        DRM = 'com.widevine.alpha'

        str_url = stream_url

        HEADERSz = {
            'User-Agent': UA,
        }

        is_helper = inputstreamhelper.Helper(PROTOCOL, drm=DRM)
        if is_helper.check_inputstream():

            play_item = xbmcgui.ListItem(path=str_url)
            play_item.setContentLookup(False)
            if subt:
                r = requests.get(subt)
                with open(SUBTITLEFILE, 'wb') as f:
                   f.write(r.content)
                play_item.setSubtitles([SUBTITLEFILE])


            if sys.version_info >= (3,0,0):
                play_item.setProperty('inputstream', is_helper.inputstream_addon)
            else:
                play_item.setProperty('inputstreamaddon', is_helper.inputstream_addon)

            play_item.setMimeType('application/xml+dash')
            play_item.setContentLookup(False)
            play_item.setProperty('inputstream.adaptive.manifest_type', PROTOCOL)
            play_item.setProperty('inputstream.adaptive.license_type', DRM)
            if 'dvr' in str_url:
                play_item.setProperty('inputstream.adaptive.manifest_update_parameter', 'full')
            play_item.setProperty('inputstream.adaptive.license_key', license_url+'|Content-Type=|R{SSM}|')
            play_item.setProperty('inputstream.adaptive.license_flags', "persistent_storage")
            play_item.setProperty('inputstream.adaptive.stream_headers', urlencode(HEADERSz))
        xbmcplugin.setResolvedUrl(addon_handle, True, listitem=play_item)

    def slug_data(self, idslug, maxResults=True, plOnly=False):
        xbmc.log('PLAYER.PL: slug %s started' % idslug, xbmc.LOGWARNING)
        gid, slug = idslug.split(':')
        PARAMS = self.params(maxResults=maxResults)
        PARAMS['category[]'] = slug
        PARAMS['sort'] = 'createdAt'
        PARAMS['order'] = 'desc'
        if gid:
            PARAMS['genreId[]'] = gid
        if plOnly:
            PARAMS['vodFilter[]'] = 'POLISH'
        urlk = self.PRODUCTVODLIST
        data = getRequests3(urlk, headers=self.HEADERS2, params=PARAMS)
        xbmc.log('PLAYER.PL: slug %s done' % idslug, xbmc.LOGWARNING)
        return data

    def async_slug_data(self, idslug, maxResults=True, plOnly=False):
        thread = ThreadCall(self.slug_data, idslug, maxResults=maxResults, plOnly=plOnly)
        thread.start()
        return thread

    def get_mylist(self):
        xbmc.log('PLAYER.PL: mylist started', xbmc.LOGWARNING)
        data = getRequests3('https://player.pl/playerapi/subscriber/product/available/list?4K=true&platform=ANDROID_TV',
                            headers=self.HEADERS2, params={})
        xbmc.log('PLAYER.PL: mylist done', xbmc.LOGWARNING)
        return set(data)

    @property
    def mylist_cache_path(self):
        return os.path.join(CACHEPATH, 'mylist')

    def save_mylist(self, mylist=None):
        path = self.mylist_cache_path
        if mylist is None:
            mylist = self.get_mylist()
        try:
            os.makedirs(CACHEPATH)
        except OSError:
            pass  # exists
        save_ints(path, mylist)

    def load_mylist(self, auto_cache=True):
        path = self.mylist_cache_path
        try:
            if time.time() - os.stat(path).st_mtime < self.MYLIST_CACHE_TIMEOUT:
                return set(load_ints(path))
        except OSError:
            pass
        except Exception as exc:
            xbmc.log('PLAYER.PL: Can not load mylist from %r: %r' % (path, exc), xbmc.LOGWARNING)
            self.remove_mylist()
        mylist = self.get_mylist()
        if auto_cache:
            try:
                self.save_mylist(mylist)
            except OSError:
                xbmc.log('PLAYER.PL: Can not save mylist to %r' % path, xbmc.LOGWARNING)
        return mylist

    def remove_mylist(self):
        path = self.mylist_cache_path
        if os.path.exists(path):
            try:
                os.unlink(path)
            except Exception as exc:
                xbmc.log('PLAYER.PL: Can not remove mylist cache %r: %r' % (path, exc),
                         xbmc.LOGWARNING)

    @property
    def mylist(self):
        if self._mylist is None:
            self._mylist = self.load_mylist()
        return self._mylist

    @mylist.deleter
    def mylist(self):
        self.remove_mylist()

    def is_allowed(self, vod):
        """Check if item (video, folder) is avaliable in current pay plan."""
        return (
            # not have to pay and not on ncPlus, it's means free
            not (vod.get('payable') or vod.get('ncPlus'))
            # or it's on myslit, it's means it is in pay plan
            or vod.get('id') in self.mylist)

    def add_media_item(self, mud, vid, meta=None, suffix=None, folder=False, isPlayable=None,
                       vod=None, linkdata=None):
        """
        Add default media item to xbmc.list.
        if `isPlayable` is None (default) it's forced to `not folder`,
        because folder is not playable.
        """
        if vid in self._precessed_vid_list:
            xbmc.log(u'PLAYER.PL: item %s (%r) already processed' % (vid, meta.tytul), xbmc.LOGWARNING)
            if self.remove_duplicates:
                return
        if meta is None and vod is not None:
            meta = self.get_meta_data(vod)
        allowed = (meta and meta.allowed is True) or vid in self.mylist
        if allowed or not self.skip_unaviable:
            no_playable = not (mud or '').strip() or meta.sezon
            if no_playable:
                isPlayable = False
                folder = True
            elif isPlayable is None:
                isPlayable = not folder
            if suffix is None:
                suffix = u''
                if no_playable and not allowed:
                    # auto suffix for non-playable video
                    suffix += u' - [COLOR khaki]([I]brak w pakiecie[/I])[/COLOR]'
                sched = vod and vod.get('displaySchedules')
                if sched and sched[0].get('type') == 'SOON':
                    suffix += u' [COLOR gray] [LIGHT] (od %s)[/LIGHT][/COLOR]' % sched[0]['till'][:-3]
            suffix = suffix or ''
            title = PLchar(meta.tytul, suffix, sep='')
            descr = PLchar(meta.opis or meta.tytul, suffix, sep='\n')
            info = {
                'title': title,
                'plot': descr,
                'plotoutline': descr,
                'tagline': descr,
                # 'genre': 'Nawalanka',  # this is shown in Arctic: Zephyr 2 - Resurrection Mod
            }
            add_item(str(vid), title, meta.foto or ADDON_ICON, mud,
                     folder=folder, isPlayable=isPlayable, infoLabels=info, art=meta.art,
                     linkdata=linkdata)
            self._precessed_vid_list.add(vid)

    def process_vod_list(self, vod_list, subitem=None):
        """
        Process list of VOD items.
        Check if playable or serial. Add items to Kodi list.
        """
        for vod in vod_list:
            if subitem:
                vod = vod[subitem]
            vid = vod['id']
            meta = self.get_meta_data(vod)
            mud, fold = ' ', None
            if meta.allowed is True:
                if vod['type'] == 'SERIAL':
                    mud = 'listcategSerial'
                    fold = True
                else:
                    mud = 'playvid'
                    fold = False
            self.add_media_item(mud, vid, meta, folder=fold, vod=vod)

    def listCollection(self):
        self.refreshTokenTVN()
        data = getRequests('https://player.pl/playerapi/product/section/list',
                           headers=self.HEADERS2, params=self.params(maxResults=True, order='asc'))
        mud = "listcollectContent"
        for vod in data:
            vid = vod['id']
            slug = vod['slug']
            meta = self.get_meta_data(vod)
            info = {
                'title': PLchar(meta.tytul),
                'plot': PLchar(meta.opis or meta.tytul),
            }
            add_item(str(vid)+':'+str(slug), meta.tytul, meta.foto, mud, folder=True,
                     infoLabels=info, art=meta.art)
        setView('movies')
        # xbmcplugin.setContent(addon_handle, 'movies')
        xbmcplugin.addSortMethod(addon_handle, sortMethod=xbmcplugin.SORT_METHOD_TITLE, label2Mask="%R, %Y, %P")
        xbmcplugin.endOfDirectory(addon_handle)

    def listFavorites(self):
        self.refreshTokenTVN()

        data = getRequests('https://player.pl/playerapi/subscriber/bookmark',
                           headers=self.HEADERS2, params=self.params(type='FAVOURITE'))
        try:
            self.process_vod_list(data['items'], subitem='item')
            setView('tvshows')
            # xbmcplugin.setContent(addon_handle, 'tvshows')
            xbmcplugin.addSortMethod(addon_handle, sortMethod=xbmcplugin.SORT_METHOD_TITLE, label2Mask="%R, %Y, %P")
            xbmcplugin.endOfDirectory(addon_handle)
        except:
            raise  # skip fallback
            # Falback: Kodi Favorites
            xbmc.executebuiltin("ActivateWindow(10134)")

    def listSearch(self, query):
        self.refreshTokenTVN()
        PARAMS = self.params(keyword=query)

        urlk = 'https://player.pl/playerapi/product/live/search'
        lives = getRequests(urlk, headers=self.HEADERS2, params=PARAMS)
        xbmc.log('PLAYER.PL: listSearch(%r): params=%r, lives=%r' % (query, PARAMS, lives), xbmc.LOGWARNING)
        lives = lives['items']
        # -- commented out, it does do nothing   (rysson)
        # if len(lives)>0:
        #     for live in lives:
        #         ac=''
        urlk = 'https://player.pl/playerapi/product/vod/search'
        data = getRequests(urlk, headers=self.HEADERS2, params=PARAMS)
        self.process_vod_list(data['items'])
        # setView('tvshows')
        xbmcplugin.setContent(addon_handle, 'videos')
        xbmcplugin.addSortMethod(addon_handle, sortMethod=xbmcplugin.SORT_METHOD_TITLE, label2Mask = "%R, %Y, %P")
        xbmcplugin.endOfDirectory(addon_handle)

    def listEpizody(self, tytsezid):
        idmain, idsezon = tytsezid.split(':')
        self.refreshTokenTVN()

        urlk = 'https://player.pl/playerapi/product/vod/serial/%s/season/%s/episode/list' % (idmain, idsezon)

        epizody = getRequests(urlk, headers=self.HEADERS2, params=self.PARAMS)
        for vod in epizody:
            vid = vod['id']
            meta = self.get_meta_data(vod)
            epiz = vod["episode"]
            sez = (vod["season"]["number"])
            tyt = PLchar((vod["season"]["serial"]["title"]))
            if 'fakty-' in vod.get('shareUrl', ''):
                name = PLchar(tyt, '-', vod['title'])
                tytul = PLchar(tyt, self.dywiz, vod['title'])
            else:
                name = '%s - S%02dE%02d' % (tyt, sez, epiz)
                tytul = '%s %s S%02dE%02d' % (tyt, PLchar(self.dywiz), sez, epiz)
            if vod.get('title'):
                tytul += PLchar('', self.dywiz, vod['title'].strip())
            meta = meta._replace(tytul=tytul)
            self.add_media_item('playvid', vid, meta, folder=False, vod=vod, linkdata={'name': name})
        setView('episodes')
        # xbmcplugin.setContent(addon_handle, 'episodes')
        xbmcplugin.addSortMethod(addon_handle, sortMethod=xbmcplugin.SORT_METHOD_TITLE, label2Mask="%R, %Y, %P")
        xbmcplugin.endOfDirectory(addon_handle)

    def getSezony(self, id, tytul, opis, foto, typ):
        self.refreshTokenTVN()
        urlk = 'https://player.pl/playerapi/product/vod/serial/%s/season/list' % id
        out = []
        sezony = getRequests(urlk, headers=self.HEADERS2, params=self.PARAMS)
        for sezon in sezony:
            seas = str(sezon['number'])
            urlid = '%s:%s' % (id, sezon['id'])
            title = '%s - Sezon %s' % (tytul, seas)
            if not typ:
                seas = str(sezon["display"])
                title = '%s / %s' % (tytul, seas)
            out.append({'title': PLchar(title), 'url': urlid, 'img': foto, 'plot': PLchar(opis)})
        return out

    def listCategSerial(self, id):
        self.refreshTokenTVN()
        urlk = 'https://player.pl/playerapi/product/vod/serial/%s' % id
        data = getRequests(urlk, headers=self.HEADERS2, params=self.PARAMS)
        meta = self.get_meta_data(data)
        typ = True
        if meta.sezon or meta.epizod:
            if not meta.sezon:
                typ = False
            items = self.getSezony(id, meta.tytul, meta.opis, meta.foto, typ)
            for f in items:
                add_item(name=f.get('title'), url=f.get('url'), mode='listEpizody', image=f.get('img'),
                         folder=True, infoLabels=f)
        setView('episodes')
        # xbmcplugin.setContent(addon_handle, 'episodes')
        xbmcplugin.addSortMethod(addon_handle, sortMethod=xbmcplugin.SORT_METHOD_TITLE, label2Mask="%R, %Y, %P")
        xbmcplugin.endOfDirectory(addon_handle)

    def listCollectContent(self, idslug):
        self.refreshTokenTVN()
        vid, slug = idslug.split(':')
        urlk = 'https://player.pl/playerapi/product/section/%s' % (vid)
        data = getRequests(urlk, headers=self.HEADERS2, params=self.params(maxResults=True))
        self.process_vod_list(data['items'])
        setView('movies')
        # xbmcplugin.setContent(int(sys.argv[1]), 'movies')
        xbmcplugin.addSortMethod(addon_handle, sortMethod=xbmcplugin.SORT_METHOD_TITLE,
                                 label2Mask="%R, %Y, %P")
        xbmcplugin.endOfDirectory(addon_handle)

    def listCategContent(self, idslug):
        self.refreshTokenTVN()
        gid, slug = idslug.split(':')
        if slug == 'live':
            dane = self.getTvs(genre=gid)
            for f in dane:
                add_item(name=f.get('title'), url=f.get('url'), mode='playvid', image=f.get('img'),
                         folder=False, isPlayable=True, infoLabels=f)
        else:
            data = self.slug_data(idslug, maxResults=True if gid else self.MaxMax)
            self.process_vod_list(data['items'])
            setView('tvshows')
            # xbmcplugin.setContent(int(sys.argv[1]), 'tvshows')
            xbmcplugin.addSortMethod(addon_handle, sortMethod=xbmcplugin.SORT_METHOD_TITLE, label2Mask="%R, %Y, %P")
        xbmcplugin.endOfDirectory(addon_handle)

    def getTvs(self, genre=None):
        self.refreshTokenTVN()
        urlk = 'https://player.pl/playerapi/product/live/list'
        out = []
        reqargs = {}
        if genre:
            reqargs['genreId[]'] = str(genre)
        data = getRequests(urlk, headers=self.HEADERS2, params=self.params(**reqargs))
        for dd in data:
            vid = dd['id']
            tyt = PLchar(dd['title'])
            foto = dd['images']['pc'][0]['mainUrl']
            foto = 'https:' + foto if foto.startswith('//') else foto
            # urlid = '%s:%s'%(vid,'kanal')  # mbebe
            urlid = vid  # kszaq
            opis = dd.get('lead', '')
            allowed = self.is_allowed(dd)
            if not allowed:
                tyt += ' - [I][COLOR khaki](brak w pakiecie)[/COLOR][/I]'
            if allowed or not self.skip_unaviable:
                out.append({'title': tyt, 'url': urlid, 'img': foto, 'plot': PLchar(opis)})
        return out

    def listCateg(self, idslug):
        getRequests(url=self.KATEGORIE, headers=self.HEADERS2, params=self.params())
        gid, slug = idslug.split(':')
        if slug == 'live':
            dane = self.getTvs()
            for f in dane:
                add_item(name=f.get('title'), url=f.get('url'), mode='playvid', image=f.get('img'),
                         folder=False, isPlayable=True, infoLabels=f)
        else:
            if self.skip_unaviable:
                xbmc.log('PLAYER.PL: folder start', xbmc.LOGWARNING)
                self.refreshTokenTVN()
                mylist_thread = ThreadCall(self.load_mylist)
                mylist_thread.start()
                slugs = {sid: self.async_slug_data(sid, maxResults=self.MaxMax) for f in serialemenu[gid]
                         for sid in ('%s:%s' % (f['id'], slug),)}
                slugs[':%s' % slug] = self.async_slug_data(':%s' % slug, maxResults=self.MaxMax)
                xbmc.log('PLAYER.PL: folder prepared', xbmc.LOGWARNING)
                for th in slugs.values():
                    th.join()
                mylist_thread.join()
                xbmc.log('PLAYER.PL: folder joined', xbmc.LOGWARNING)
                mylist = mylist_thread.result
                slugs = {sid: thread.result['items'] for sid, thread in slugs.items()}
                xbmc.log('PLAYER.PL: folder catch data', xbmc.LOGWARNING)
                if not mylist:
                    xbmc.log('PLAYER.PL: XXX: mylist=%r' % mylist, xbmc.LOGWARNING)
            try:
                dane = serialemenu[gid]
            except KeyError:
                dane = getRequests(url='https://player.pl/playerapi/item/category/%s/genre/list' % gid,
                                   headers=self.HEADERS2, params=self.params())
            if self.skip_unaviable:
                dane.append({'id': '', 'name': '[B]Wszystkie[/B]', '_props_': {'SpecialSort': 'top'}})
            for f in dane:
                name = f['name']
                urlk = '%s:%s' % (f['id'], slug)
                if self.skip_unaviable:
                    xbmc.log('PLAYER.PL: ul=%s, mylist=%s, slg=%s, start counting' % (urlk, len(mylist), len(slugs[urlk])), xbmc.LOGWARNING)
                    # count = sum(item['id'] in mylist for item in slugs[urlk])
                    count = len({item['id'] for item in slugs[urlk]} & mylist)
                    xbmc.log('PLAYER.PL: ul=%s, mylist=%s, slg=%s, cnt=%s' % (urlk, len(mylist), len(slugs[urlk]), count), xbmc.LOGWARNING)
                    fmt = '{name} ({count})' if count else '{name} ([COLOR red]brak[/COLOR])'
                    name = fmt.format(name=name, count=count)
                image = media('genre/%s.png' % f['id'], fallback=ADDON_ICON)
                add_item(urlk, name, image, mode='listcategContent', folder=True, isPlayable=False,
                         properties=f.get('_props_'))

        xbmc.log('PLAYER.PL: folder items done', xbmc.LOGWARNING)
        setView('tvshows')
        xbmcplugin.addSortMethod(addon_handle, sortMethod=xbmcplugin.SORT_METHOD_TITLE,
                                 label2Mask="%R, %Y, %P")
        xbmcplugin.endOfDirectory(addon_handle)
        xbmc.log('PLAYER.PL: folder done, skip=%s' % self.skip_unaviable, xbmc.LOGWARNING)

    @property
    def category_tree(self):
        self.refreshTokenTVN()
        return getRequests(url=self.KATEGORIE, headers=self.HEADERS2, params=self.params())

    def root(self):
        """Get ROOT folder (main menu)."""
        # add_item('17:live', 'TV', ADDON_ICON, 'listcateg', folder=True)
        self.category_list()

    def category_list(self, exlink=None):
        """Get root categories (main menu)."""
        for item in self.category_tree:
            if item.get('genres') and item['slug'] not in slug_blacklist:
                name = item['name']
                image = (item.get('image', {}).get('smart_tv') or [{}])[0].get('mainUrl')
                url = '%s:%s' % (item['id'], item['slug'])
                add_item(url, name, image=image, mode='category_genre_list', folder=True)

    def xxx_content(self, exlink=None):
        """Get ROOT content ???"""
        self.refreshTokenTVN()
        data = getRequests('https://player.pl/playerapi/document/menu-category/content',
                           headers=self.HEADERS2, params=self.params())

    def category_genre_list(self, exlink):
        """Get ROOT folder content (main menu)."""
        try:
            cid, slug = exlink.split(':', 1)
            cid = int(cid)
        except ValueError:
            raise ValueError('cannot get integer id in category_genre_list(%r)' % exlink)
        # mylist = self.mylist
        try:
            category = next(cat for cat in self.category_tree if cat['id'] == cid)
        except StopIteration:
            raise ValueError('cennot find category in category_genre_list(%r)' % exlink)
        genres = category['genres']
        if len(genres) > 1:
            genres.append({'id': '', 'name': '[B]Wszystkie[/B]', '_props_': {'SpecialSort': 'top'}})
        for item in genres:
            xbmc.log('PLAYER.PL: XXXXXXX %s: %r' % (type(item), item), xbmc.LOGWARNING)
            name = item['name']
            url = '%s:%s' % (item['id'], slug)
            # if self.skip_unaviable:
            #     xbmc.log('PLAYER.PL: ul=%s, mylist=%s, slg=%s, start counting' % (urlk, len(mylist), len(slugs[urlk])), xbmc.LOGWARNING)
            #     # count = sum(item['id'] in mylist for item in slugs[urlk])
            #     count = len({item['id'] for item in slugs[urlk]} & mylist)
            #     xbmc.log('PLAYER.PL: ul=%s, mylist=%s, slg=%s, cnt=%s' % (urlk, len(mylist), len(slugs[urlk]), count), xbmc.LOGWARNING)
            #     fmt = '{name} ({count})' if count else '{name} ([COLOR red]brak[/COLOR])'
            #     name = fmt.format(name=name, count=count)
            # image = media('genre/%s.png' % item['id'], fallback=ADDON_ICON)
            add_item(url, name, image=None, mode='listcategContent', folder=True, isPlayable=False,
                     properties=item.get('_props_'), fallback_image=None)
        setView('tvshows')
        xbmcplugin.addSortMethod(addon_handle, sortMethod=xbmcplugin.SORT_METHOD_TITLE,
                                 label2Mask="%R, %Y, %P")
        xbmcplugin.endOfDirectory(addon_handle, succeeded=True, cacheToDisc=False)
        xbmc.log('PLAYER.PL: ZZZZZZZ handle=%r, args=%r' % (addon_handle, sys.argv), xbmc.LOGWARNING)


if __name__ == '__main__':

    mode = params.get('mode', None)
    name = params.get('name')
    xbmc.log('PLAYER.PL: ENTER: mode=%r, name=%r, exlink=%r' % (mode, name, exlink),
             xbmc.LOGWARNING)

    if not mode:
        home()
        setView('tvshows')
        # xbmcplugin.setContent(addon_handle, 'tvshows')
        xbmcplugin.endOfDirectory(addon_handle)

    elif mode == "content":
        PLAYERPL().content()

    elif mode == "listcateg":
        PLAYERPL().listCateg(exlink)

    elif mode == "listcategContent":
        PLAYERPL().listCategContent(exlink)

    elif mode == "listcategSerial":
        PLAYERPL().listCategSerial(exlink)
    elif mode == "listEpizody":
        PLAYERPL().listEpizody(exlink)

    elif mode == 'search.it':
        query = exlink
        if query:
            PLAYERPL().listSearch(query)

    elif mode == 'search':
        add_item('', '[COLOR khaki][B]Nowe szukanie[/B][/COLOR]', image=None, mode='search.new',
                 folder=True)
        for entry in historyLoad():
            if entry:
                contextmenu = [
                    (u'Usuń', 'Container.Update(%s)'
                     % build_url({'mode': 'search.remove', 'url': entry})),
                    (u'Usuń całą historię', 'Container.Update(%s)'
                     % build_url({'mode': 'search.remove_all'})),
                ]
                add_item(entry, entry, image=None, mode='search.it', contextmenu=contextmenu,
                         folder=True)
        xbmcplugin.endOfDirectory(addon_handle, succeeded=True, cacheToDisc=False)

    elif mode == 'search.new':
        query = xbmcgui.Dialog().input(u'Szukaj, podaj tytuł filmu', type=xbmcgui.INPUT_ALPHANUM)
        if query:
            historyAdd(query)
            try:
                PLAYERPL().listSearch(query)
            except Exception:
                addon_data.save(indent=2)  # save new search even if exception raised
                raise
    elif mode == 'search.remove':
        historyDel(exlink)
        xbmc.executebuiltin('Container.Refresh(%s)' % build_url({'mode': 'search'}))
        xbmcplugin.endOfDirectory(addon_handle, succeeded=True, cacheToDisc=False)

    elif mode == 'search.remove_all':
        historyClear()
        xbmc.executebuiltin('Container.Refresh(%s)' % build_url({'mode': 'search'}))
        xbmcplugin.endOfDirectory(addon_handle, succeeded=True, cacheToDisc=False)

    elif mode == 'favors':
        PLAYERPL().listFavorites()
    elif mode == "collect":
        PLAYERPL().listCollection()

    elif mode == "listcollectContent":
        PLAYERPL().listCollectContent(exlink)

    elif mode=='playvid':
        PLAYERPL().playvid(exlink)

    elif mode=='login':

        set_setting('logged', 'true')
        PLAYERPL().LOGGED = addon.getSetting('logged')
        xbmc.executebuiltin('Container.Refresh()')

    elif mode=='opcje':
        addon.openSettings()


    elif mode=='logout':

        yes = xbmcgui.Dialog().yesno("[COLOR orange]Uwaga[/COLOR]", 'Wylogowanie spowoduje konieczność ponownego wpisania kodu na stronie.[CR]Jesteś pewien?',yeslabel='TAK', nolabel='NIE')
        if yes:
            set_setting('refresh_token', '')
            set_setting('logged', 'false')
            PLAYERPL().REFRESH_TOKEN = addon.getSetting('refresh_token')
            PLAYERPL().LOGGED = addon.getSetting('logged')
            xbmc.executebuiltin('Container.Refresh()')

    else:
        # auto bind
        playerpl = PLAYERPL()
        if hasattr(playerpl, mode):
            getattr(playerpl, mode)(exlink)

addon_data.save(indent=2)
