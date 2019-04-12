# -*- coding: utf-8 -*-

import sys
import os
import re
import xbmc
import xbmcgui
import xbmcplugin
import xbmcaddon

PY2 = sys.version_info[0] == 2
PY3 = sys.version_info[0] == 3
if PY2:
    from urllib import quote, unquote, quote_plus, unquote_plus, urlencode  # Python 2.X
    from urllib2 import build_opener, HTTPCookieProcessor, Request, urlopen  # Python 2.X
    from cookielib import LWPCookieJar  # Python 2.X
    from urlparse import urljoin, urlparse, urlunparse  # Python 2.X

    bytes = str
elif PY3:
    from urllib.parse import quote, unquote, quote_plus, unquote_plus, urlencode, urljoin, urlparse, urlunparse  # Python 3+
    from urllib.request import build_opener, HTTPCookieProcessor, Request, urlopen  # Python 3+
    from http.cookiejar import LWPCookieJar  # Python 3+

    bytes = bytes
from operator import itemgetter
import json
import xbmcvfs
import random
import socket
import datetime
import time
import io
import gzip
import ssl

try:
    _create_unverified_https_context = ssl._create_unverified_context
except AttributeError:
    pass
else:
    ssl._create_default_https_context = _create_unverified_https_context

pluginhandle = int(sys.argv[1])
addon = xbmcaddon.Addon()
socket.setdefaulttimeout(40)
addonPath = xbmc.translatePath(addon.getAddonInfo('path')).encode('utf-8').decode('utf-8')
dataPath = xbmc.translatePath(addon.getAddonInfo('profile')).encode('utf-8').decode('utf-8')
region = xbmc.getLanguage(xbmc.ISO_639_1, region=True).split("-")[1]
icon = os.path.join(addonPath, 'icon.png').encode('utf-8').decode('utf-8')
defaultFanart = os.path.join(addonPath, 'fanart.jpg').encode('utf-8').decode('utf-8')
pic = os.path.join(addonPath, 'resources/media/').encode('utf-8').decode('utf-8')
blackList = addon.getSetting("blacklist").split(',')
infoEnabled = addon.getSetting("showInfo") == "true"
infoType = addon.getSetting("infoType")
infoDelay = int(addon.getSetting("infoDelay"))
infoDuration = int(addon.getSetting("infoDuration"))
useThumbAsFanart = addon.getSetting("useThumbAsFanart") == 'true'
cachePath = xbmc.translatePath(os.path.join(addon.getSetting("cacheDir")))
cacheDays = int(addon.getSetting("cacheLong"))
forceView = addon.getSetting("forceView") == 'true'
viewIDGenres = str(addon.getSetting("viewIDGenres"))
viewIDPlaylists = str(addon.getSetting("viewIDPlaylists"))
viewIDVideos = str(addon.getSetting("viewIDVideos"))
urlBaseBP = "https://www.beatport.com"
#REtoken2 = "AIzaSyAdORXg7UZUo7sePv97JyoDqtQVi3Ll0b8"
#REtoken3 = "AIzaSyDDxfHuYTdjwAUnFPeFUgqGvJM8qqLpdGc"
token = "AIzaSyCIM4EzNqi1in22f4Z3Ru3iYvLaY8tc3bo"
xbmcplugin.setContent(int(sys.argv[1]), 'musicvideos')

if cachePath == "":
    addon.setSetting(id='cacheDir', value='special://profile/addon_data/' + addon.getAddonInfo('id') + '/cache')
elif cachePath != "" and not os.path.isdir(cachePath) and not cachePath.startswith(('smb://', 'nfs://', 'upnp://', 'ftp://')):
    os.mkdir(cachePath)
elif cachePath != "" and not os.path.isdir(cachePath) and cachePath.startswith(('smb://', 'nfs://', 'upnp://', 'ftp://')):
    addon.setSetting(id='cacheDir', value='special://profile/addon_data/' + addon.getAddonInfo('id') + '/cache') and os.mkdir(cachePath)
