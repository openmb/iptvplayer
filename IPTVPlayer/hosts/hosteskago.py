# -*- coding: utf-8 -*-
###################################################
# LOCAL import
###################################################
from Plugins.Extensions.IPTVPlayer.components.iptvplayerinit import TranslateTXT as _, SetIPTVPlayerLastHostError
from Plugins.Extensions.IPTVPlayer.components.ihost import CHostBase, CBaseHostClass, CDisplayListItem, ArticleContent, RetHost, CUrlItem
from Plugins.Extensions.IPTVPlayer.tools.iptvtools import CSelOneLink, printDBG, printExc, CSearchHistoryHelper, GetLogoDir, GetCookieDir, byteify
from Plugins.Extensions.IPTVPlayer.libs.urlparserhelper import getDirectM3U8Playlist
from Plugins.Extensions.IPTVPlayer.libs.urlparser import urlparser
from Plugins.Extensions.IPTVPlayer.libs.youtube_dl.utils import clean_html
from Plugins.Extensions.IPTVPlayer.libs.crypto.hash.sha1Hash import SHA1
###################################################

###################################################
# FOREIGN import
###################################################
from Components.config import config, ConfigInteger, ConfigSelection, ConfigYesNo, ConfigText, getConfigListEntry
from datetime import timedelta
from binascii import hexlify
import re
import urllib
import time
import random
try:    import simplejson as json
except Exception: import json
###################################################


###################################################
# E2 GUI COMMPONENTS 
###################################################
from Plugins.Extensions.IPTVPlayer.components.asynccall import MainSessionWrapper
from Screens.MessageBox import MessageBox
###################################################

###################################################
# Config options for HOST
###################################################


def GetConfigList():
    optionList = []
    return optionList
###################################################

def gettytul():
    return 'eskaGO'

