# -*- coding: utf-8 -*-
###################################################
# LOCAL import
###################################################
from Plugins.Extensions.IPTVPlayer.components.iptvplayerinit import TranslateTXT as _, SetIPTVPlayerLastHostError
from Plugins.Extensions.IPTVPlayer.components.ihost import CHostBase, CBaseHostClass, CDisplayListItem, RetHost, CUrlItem, ArticleContent
from Plugins.Extensions.IPTVPlayer.tools.iptvtools import printDBG, printExc, GetLogoDir, GetCookieDir, byteify
from Plugins.Extensions.IPTVPlayer.tools.iptvtypes import strwithmeta
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
    return 'http://filiser.tv/'

class FiliserTv(CBaseHostClass):
 
    def __init__(self):
        CBaseHostClass.__init__(self, {'history':'FiliserTv.tv', 'cookie':'filisertv.cookie'})
        
        self.HEADER = {'User-Agent': 'Mozilla/5.0', 'Accept': 'text/html'}
        self.AJAX_HEADER = dict(self.HEADER)
        self.AJAX_HEADER.update( {'X-Requested-With': 'XMLHttpRequest'} )
        self.defaultParams = {'header':self.HEADER, 'use_cookie': True, 'load_cookie': True, 'save_cookie': True, 'cookiefile': self.COOKIE_FILE}
        
        self.MAIN_URL = 'http://filiser.tv/'
        self.DEFAULT_ICON_URL = self.MAIN_URL + 'assets/img/logo.png'
        
        self.MAIN_CAT_TAB = [{'category':'list_items',        'title': _('Movies'),                       'url':self.getFullUrl('filmy')   },
                             {'category':'list_items',        'title': _('Series'),                       'url':self.getFullUrl('seriale') },
                             {'category':'search',            'title': _('Search'),               'search_item':True,                      },
                             {'category':'search_history',    'title': _('Search history'),                                                } 
                            ]
        
        self.cacheFilters = {}
        self.cacheLinks = {}
        self.cacheSeasons = {}
        FiliserTv.SALT_CACHE = {}
        self.WaitALittleBit  = None
        
    def getStr(self, item, key):
        if key not in item: return ''
        if item[key] == None: return ''
        return str(item[key])
        
    def fillFilters(self, cItem):
        self.cacheFilters = {}
        sts, data = self.cm.getPage(cItem['url'])
        if not sts: return
        
        def addFilter(data, key, addAny, titleBase, marker):
            self.cacheFilters[key] = []
            for item in data:
                value = self.cm.ph.getSearchGroups(item, '''%s=['"]([^'^"]+?)['"]''' % marker)[0]
                if value == '': continue
                title = self.cleanHtmlStr(item)
                if titleBase == '':
                    title = title.title()
                self.cacheFilters[key].append({'title':titleBase + title, key:value})
            if addAny and len(self.cacheFilters[key]):
                self.cacheFilters[key].insert(0, {'title':'Wszystkie'})
                
        # language
        tmpData = self.cm.ph.getAllItemsBeetwenMarkers(data, '<div class="vBox"', '</div>', withMarkers=True)
        addFilter(tmpData, 'language', True, '', 'data-type')
        
        # genres
        tmpData = self.cm.ph.getAllItemsBeetwenMarkers(data, '<li data-gen', '</li>', withMarkers=True)
        addFilter(tmpData, 'genres', True, '', 'data-gen') 
        
        # year
        self.cacheFilters['year'] = [{'title':_('Year: ') + _('Any')}]
        year = datetime.now().year
        while year >= 1978:
            self.cacheFilters['year'].append({'title': _('Year: ') + str(year), 'year': year})
            year -= 1
        
        # sort
        self.cacheFilters['sort_by'] = []
        for item in [('date', 'data dodania/aktualizacji'), ('views', ' liczba wyświetleń'), ('rate', ' ocena')]:
            self.cacheFilters['sort_by'].append({'title': _('Sort by: ') + str(item[1]), 'sort_by': item[0]})
        
        # add order to sort_by filter
        orderLen = len(self.cacheFilters['sort_by'])
        for idx in range(orderLen):
            item = deepcopy(self.cacheFilters['sort_by'][idx])
            # desc
            self.cacheFilters['sort_by'][idx].update({'title':'\xe2\x86\x93 ' + self.cacheFilters['sort_by'][idx]['title'], 'order':'desc'})
            # asc
            item.update({'title': '\xe2\x86\x91 ' + item['title'], 'order':'asc'})
            self.cacheFilters['sort_by'].append(item)
        
    def listFilter(self, cItem, filters):
        params = dict(cItem)
        idx = params.get('f_idx', 0)
        params['f_idx'] = idx + 1
        
        if idx == 0:
            self.fillFilters(cItem)
        
        tab = self.cacheFilters.get(filters[idx], [])
        self.listsTab(tab, params)
        
    def listItems(self, cItem, nextCategory):
        printDBG("FiliserTv.listItems")
        
        baseUrl = cItem['url']
        if '?' not in baseUrl:
            baseUrl += '?'
        else:
            baseUrl += '&'
        
        page = cItem.get('page', 1)
        if page > 1:
            baseUrl += 'page={0}&'.format(page)
        
        if cItem.get('genres', '') not in ['-', '']:
            baseUrl += 'kat={0}&'.format(cItem['genres'])
        
        if cItem.get('language', '') not in ['-', '']:
            baseUrl += 'ver={0}&'.format(cItem['language'])
        
        if cItem.get('year', '0') not in ['0', '-', '']:
            baseUrl += 'start_year={0}&end_year={1}&'.format(cItem['year'], cItem['year'])
        
        if cItem.get('sort_by', '0') not in ['0', '-', '']:
            baseUrl += 'sort_by={0}&'.format(cItem['sort_by'])
            
        if cItem.get('order', '0') not in ['0', '-', '']:
            baseUrl += 'type={0}&'.format(cItem['order'])
            
        sts, data = self.cm.getPage(self.getFullUrl(baseUrl), self.defaultParams)
        if not sts: return
        
        if '>Następna<' in data:
            nextPage = True
        else: nextPage = False
        
        data = self.cm.ph.getAllItemsBeetwenMarkers(data, '<section class="item"', '</section>', withMarkers=True)
        for item in data:
            url    = self.getFullUrl(self.cm.ph.getSearchGroups(item, '''href=['"]([^'^"]+?)['"]''')[0])
            icon   = self.getFullIconUrl(self.cm.ph.getSearchGroups(item, '''src=['"]([^'^"]+?)['"]''')[0].strip())
            title  = self.cleanHtmlStr(self.cm.ph.getSearchGroups(item, '''alt=['"]([^'^"]+?)['"]''')[0])
            if title == '': title = self.cleanHtmlStr(self.cm.ph.getSearchGroups(item, '''title=['"]([^'^"]+?)['"]''')[0])
            title1 = self.cleanHtmlStr(self.cm.ph.getDataBeetwenMarkers(item, '<h3', '</h3>')[1])
            title2 = self.cleanHtmlStr(self.cm.ph.getDataBeetwenMarkers(item, '<h4', '</h4>')[1])
            
            desc   = self.cleanHtmlStr(item.split('<div class="block2">')[-1].replace('<p class="desc">', '[/br]'))
            params = {'good_for_fav': True, 'title':title, 'url':url, 'icon':icon, 'desc':desc}
            if '/film/' in url:
                self.addVideo(params)
            elif '/serial/' in url:
                params['category'] = nextCategory
                self.addDir(params)
        
        if nextPage:
            params = dict(cItem)
            params.update({'title':_('Next page'), 'page':page + 1})
            self.addDir(params)
        
    def listSeasons(self, cItem, nextCategory):
        printDBG("FiliserTv.listSeasons")
        
        self.cacheSeasons = {'keys':[], 'dict':{}}
        
        sts, data = self.cm.getPage(cItem['url'], self.defaultParams)
        if not sts: return
        
        data = data.split('<div id="episodes">')
        if 2 != len(data): return
        
        tmp = self.cm.ph.getDataBeetwenMarkers(data[0], '<div id="seasons_list">', '<div class="clear">')[1]
        tmp = re.compile('<[^>]+?num\="([0-9]+?)"[^>]*?>([^<]+?)<').findall(tmp)
        for item in tmp:
            self.cacheSeasons['keys'].append({'key':item[0], 'title':self.cleanHtmlStr(item[1])})
        
        del data[0]
        
        # fill episodes
        for season in self.cacheSeasons['keys']:
            tmp = self.cm.ph.getDataBeetwenMarkers(data[0], 'data-season-num="%s"' % season['key'], '</ul>')[1]
            tmp = self.cm.ph.getAllItemsBeetwenMarkers(tmp, '<li', '</li>', withMarkers=True)
            self.cacheSeasons['dict'][season['key']] = []
            for item in tmp:
                url    = self.getFullUrl(self.cm.ph.getSearchGroups(item, '''href=['"]([^'^"]+?)['"]''')[0])
                title  = self.cleanHtmlStr(self.cm.ph.getDataBeetwenMarkers(item, '<a class="episodeName"', '</a>')[1])
                es     = self.cm.ph.getSearchGroups(url, '''/(s[0-9]+?e[0-9]+?)/''')[0]
                self.cacheSeasons['dict'][season['key']].append({'good_for_fav': True, 'title': '%s: %s %s' % (cItem['title'], es, title), 'url':url})
                
        for season in self.cacheSeasons['keys']:
            params = dict(cItem)
            params.update({'good_for_fav': False, 'category':nextCategory, 'title':season['title'], 's_key':season['key']})
            self.addDir(params)
        
    def listEpisodes(self, cItem):
        printDBG("FiliserTv.listEpisodes")
        
        tab = self.cacheSeasons.get('dict', {}).get(cItem['s_key'], [])
        for item in tab:
            params = dict(cItem)
            params.update(item)
            self.addVideo(params)

    def listSearchResult(self, cItem, searchPattern, searchType):
        printDBG("FiliserTv.listSearchResult cItem[%s], searchPattern[%s] searchType[%s]" % (cItem, searchPattern, searchType))
        
        baseUrl = self.getFullUrl('szukaj?q=' + urllib.quote_plus(searchPattern))
        sts, data = self.cm.getPage(baseUrl)
        if not sts: return

        data = self.cm.ph.getDataBeetwenMarkers(data, '<ul id="resultList2">', '</ul>', withMarkers=False)[1]
        data = self.cm.ph.getAllItemsBeetwenMarkers(data, '<li', '</li>', withMarkers=True)
        for item in data:
            tmp    = item.split('<div class="info">')
            url    = self.getFullUrl(self.cm.ph.getSearchGroups(item, '''href=['"]([^'^"]+?)['"]''')[0])
            title  = self.cleanHtmlStr(tmp[0].replace('<div class="title_org">', '/'))
            icon   = self.getFullIconUrl(self.cm.ph.getSearchGroups(item, '''src=['"]([^'^"]+?)['"]''')[0].strip())
            desc   = self.cleanHtmlStr(tmp[-1])
            params = {'good_for_fav': True, 'title':title, 'url':url, 'icon':icon, 'desc':desc}
            if '/film/' in url:
                self.addVideo(params)
            elif '/serial/' in url:
                params['category'] = 'list_seasons'
                self.addDir(params)
    
    def getLinksForVideo(self, cItem):
        printDBG("FiliserTv.getLinksForVideo [%s]" % cItem)
        urlTab = []
        
        if len(self.cacheLinks.get(cItem['url'], [])):
            return self.cacheLinks[cItem['url']]
        
        sts, data = self.cm.getPage(cItem['url'], self.defaultParams)
        if not sts: return []
        
        errorMessage = self.cleanHtmlStr(self.cm.ph.getDataBeetwenMarkers(data, '<h2 class="title_block">', '</section>')[1])
        if '' != errorMessage:  SetIPTVPlayerLastHostError(errorMessage)
        
        data = data.split('<div id="links">')
        if 2 != len(data): return []
        
        tabs = []
        tmp = self.cm.ph.getDataBeetwenMarkers(data[0], '<div id="video_links">', '<div class="clear">')[1]
        tmp = re.compile('<[^>]+?data-type\="([^"]+?)"[^>]*?>([^<]+?)<').findall(tmp)
        for item in tmp:
            tabs.append({'key':item[0], 'title':self.cleanHtmlStr(item[1])})
        
        del data[0]
        
        for tab in tabs:
            tmp = self.cm.ph.getDataBeetwenMarkers(data[0], 'data-type="%s"' % tab['key'], '</ul>')[1]
            tmp = self.cm.ph.getAllItemsBeetwenMarkers(tmp, '<li', '</li>', withMarkers=True)
            for item in tmp:
                url    = self.cm.ph.getSearchGroups(item, '''data-ref=['"]([^'^"]+?)['"]''')[0]
                title  = self.cleanHtmlStr(item.split('<div class="rightSide">')[0])
                urlTab.append({'name': '%s: %s' % (tab['title'], title), 'url':url, 'need_resolve':1})
        
        self.cacheLinks[cItem['url']] = urlTab
        return urlTab
        
    def getHeaders(self, tries):
        header = dict(self.HEADER)
        if tries == 1:
            return header
        
        if self.WaitALittleBit == None:
            try:
                tmp = 'ZGVmIHphcmF6YShpbl9hYmMpOg0KICAgIGRlZiByaGV4KGEpOg0KICAgICAgICBoZXhfY2hyID0gJzAxMjM0NTY3ODlhYmNkZWYnDQogICAgICABiID0gZmYoYiwgYywgZCwgYSwgdGFiQlszXSwgMjIsIC0xMDQ0NTI1MzMwKTsN\rZGVmIFdhaXRBTGl0dGxlQml0KHRyaWVzKToNCiAgICBmaXJzdEJ5dGUgPSBbODUsMTA5LDg5LDkxLDQ2LDE3OCwyMTcsMjEzXQ0KICAgIGlwID0gJyVzLiVzLiVzLiVzJyAlIChmaXJzdEJ5dGVbcmFuZGludCgwLCBsZW4oZmlyc3RCeXRlKSldLCByYW5kaW50KDAsIDI0NiksICByYW5kaW50KDAsIDI0NiksICByYW5kaW50KDAsIDI0NikpDQogICAgcmV0dXJuIHsnVXNlci1BZ2VudCc6J01vemlsbGEvNS4wJywnQWNjZXB0JzondGV4dC9odG1sJywnWC1Gb3J3YXJkZWQtRm9yJzppcH0NCg0K'
                tmp = base64.b64decode(tmp.split('\r')[-1]).replace('\r', '')
                WaitALittleBit = compile(tmp, '', 'exec')
                vGlobals = {"__builtins__": None, 'len': len, 'list': list, 'dict':dict, 'randint':randint}
                vLocals = { 'WaitALittleBit': '' }
                exec WaitALittleBit in vGlobals, vLocals
                self.WaitALittleBit = vLocals['WaitALittleBit']
            except Exception:
                printExc()
        try:
            header.update(self.WaitALittleBit(tries))
        except Exception:
            printExc()
        return header
        
    def getVideoLinks(self, videoUrl):
        printDBG("FiliserTv.getVideoLinks [%s]" % videoUrl)
        urlTab = []
        
        # mark requested link as used one
        if len(self.cacheLinks.keys()):
            key = self.cacheLinks.keys()[0]
            for idx in range(len(self.cacheLinks[key])):
                if videoUrl in self.cacheLinks[key][idx]['url']:
                    if not self.cacheLinks[key][idx]['name'].startswith('*'):
                        self.cacheLinks[key][idx]['name'] = '*' + self.cacheLinks[key][idx]['name']
                    break
        
        reCaptcha = False
        if not self.cm.isValidUrl(videoUrl):
            salt = videoUrl
            if salt not in FiliserTv.SALT_CACHE:
                httpParams = dict(self.defaultParams)
                tries = 0
                while tries < 6:
                    tries += 1
                    url = 'http://filiser.tv/embed?salt=' + videoUrl
                    httpParams['header'] = self.getHeaders(tries)
                    sts, data = self.cm.getPage(url, httpParams)
                    if not sts: return urlTab
                    
                    if '/captchaResponse' in data:
                        reCaptcha = True
                        sleep(1)
                        continue
                    
                    reCaptcha = False
                    
                    videoUrl = self.cm.ph.getSearchGroups(data, '''var\s*url\s*=\s*['"](http[^'^"]+?)['"]''')[0]
                    videoUrl = videoUrl.replace('#WIDTH', '800').replace('#HEIGHT', '600')
                    
                    if self.cm.isValidUrl(videoUrl):
                        FiliserTv.SALT_CACHE[salt] = base64.b64encode(videoUrl)
                    
                    break
            else:
                videoUrl = base64.b64decode(FiliserTv.SALT_CACHE[salt])
        
        if self.cm.isValidUrl(videoUrl):
            urlTab = self.up.getVideoLinkExt(videoUrl)
            
        if reCaptcha:
            self.sessionEx.open(MessageBox, 'Otwórz stronę http://filiser.tv/ w przeglądarce i odtwórz dowolny film potwierdzając, że jesteś człowiekiem.', type = MessageBox.TYPE_ERROR, timeout = 10 )
        
        return urlTab
        
    def getFavouriteData(self, cItem):
        printDBG('FiliserTv.getFavouriteData')
        return json.dumps(cItem)
        
    def getLinksForFavourite(self, fav_data):
        printDBG('FiliserTv.getLinksForFavourite')
        links = []
        try:
            cItem = byteify(json.loads(fav_data))
            links = self.getLinksForVideo(cItem)
        except Exception: printExc()
        return links
        
    def setInitListFromFavouriteItem(self, fav_data):
        printDBG('FiliserTv.setInitListFromFavouriteItem')
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
        elif 'list_items' == category:
            filtersTab = ['language', 'genres', 'year', 'sort_by']
            idx = self.currItem.get('f_idx', 0)
            if idx < len(filtersTab):
                self.listFilter(self.currItem, filtersTab)
            else:
                self.listItems(self.currItem, 'list_seasons')
        elif category == 'list_seasons':
            self.listSeasons(self.currItem, 'list_episodes')
        elif category == 'list_episodes':
            self.listEpisodes(self.currItem)
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
        CHostBase.__init__(self, FiliserTv(), True, [])