elif cachePath != "" and os.path.isdir(cachePath):
    xDays = cacheDays  # Days after which Files would be deleted
    now = time.time()  # Date and time now
    for root, dirs, files in os.walk(cachePath):
        for name in files:
            filename = os.path.join(root, name).encode('utf-8').decode('utf-8')
            try:
                if os.path.exists(filename):
                    if os.path.getmtime(filename) < now - (60 * 60 * 24 * xDays):  # Check if CACHE-File exists and remove CACHE-File after defined xDays
                        os.unlink(filename)
            except:
                pass


def py2_enc(s, encoding='utf-8'):
    if PY2 and isinstance(s, unicode):
        s = s.encode(encoding)
    return s


def py2_uni(s, encoding='utf-8'):
    if PY2 and isinstance(s, str):
        s = unicode(s, encoding)
    return s


def py3_dec(d, encoding='utf-8'):
    if PY3 and isinstance(d, bytes):
        d = d.decode(encoding)
    return d


def TitleCase(s):
    return re.sub(r"[A-Za-z]+('[A-Za-z]+)?", lambda mo: mo.group(0)[0].upper() + mo.group(0)[1:].lower(), s)


def translation(id):
    LANGUAGE = addon.getLocalizedString(id)
    LANGUAGE = py2_enc(LANGUAGE)
    return LANGUAGE


def failing(content):
    log(content, xbmc.LOGERROR)


def debug(content):
    log(content, xbmc.LOGDEBUG)


def log(msg, level=xbmc.LOGNOTICE):
    msg = py2_enc(msg)
    xbmc.log("[" + addon.getAddonInfo('id') + "-" + addon.getAddonInfo('version') + "]" + msg, level)


def index():
    addDir(translation(30601), "", "beatportMain", pic + 'beatport.png')
    xbmcplugin.endOfDirectory(pluginhandle)


def beatportMain():
    content = cache('https://pro.beatport.com', 30)
    content = content[content.find('<div class="mobile-menu-body">') + 1:]
    content = content[:content.find('<!-- End Mobile Touch Menu -->')]
    match = re.compile('<a href="(.*?)" class="(.*?)" data-name=".+?">(.*?)</a>', re.DOTALL).findall(content)
    allTitle = translation(30635)
    addAutoPlayDir(allTitle, urlBaseBP + "", "", pic + 'beatport.png', "", "browse")
    for genreURL, genreTYPE, genreTITLE in match:
        topUrl = urlBaseBP + genreURL + '/top-100'
        title = cleanTitle(genreTITLE).replace('Electronica / Downtempo', 'Electronica').replace('Breaks', 'Breakbeat').replace('Hardcore / Hard Techno', 'Hard Techno ').replace('Hip-Hop / R&B','Rap').replace('Melodic House & Techno', 'Melodic Tech').replace('Minimal / Deep Tech', 'Minimal').replace('Trap / Future Bass', 'Trap').replace('Hard Dance', 'Hardcore').replace('Indie Dance / Nu Disco', 'Indie Dance').replace('Psy-Trance', 'Psy Trance')
        if any(['big room' in title.lower(), 'dj tools' in title.lower(), 'funk' in title.lower(), 'garage' in title.lower(), 'leftfield' in title.lower(), 'dancehall' in title.lower()]):
            continue
        addAutoPlayDir(title, topUrl, "listBeatportVideos", pic + 'beatport.png', "", "browse")
    xbmcplugin.endOfDirectory(pluginhandle)
    if forceView:
        xbmc.executebuiltin('Container.SetViewMode(' + viewIDGenres + ')')