class EskaGo(CBaseHostClass):
    # CHANNELS_URL and MAINURL_VOD taken from http://svn.sd-xbmc.org/filedetails.php?repname=sd-xbmc&path=%2Ftrunk%2Fxbmc-addons%2Fsrc%2Fplugin.video.polishtv.live%2Fhosts%2Feskago.py
    CHANNELS_URL =  'http://www.eskago.pl/indexajax.php?action=SamsungSmartTvV1&start=channelsGroups'
    
    def __init__(self):
        printDBG("EskaGo.__init__")
        CBaseHostClass.__init__(self, {'history':'eskaGO.pl'})
        self.cacheChannels = None
            
    def _fillChannelsCache(self, url):
        printDBG("EskaGo._fillChannelsCache")
        sts, data = self.cm.getPage(url)
        if not sts: return
        try:
            data = byteify( json.loads(data) )
            self.cacheChannels = data
        except Exception:
            printExc()
            
    def listChannels(self, cItem):
        printDBG("EskaGo.listChannels")
        sts, data = self.cm.getPage(cItem['url'])
        if not sts: return
        keysTab = cItem.get('channels_keys_tab', [])
        if 0 == len(keysTab):
            self._fillChannelsCache(cItem['url'])
            keysTab = [{'key':'result', 'meta_data':{}}]
        
        data = self.cacheChannels
        for item in keysTab:
            try:
                data = data[item['key']]
                meta_data = item['meta_data']
            except Exception:
                printExc()
                return
        idx = 0
        for item in data:
            newKeysTab = list(keysTab)
            newKeysTab.append({'key':idx, 'meta_data':{}})
                
            if 'channels' in item:
                title = item.get('title', '').replace("Kanały w klimacie ", '')
                icon  = item.get('image', '')
                newKeysTab.append({'key':'channels', 'meta_data':{}})
                
                params = dict(cItem)
                params.update({'title':title, 'icon':icon, 'channels_keys_tab':newKeysTab})
                self.addDir(params)
            elif 'subChannels' in item:
                title = item.get('name', '')
                newKeysTab.append({'key':'subChannels', 'meta_data':{'type':item.get('type', '')}})
                
                params = dict(cItem)
                params.update({'title':title, 'channels_keys_tab':newKeysTab})
                self.addDir(params)
            elif 'streamUrl' in item:
                title = item.get('name', '')
                if '' == title: title = item.get('subname', '')
                
                type = item.get('type', '')
                if '' == type: type = meta_data.get('type', '')
                
                tmpUrls = []
                if 'streamUrls' in item:
                    streamUrlHD = item['streamUrls'].get('hd', '').strip()
                    streamUrlSD = item['streamUrls'].get('sd', '').strip()
                    if streamUrlHD != '': tmpUrls.append({'name':'HD', 'url':streamUrlHD})
                    if streamUrlSD != '': tmpUrls.append({'name':'SD', 'url':streamUrlSD}) 
                else:
                    streamUrl  = item.get('streamUrl', '')
                    if None == streamUrl: streamUrl = ''
                    else: streamUrl = streamUrl.strip()
                    if streamUrl != '': tmpUrls.append({'name':'Normal', 'url':streamUrl}) 
                
                if len(tmpUrls):
                    params = dict(cItem)
                    params.update( {'title':title, 'urls':tmpUrls} )
                    if type == 'Radio':
                        self.addAudio(params)
                    else:
                        self.addVideo(params)
            idx += 1

    def getLinksForVideo(self, cItem):
        printDBG("EskaGo.getLinksForVideo [%s]" % cItem)
        duplicates = []
        urlTab = []
        for urlItem in cItem.get('urls', []):
            url = urlItem['url']
            if url.split('?')[0].endswith('m3u8'):
                streamUri = self.cm.ph.getSearchGroups(url, '/tv/([^/]+?/[^/]+?)/')[0]
                if streamUri != '':
                    urlItem = {'name': streamUri.split('_')[-1], 'url':streamUri, 'need_resolve':1}
                    urlTab.append(urlItem)
                
                #data = getDirectM3U8Playlist(url, checkExt=False)
                #for item in data:
                #    item['url'] = urlparser.decorateUrl(item['url'], {'iptv_proto':'m3u8', 'iptv_livestream':True})
                #    urlTab.append(item)
            else:
                urlTab.append(urlItem)
        return urlTab
        
    def getVideoLinks(self, videoUrl):
        printDBG("T123MoviesTO.getVideoLinks [%s]" % videoUrl)
        urlTab = []
        
        streamUri = videoUrl.replace('/', '-t/')
        sts, videoUrl = self.cm.getPage('https://api.stream.smcdn.pl/api/secureToken.php', post_data={'streamUri':streamUri})
        if not sts: return []
        
        printDBG('++++++++++++++++++++++++++')
        printDBG(videoUrl)
        printDBG('++++++++++++++++++++++++++')
        
        if self.cm.isValidUrl(videoUrl) and videoUrl.split('?')[0].endswith('m3u8'):
            data = getDirectM3U8Playlist(videoUrl, checkExt=False)
            for item in data:
                item['url'] = urlparser.decorateUrl(item['url'], {'iptv_proto':'m3u8', 'iptv_livestream':True})
                urlTab.append(item)
        
        return urlTab
        
    def handleService(self, index, refresh=0, searchPattern='', searchType=''):
        printDBG('EskaGo.handleService start')
        CBaseHostClass.handleService(self, index, refresh, searchPattern, searchType)
        name     = self.currItem.get("name", None)
        category = self.currItem.get("category", '')
        printDBG( "EskaGo.handleService: ---------> name[%s], category[%s] " % (name, category) )
        searchPattern = self.currItem.get("search_pattern", searchPattern)
        self.currList = [] 

        if None == name:
            self.listChannels({'name':'category', 'url':EskaGo.CHANNELS_URL})
        else:
            self.listChannels(self.currItem)
        CBaseHostClass.endHandleService(self, index, refresh)

class IPTVHost(CHostBase):

    def __init__(self):
        CHostBase.__init__(self, EskaGo(), True)

    def getLogoPath(self):
        return RetHost(RetHost.OK, value = [GetLogoDir('eskagologo.png')])

