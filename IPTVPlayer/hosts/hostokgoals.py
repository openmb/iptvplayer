# -*- coding: utf-8 -*-
###################################################
# LOCAL import
###################################################
from Plugins.Extensions.IPTVPlayer.components.iptvplayerinit import TranslateTXT as _, SetIPTVPlayerLastHostError
from Plugins.Extensions.IPTVPlayer.components.ihost import CHostBase, CBaseHostClass, CDisplayListItem, RetHost, CUrlItem, ArticleContent
from Plugins.Extensions.IPTVPlayer.tools.iptvtools import printDBG, printExc, GetLogoDir, GetCookieDir, byteify
from Plugins.Extensions.IPTVPlayer.tools.iptvtypes import strwithmeta
from Plugins.Extensions.IPTVPlayer.libs.urlparserhelper import getF4MLinksWithMeta, getDirectM3U8Playlist
###################################################

###################################################
# FOREIGN import
###################################################
import re
import urllib
import string
import base64
try:    import json
except Exception: import simplejson as json
from random import randint
from datetime import datetime
from time import sleep
from copy import deepcopy
from Components.config import config, ConfigSelection, ConfigYesNo, ConfigText, getConfigListEntry
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
    return 'http://okgoals.com/'

class OkGoals(CBaseHostClass):
 
    def __init__(self):
        CBaseHostClass.__init__(self, {'history':'OkGoals.tv', 'cookie':'filisertv.cookie'})
        
        self.HEADER = {'User-Agent': 'Mozilla/5.0', 'Accept': 'text/html'}
        self.AJAX_HEADER = dict(self.HEADER)
        self.AJAX_HEADER.update( {'X-Requested-With': 'XMLHttpRequest'} )
        self.defaultParams = {'header':self.HEADER, 'use_cookie': True, 'load_cookie': True, 'save_cookie': True, 'cookiefile': self.COOKIE_FILE}
        
        self.MAIN_URL = 'http://www.okgoals.com/'
        self.DEFAULT_ICON_URL = self.getFullUrl('/okgoals_logo.jpg')
        
        self.MAIN_CAT_TAB = [{'category':'list_items',        'title': _('Main'),       'url':self.getFullUrl('index.php') },
                             {'category':'list_categories',   'title': _('Categories'), 'url':self.getMainUrl()            },
                             {'category':'search',            'title': _('Search'),     'search_item':True,                },
                             {'category':'search_history',    'title': _('Search history'),                                },
                            ]
        
    def listCategories(self, cItem, nextCategory):
        printDBG("OkGoals.listCategories")
        
        sts, data = self.cm.getPage(cItem['url'])
        if not sts: return
        
        data = self.cm.ph.getDataBeetwenMarkers(data, '<ul id="mediamenu">', '</ul>')[1]
        data = self.cm.ph.getAllItemsBeetwenMarkers(data, '<li', '</li>', withMarkers=True)
        for item in data:
            url   = self.getFullUrl(self.cm.ph.getSearchGroups(item, '''href=['"]([^'^"]+?)['"]''')[0])
            if not self.cm.isValidUrl(url): continue
            icon  = self.getFullIconUrl(self.cm.ph.getSearchGroups(item, '''src=['"]([^'^"]+?)['"]''')[0])
            title = self.cleanHtmlStr(item)
            
            params = {'good_for_fav': True, 'category':nextCategory, 'title':title, 'url':url, 'icon':icon}
            self.addDir(params)
        
    def listItems(self, cItem, nextCategory):
        printDBG("OkGoals.listItems")
        
        page = cItem.get('page', 1)
        
        sts, data = self.cm.getPage(cItem['url'])
        if not sts: return
        
        nextPage = self.cm.ph.getDataBeetwenMarkers(data, '<div class="wpnavi">', '<div class="clear">')[1]
        nextPage = self.cm.ph.getSearchGroups(nextPage, '''<a[^>]+?href=["']([^'^"]+?)["'][^>]*?>\s*{0}\s*</a>'''.format(page+1))[0]
        
        data = self.cm.ph.getAllItemsBeetwenMarkers(data, '<div id="matchlistng">', '</a>', withMarkers=False)
        for item in data:
            url   = self.getFullUrl(self.cm.ph.getSearchGroups(item, '''href=['"]([^'^"]+?)['"]''')[0])
            icon  = self.getFullIconUrl(self.cm.ph.getSearchGroups(item, '''src=['"]([^'^"]+?)['"]''')[0])
            desc  = self.cleanHtmlStr(self.cm.ph.getSearchGroups(item, '''alt=['"]([^'^"]+?)['"]''')[0].replace('icon', ''))
            title = self.cleanHtmlStr(item)

            params = {'good_for_fav': True, 'category':nextCategory, 'title':title, 'url':url, 'icon':icon, 'desc':desc}
            self.addDir(params)
        
        if nextPage != '':
            params = dict(cItem)
            params.update({'title':_('Next page'), 'page':page + 1, 'url':self.getFullUrl(nextPage)})
            self.addDir(params)
            
    def exploreItem(self, cItem):
        printDBG("OkGoals.exploreItem")
        
        sts, data = self.cm.getPage(cItem['url'])
        if not sts: return
        
        tmp = self.cm.ph.getDataBeetwenMarkers(data, 'class="matchcontainer">', '<div align="center">', False)[1]
        tmp = tmp.split('</script>')
        for item in tmp:
            url = self.getFullUrl(self.cm.ph.getSearchGroups(item, '''['"]([^'^"]*?//config\.playwire\.com[^'^"]+?\.json)['"]''')[0])
            if not self.cm.isValidUrl(url): continue
            title = self.cleanHtmlStr(item)
            if title == '': title = cItem['title']
            params = {'good_for_fav': True, 'title':title, 'url':url}
            self.addVideo(params)
    
    def getLinksForVideo(self, cItem):
        printDBG("OkGoals.getLinksForVideo [%s]" % cItem)
        urlTab = []
        videoUrl = cItem['url']
        if 'playwire.com' in videoUrl:
            sts, data = self.cm.getPage(videoUrl)
            if not sts: return []
            try:
                data = byteify(json.loads(data))
                if 'content' in data:
                    url = data['content']['media']['f4m']
                else:
                    url = data['src']
                sts, data = self.cm.getPage(url)
                baseUrl = self.cm.ph.getDataBeetwenMarkers(data, '<baseURL>', '</baseURL>', False)[1].strip()
                data = self.cm.ph.getAllItemsBeetwenMarkers(data, '<media ', '>')
                for item in data:
                    url  = self.cm.ph.getSearchGroups(item, '''url=['"]([^'^"]+?)['"]''')[0]
                    height = self.cm.ph.getSearchGroups(item, '''height=['"]([^'^"]+?)['"]''')[0]
                    bitrate = self.cm.ph.getSearchGroups(item, '''bitrate=['"]([^'^"]+?)['"]''')[0]
                    name = '[%s] bitrate:%s height: %s' % (url.split('.')[-1], bitrate, height)
                    if not url.startswith('http'):
                        url = baseUrl + '/' + url
                    if url.startswith('http'):
                        if 'm3u8' in url:
                            hlsTab = getDirectM3U8Playlist(url)
                            for idx in range(len(hlsTab)):
                                hlsTab[idx]['name'] = '[hls] bitrate:%s height: %s' % (hlsTab[idx]['bitrate'], hlsTab[idx]['height'])
                            urlTab.extend(hlsTab)
                        else:
                            urlTab.append({'name':name, 'url':url})
            except Exception:
                printExc()
        elif videoUrl.startswith('http'):
            urlTab.extend(self.up.getVideoLinkExt(videoUrl))
        return urlTab

        
    def getVideoLinks(self, videoUrl):
        printDBG("OkGoals.getVideoLinks [%s]" % videoUrl)
        urlTab = []
        return urlTab
        
    def listSearchResult(self, cItem, searchPattern, searchType):
        printDBG("KissCartoonMe.listSearchResult cItem[%s], searchPattern[%s] searchType[%s]" % (cItem, searchPattern, searchType))
        cItem = dict(cItem)
        url = self.getFullUrl('search.php?dosearch=yes&search_in_archives=yes&title=') + urllib.quote_plus(searchPattern)
        sts, data = self.cm.getPage(url)
        if not sts: return
        
        data = self.cm.ph.getDataBeetwenMarkers(data, 'Founded matches', '<div class="clear">')[1]
        data = self.cm.ph.getAllItemsBeetwenMarkers(data, '<a', '</a>', withMarkers=True)
        for item in data:
            url   = self.getFullUrl(self.cm.ph.getSearchGroups(item, '''href=['"]([^'^"]+?)['"]''')[0])
            title = self.cleanHtmlStr(item)

            params = {'good_for_fav': True, 'category':'explore_item', 'title':title, 'url':url}
            self.addDir(params)
        
    def getFavouriteData(self, cItem):
        printDBG('OkGoals.getFavouriteData')
        return json.dumps(cItem)
        
    def getLinksForFavourite(self, fav_data):
        printDBG('OkGoals.getLinksForFavourite')
        links = []
        try:
            cItem = byteify(json.loads(fav_data))
            links = self.getLinksForVideo(cItem)
        except Exception: printExc()
        return links
        
    def setInitListFromFavouriteItem(self, fav_data):
        printDBG('OkGoals.setInitListFromFavouriteItem')
        try:
            params = byteify(json.loads(fav_data))
        except Exception: 
            params = {}
            printExc()
        self.addDir(params)
        return True
        
    def handleService(self, index, refresh = 0, searchPattern = '', searchType = ''):
        printDBG('handleService start')
        
        CBaseHostClass.handleService(self, index, refresh, searchPattern, searchType)

        name     = self.currItem.get("name", '')
        category = self.currItem.get("category", '')
        mode     = self.currItem.get("mode", '')
        
        printDBG( "handleService: |||||||||||||||||||||||||||||||||||| name[%s], category[%s] " % (name, category) )
        self.currList = []
        
    #MAIN MENU
        if name == None:
            self.listsTab(self.MAIN_CAT_TAB, {'name':'category'})
        elif category == 'list_categories':
            self.listCategories(self.currItem, 'list_items')
        elif 'list_items' == category:
            self.listItems(self.currItem, 'explore_item')
        elif category == 'explore_item':
            self.exploreItem(self.currItem)
    #SEARCH
        elif category in ["search", "search_next_page"]:
            cItem = dict(self.currItem)
            cItem.update({'search_item':False, 'name':'category'}) 
            self.listSearchResult(cItem, searchPattern, searchType)
    #HISTORIA SEARCH
        elif category == "search_history":
            self.listsHistory({'name':'history', 'category': 'search'}, 'desc', _("Type: "))
        else:
            printExc()
        
        CBaseHostClass.endHandleService(self, index, refresh)
class IPTVHost(CHostBase):

    def __init__(self):
        CHostBase.__init__(self, OkGoals(), True, [])