def listBeatportVideos(type, url, limit):
    musicVideos = []
    count = 0
    if type == "play":
        playlist = xbmc.PlayList(1)
        playlist.clear()
    content = cache(url, 1)
    spl = content.split('bucket-item ec-item track')
    for i in range(1, len(spl), 1):
        entry = spl[i]
        artist = re.compile('data-artist=".+?">(.*?)</a>', re.DOTALL).findall(entry)[0]
        artist = cleanTitle(artist)
        song = re.compile('<span class="buk-track-primary-title" title=".+?">(.*?)</span>', re.DOTALL).findall(entry)[0]
        remix = re.compile('<span class="buk-track-remixed">(.*?)</span>', re.DOTALL).findall(entry)
        if "(original mix)" in song.lower():
            song = song.lower().split('(original mix)')[0]
        song = cleanTitle(song)
        if "(feat." in song.lower() and " feat." in song.lower():
            song = song.split(')')[0] + ')'
        elif not "(feat." in song.lower() and " feat." in song.lower():
            firstSong = song.lower().split(' feat.')[0]
            secondSong = song.lower().split(' feat.')[1]
            song = firstSong + ' (feat.' + secondSong + ')'
        if remix and not "original" in remix[0].lower():
            newRemix = remix[0].replace('[', '').replace(']', '')
            song += ' [' + cleanTitle(newRemix) + ']'
        firstTitle = artist + " - " + song
        try:
            oldDate = re.compile('<p class="buk-track-released">(.*?)</p>', re.DOTALL).findall(entry)[0]
            convert = time.strptime(oldDate, '%Y-%m-%d')
            newDate = time.strftime('%d.%m.%Y', convert)
            completeTitle = firstTitle + '   [COLOR deepskyblue][' + str(newDate) + '][/COLOR]'
        except:
            completeTitle = firstTitle
        try:
            thumb = re.compile('data-src="(http.*?.jpg)"', re.DOTALL).findall(entry)[0]
            thumb = thumb.split('image_size')[0] + 'image/' + thumb.split('/')[-1]
        # thumb = thumb.replace("/30x30/","/500x500/").replace("/60x60/","/500x500/").replace("/95x95/","/500x500/").replace("/250x250/","/500x500/")
        except:
            thumb = pic + 'noimage.png'
        filtered = False
        for snippet in blackList:
            if snippet.strip().lower() and snippet.strip().lower() in firstTitle.lower():
                filtered = True
        if filtered:
            continue
        if type == "play":
            url = "plugin://" + addon.getAddonInfo('id') + "/?url=" + quote_plus(firstTitle.replace(" - ", " ")) + "&mode=playYTByTitle"
        else:
            url = firstTitle
        musicVideos.append([firstTitle, completeTitle, url, thumb])
    if type == "browse":
        for firstTitle, completeTitle, url, thumb in musicVideos:
            count += 1
            name = '[COLOR chartreuse]' + str(count) + ' •  [/COLOR]' + completeTitle
            addLink(name, url.replace(" - ", " "), "playYTByTitle", thumb)
        xbmcplugin.endOfDirectory(pluginhandle)
        if forceView:
            xbmc.executebuiltin('Container.SetViewMode(' + viewIDVideos + ')')
    else:
        if limit:
            musicVideos = musicVideos[:int(limit)]
        random.shuffle(musicVideos)
        for firstTitle, completeTitle, url, thumb in musicVideos:
            listitem = xbmcgui.ListItem(firstTitle, thumbnailImage=thumb)
            playlist.add(url, listitem)
        xbmc.Player().play(playlist)


def getHTML(url, headers=False, referer=False):
    req = Request(url)
    if headers:
        for key in headers:
            req.add_header(key, headers[key])
    else:
        req.add_header('User-Agent', 'Mozilla/5.0 (Windows NT 10.0; WOW64; rv:55.0) Gecko/20100101 Firefox/55.0')
        req.add_header('Accept-Encoding', 'gzip, deflate')
    if referer:
        req.add_header('Referer', referer)
    response = urlopen(req, timeout=30)
    if response.info().get('Content-Encoding') == 'gzip':
        link = py3_dec(gzip.GzipFile(fileobj=io.BytesIO(response.read())).read())
    else:
        link = py3_dec(response.read())
    response.close()
    return link

def cache(url, duration=0):
    cacheFile = os.path.join(cachePath, (''.join(c for c in py2_uni(url) if c not in '/\\:?"*|<>')).strip())
    if len(cacheFile) > 255:
        cacheFile = cacheFile.replace("part=snippet&type=video&maxResults=5&order=relevance&q", "")
        cacheFile = cacheFile[:255]
    if os.path.exists(cacheFile) and duration != 0 and os.path.getmtime(cacheFile) < time.time() - (60 * 60 * 24 * duration):
        fh = xbmcvfs.File(cacheFile, 'r')
        content = fh.read()
        fh.close()
    else:
        content = getHTML(url)
        fh = xbmcvfs.File(cacheFile, 'w')
        fh.write(content)
        fh.close()
    return content


def getYoutubeId(title):
    title = quote_plus(title.lower()).replace('%5B', '').replace('%5D', '').replace('%28', '').replace('%29', '')
    videoBest = False
    movieID = []
    content = cache("https://www.googleapis.com/youtube/v3/search?part=snippet&type=video&maxResults=5&order=relevance&q=%s&key=%s" % (title, token), 1)
    response = json.loads(content)
    for videoTrack in response.get('items', []):
        if videoTrack['id']['kind'] == "youtube#video":
            movieID.append('%s @@@ %s' % (videoTrack['snippet']['title'], videoTrack['id']['videoId']))
    if len(movieID) > 0:
        for videoTrack in movieID:
            best = movieID[:]
            if not 'audio' in best[0].strip().lower():
                VIDEOexAUDIO = best[0].split('@@@ ')[1].strip()
            elif not 'audio' in best[1].strip().lower():
                VIDEOexAUDIO = best[1].split('@@@ ')[1].strip()
            elif not 'audio' in best[2].strip().lower():
                VIDEOexAUDIO = best[2].split('@@@ ')[1].strip()
            else:
                VIDEOexAUDIO = best[0].split('@@@ ')[1].strip()
        videoBest = VIDEOexAUDIO
    else:
        xbmcgui.Dialog().notification('Youtube Music : [COLOR red]!!! URL - ERROR !!![/COLOR]', 'ERROR = [COLOR red]No *SingleEntry* found on YOUTUBE ![/COLOR]', icon, 6000)
    return videoBest


def playYTByTitle(title):
    try:
        youtubeID = getYoutubeId('official ' + title)
        finalURL = 'plugin://plugin.video.youtube/play/?video_id=' + youtubeID
        xbmcplugin.setResolvedUrl(pluginhandle, True, xbmcgui.ListItem(path=finalURL))
        xbmc.sleep(1000)
        if infoEnabled and not xbmc.abortRequested:
            showInfo()
    except:
        pass


def showInfo():
    count = 0
    while not xbmc.Player().isPlaying():
        xbmc.sleep(200)
        if count == 50:
            break
        count += 1
    xbmc.sleep(infoDelay * 1000)
    if xbmc.Player().isPlaying() and infoType == "0":
        xbmc.sleep(1500)
        xbmc.executebuiltin('ActivateWindow(12901)')
        xbmc.sleep(infoDuration * 1000)
        xbmc.executebuiltin('ActivateWindow(12005)')
        xbmc.sleep(500)
        xbmc.executebuiltin('Action(Back)')
    elif xbmc.Player().isPlaying() and infoType == "1":
        TOP = translation(30806)
        xbmc.getInfoLabel('Player.Title')
        xbmc.getInfoLabel('Player.Duration')
        xbmc.getInfoLabel('Player.Art(thumb)')
        xbmc.sleep(500)
        title = xbmc.getInfoLabel('Player.Title')
        relTitle = cleanTitle(title)
        if relTitle.isupper() or relTitle.islower():
            relTitle = TitleCase(relTitle)
        runTime = xbmc.getInfoLabel('Player.Duration')
        photo = xbmc.getInfoLabel('Player.Art(thumb)')
        xbmc.sleep(1000)
        xbmcgui.Dialog().notification(TOP, relTitle + "[COLOR blue]  * " + runTime + " *[/COLOR]", photo, infoDuration * 1000)
    else:
        pass


def cleanTitle(title):
    title = py2_enc(title)
    title = title.replace("&lt;", "<").replace("&gt;", ">").replace("&amp;", "&").replace("&Amp;", "&").replace("&#34;", "”").replace("&#39;", "'").replace("&#039;", "'").replace("&quot;", "\"").replace("&Quot;", "\"").replace("&szlig;", "ß").replace("&mdash;", "-").replace("&ndash;", "-").replace('–', '-')
    title = title.replace("&#x00c4", "Ä").replace("&#x00e4", "ä").replace("&#x00d6", "Ö").replace("&#x00f6", "ö").replace("&#x00dc", "Ü").replace("&#x00fc", "ü").replace("&#x00df", "ß")
    title = title.replace("&Auml;", "Ä").replace("&auml;", "ä").replace("&Euml;", "Ë").replace("&euml;", "ë").replace("&Iuml;", "Ï").replace("&iuml;", "ï").replace("&Ouml;", "Ö").replace("&ouml;", "ö").replace("&Uuml;", "Ü").replace("&uuml;", "ü").replace("&#376;", "Ÿ").replace("&yuml;", "ÿ")
    title = title.replace("&agrave;", "à").replace("&Agrave;", "À").replace("&aacute;", "á").replace("&Aacute;", "Á").replace("&egrave;", "è").replace("&Egrave;", "È").replace("&eacute;", "é").replace("&Eacute;", "É").replace("&igrave;", "ì").replace("&Igrave;", "Ì").replace("&iacute;", "í").replace("&Iacute;", "Í")
    title = title.replace("&ograve;", "ò").replace("&Ograve;", "Ò").replace("&oacute;", "ó").replace("&Oacute;", "ó").replace("&ugrave;", "ù").replace("&Ugrave;", "Ù").replace("&uacute;", "ú").replace("&Uacute;", "Ú").replace("&yacute;", "ý").replace("&Yacute;", "Ý")
    title = title.replace("&atilde;", "ã").replace("&Atilde;", "Ã").replace("&ntilde;", "ñ").replace("&Ntilde;", "Ñ").replace("&otilde;", "õ").replace("&Otilde;", "Õ").replace("&Scaron;", "Š").replace("&scaron;", "š")
    title = title.replace("&acirc;", "â").replace("&Acirc;", "Â").replace("&ccedil;", "ç").replace("&Ccedil;", "Ç").replace("&ecirc;", "ê").replace("&Ecirc;", "Ê").replace("&icirc;", "î").replace("&Icirc;", "Î").replace("&ocirc;", "ô").replace("&Ocirc;", "Ô").replace("&ucirc;", "û").replace("&Ucirc;", "Û")
    title = title.replace("&alpha;", "a").replace("&Alpha;", "A").replace("&aring;", "å").replace("&Aring;", "Å").replace("&aelig;", "æ").replace("&AElig;", "Æ").replace("&epsilon;", "e").replace("&Epsilon;", "Ε").replace("&eth;", "ð").replace("&ETH;", "Ð").replace("&gamma;", "g").replace("&Gamma;", "G")
    title = title.replace("&oslash;", "ø").replace("&Oslash;", "Ø").replace("&theta;", "θ").replace("&thorn;", "þ").replace("&THORN;", "Þ")
    title = title.replace("\\'", "'").replace("&x27;", "'").replace("&bull;", "•").replace("&iexcl;", "¡").replace("&iquest;", "¿").replace("&rsquo;", "’").replace("&lsquo;", "‘").replace("&sbquo;", "’").replace("&rdquo;", "”").replace("&ldquo;", "“").replace("&bdquo;", "”").replace("&rsaquo;", "›").replace("lsaquo;", "‹").replace("&raquo;", "»").replace("&laquo;", "«")
    title = title.replace(" ft ", " feat. ").replace(" FT ", " feat. ").replace(" Ft ", " feat. ").replace("Ft.", "feat.").replace("ft.", "feat.").replace(" FEAT ", " feat. ").replace(" Feat ", " feat. ").replace("Feat.", "feat.").replace("Featuring", "feat.").replace("&copy;", "©").replace("&reg;", "®").replace("™", "")
    title = title.strip()
    return title


def parameters_string_to_dict(parameters):
    paramDict = {}
    if parameters:
        paramPairs = parameters[1:].split("&")
        for paramsPair in paramPairs:
            paramSplits = paramsPair.split('=')
            if (len(paramSplits)) == 2:
                paramDict[paramSplits[0]] = paramSplits[1]
    return paramDict


def addVideoList(url, name, image):
    PL = xbmc.PlayList(1)
    listitem = xbmcgui.ListItem(name, thumbnailImage=image)
    if useThumbAsFanart:
        listitem.setArt({'fanart': defaultFanart})
    listitem.setProperty('IsPlayable', 'true')
    listitem.setContentLookup(False)
    PL.add(url, listitem)


def addLink(name, url, mode, image, plot=None):
    u = sys.argv[0] + "?url=" + quote_plus(url) + "&mode=" + str(mode)
    liz = xbmcgui.ListItem(name, iconImage="DefaultAudio.png", thumbnailImage=image)
    liz.setInfo(type="Video", infoLabels={"Title": name, "Plot": plot, 'mediatype': 'video'})
    if useThumbAsFanart:
        liz.setArt({'fanart': defaultFanart})
    liz.setProperty('IsPlayable', 'true')
    liz.addContextMenuItems([(translation(30807), 'RunPlugin(plugin://{0}/?mode=addVideoList&url={1}&name={2}&image={3})'.format(addon.getAddonInfo('id'), quote_plus(u), quote_plus(name), quote_plus(image)))])
    return xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]), url=u, listitem=liz)


def addDir(name, url, mode, image, plot=None):
    u = sys.argv[0] + "?url=" + quote_plus(url) + "&mode=" + str(mode)
    liz = xbmcgui.ListItem(name, iconImage="DefaultMusicVideos.png", thumbnailImage=image)
    liz.setInfo(type="Video", infoLabels={"Title": name, "Plot": plot})
    if useThumbAsFanart:
        liz.setArt({'fanart': defaultFanart})
    return xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]), url=u, listitem=liz, isFolder=True)


def addAutoPlayDir(name, url, mode, image, plot=None, type=None, limit=None):
    u = sys.argv[0] + "?url=" + quote_plus(url) + "&mode=" + str(mode) + "&type=" + str(type) + "&limit=" + str(limit) + '&image=' + quote_plus(image)
    liz = xbmcgui.ListItem(name, iconImage="DefaultMusicVideos.png", thumbnailImage=image)
    liz.setInfo(type="Video", infoLabels={"Title": name, "Plot": plot, 'mediatype': 'video'})
    if useThumbAsFanart:
        liz.setArt({'fanart': defaultFanart})
    entries = []
    entries.append((translation(30831), 'RunPlugin(plugin://' + addon.getAddonInfo('id') + '/?mode=' + str(mode) + '&url=' + quote_plus(url) + '&type=play&limit=)'))
    entries.append((translation(30832), 'RunPlugin(plugin://' + addon.getAddonInfo('id') + '/?mode=' + str(mode) + '&url=' + quote_plus(url) + '&type=play&limit=10)'))
    entries.append((translation(30833), 'RunPlugin(plugin://' + addon.getAddonInfo('id') + '/?mode=' + str(mode) + '&url=' + quote_plus(url) + '&type=play&limit=20)'))
    entries.append((translation(30834), 'RunPlugin(plugin://' + addon.getAddonInfo('id') + '/?mode=' + str(mode) + '&url=' + quote_plus(url) + '&type=play&limit=30)'))
    entries.append((translation(30835), 'RunPlugin(plugin://' + addon.getAddonInfo('id') + '/?mode=' + str(mode) + '&url=' + quote_plus(url) + '&type=play&limit=40)'))
    entries.append((translation(30836), 'RunPlugin(plugin://' + addon.getAddonInfo('id') + '/?mode=' + str(mode) + '&url=' + quote_plus(url) + '&type=play&limit=50)'))
    liz.addContextMenuItems(entries, replaceItems=False)
    return xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]), url=u, listitem=liz, isFolder=True)


params = parameters_string_to_dict(sys.argv[2])
name = unquote_plus(params.get('name', ''))
url = unquote_plus(params.get('url', ''))
mode = unquote_plus(params.get('mode', ''))
image = unquote_plus(params.get('image', ''))
type = unquote_plus(params.get('type', ''))
limit = unquote_plus(params.get('limit', ''))
referer = unquote_plus(params.get('referer', ''))


if mode == 'beatportMain' or mode == '':
    beatportMain()
elif mode == 'listBeatportVideos':
    listBeatportVideos(type, url, limit)
elif mode == 'playYTByTitle':
    playYTByTitle(url)
elif mode == 'addVideoList':
    addVideoList(url, name, image)
else:
    index()

