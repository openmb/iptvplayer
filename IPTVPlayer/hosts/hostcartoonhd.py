# -*- coding: utf-8 -*-
###################################################
# LOCAL import
###################################################
from Plugins.Extensions.IPTVPlayer.components.iptvplayerinit import TranslateTXT as _, SetIPTVPlayerLastHostError
from Plugins.Extensions.IPTVPlayer.components.ihost import CHostBase, CBaseHostClass, CDisplayListItem, RetHost, CUrlItem, ArticleContent
from Plugins.Extensions.IPTVPlayer.tools.iptvtools import printDBG, printExc, CSearchHistoryHelper, remove_html_markup, GetLogoDir, GetCookieDir, byteify
from Plugins.Extensions.IPTVPlayer.libs.pCommon import common, CParsingHelper
import Plugins.Extensions.IPTVPlayer.libs.urlparser as urlparser
from Plugins.Extensions.IPTVPlayer.libs.youtube_dl.utils import clean_html
from Plugins.Extensions.IPTVPlayer.tools.iptvtypes import strwithmeta
###################################################

###################################################
# FOREIGN import
###################################################
import time
import re
import random
import urllib
import base64
try:    import json
except Exception: import simplejson as json
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
config.plugins.iptvplayer.movieshdco_sortby = ConfigSelection(default = "date", choices = [("date", _("Lastest")), ("views", _("Most viewed")), ("duree", _("Longest")), ("rate", _("Top rated")), ("random", _("Tandom"))]) 
config.plugins.iptvplayer.cartoonhd_login    = ConfigText(default = "", fixed_size = False)
config.plugins.iptvplayer.cartoonhd_password = ConfigText(default = "", fixed_size = False)

def GetConfigList():
    optionList = []
    optionList.append(getConfigListEntry(_("login")+":", config.plugins.iptvplayer.cartoonhd_login))
    optionList.append(getConfigListEntry(_("password")+":", config.plugins.iptvplayer.cartoonhd_password))
    return optionList
###################################################


def gettytul():
    return 'https://cartoonhd.online/'

class CartoonHD(CBaseHostClass):
    HEADER = {'User-Agent': 'Mozilla/5.0', 'Accept': 'text/html'}
    AJAX_HEADER = dict(HEADER)
    AJAX_HEADER.update( {'X-Requested-With': 'XMLHttpRequest'} )
    
    MAIN_URL = 'https://cartoonhd.online/'
    SEARCH_URL = 'https://api.cartoonhd.online/api/v1/0A6ru35yevokjaqbb8'
    
    MAIN_CAT_TAB = [{'category':'new',            'mode':'',            'title': 'New',       'url':'search.php',    'icon':''},
                    {'category':'movies',         'mode':'movies',      'title': 'Movies',    'url':'search.php',    'icon':''},
                    {'category':'tv_shows',       'mode':'tv_shows',    'title': 'TV shows',  'url':'search.php',    'icon':''},
                    {'category':'search',          'title': _('Search'), 'search_item':True},
                    {'category':'search_history',  'title': _('Search history')} ]
 
    def __init__(self):
        CBaseHostClass.__init__(self, {'history':'CartoonHD.tv', 'cookie':'cartoonhdtv.cookie', 'cookie_type':'MozillaCookieJar'})
        self.defaultParams = {'use_cookie': True, 'load_cookie': True, 'save_cookie': True, 'cookiefile': self.COOKIE_FILE}
        self.cacheFilters = {}
        self.cacheLinks = {}
        self.loggedIn = None
        self.DEFAULT_ICON_URL = 'http://cartoonhd.online/templates/FliXanity/assets/images/logochd.png'
        
    def _getToken(self, data):
        torName = self.cm.ph.getSearchGroups(data, "var token[\s]*=([^;]+?);")[0].strip()
        return self.cm.ph.getSearchGroups(data, '''var[\s]*{0}[\s]*=[\s]*['"]([^'^"]+?)['"]'''.format(torName))[0]
        
    def _makeid(self):
        text = ""
        possible = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz"
        for i in range(25):
            text += possible[random.randint(0, len(possible)-1)]
        return text
        
    def _rflix(self, a):
        def _repFun(matchObj):
            a = matchObj.group(0) 
            if a <= 'Z': tmp = 90
            else: tmp = 122
            a = ord(a) + 13
            if tmp < a:
                a = a - 26
            return chr(a)
        return re.sub('[a-zA-Z]', _repFun, a)
            
    def fillSortNav(self, type):
        self.cacheSortNav[type] = []
        sts, data = self.cm.getPage(self.MAIN_URL + type, self.defaultParams)
        if not sts: return
        data = self.cm.ph.getDataBeetwenMarkers(data, '<select name="sortnav"', '</select>', False)[1]
        data = re.compile('<option value="http[^"]+?/([^"^/]+?)">([^<]+?)<').findall(data)
        for item in data:
            self.cacheSortNav[type].append({'sort_by':item[0], 'title':item[1]})
            
    def listSortNav(self, cItem, nextCategory):
        sts, data = self.cm.getPage(cItem['url'], self.defaultParams)
        if not sts: return
        data = self.cm.ph.getDataBeetwenMarkers(data, '<select name="sortnav"', '</select>', False)[1]
        data = re.compile('<option value="http[^"]+?/([^"^/]+?)"[^>]*?>([^<]+?)<').findall(data)
        tab = []
        for item in data:
            tab.append({'sort_by':item[0], 'title':item[1]})
        cItem = dict(cItem)
        cItem['category'] = nextCategory
        self.listsTab(tab, cItem)
            
    def fillCategories(self):
        printDBG("CartoonHD.fillCategories")
        self.cacheFilters = {}
        sts, data = self.cm.getPage(self.MAIN_URL, self.defaultParams)
        if not sts: return
        
        moviesTab = [{'title':'All', 'url':self.getFullUrl('movies')}]
        tmp = self.cm.ph.getDataBeetwenMarkers(data, '>Movies</a>', '</ul>', False)[1]
        tmp = re.compile('<a[^>]*?href="([^"]+?)"[^>]*?>([^<]+?)<').findall(tmp)
        for item in tmp:
            moviesTab.append({'title':item[1], 'url':self.getFullUrl(item[0])})
            
        tvshowsTab = [{'title':'All', 'url':self.getFullUrl('tv-shows')}]
        tmp = self.cm.ph.getDataBeetwenMarkers(data, 'TV Shows</a>', '</ul>', False)[1]
        tmp = re.compile('<a[^>]*?href="([^"]+?)"[^>]*?>([^<]+?)<').findall(tmp)
        for item in tmp:
            if 'latest-episodes' in item[0]: continue
            tvshowsTab.append({'title':item[1], 'url':self.getFullUrl(item[0])})
            
        newsTab = [{'title':'New Episodes',           'mode':'movies',   'category':'list_items',   'url':self.getFullUrl('latest-episodes')}]
        newsTab.append( {'title':'New Movies',        'mode':'movies',   'category':'list_items',   'url':self.getFullUrl('new-movies')} )
        newsTab.append( {'title':'Box Office Movies', 'mode':'movies',   'category':'list_items',   'url':self.getFullUrl('box-office-movies')} )
            
        self.cacheFilters['new']      = newsTab
        self.cacheFilters['movies']   = moviesTab
        self.cacheFilters['tv_shows'] = tvshowsTab
        
    def listMoviesCategory(self, cItem, nextCategory):
        printDBG("CartoonHD.listMoviesCategory")
        if {} == self.cacheFilters:
            self.fillCategories()
            
        cItem = dict(cItem)
        cItem['category'] = nextCategory
        self.listsTab(self.cacheFilters.get('movies', []), cItem)
        
    def listTVShowsCategory(self, cItem, nextCategory):
        printDBG("CartoonHD.listTVShowsCategory")
        if {} == self.cacheFilters:
            self.fillCategories()
            
        cItem = dict(cItem)
        cItem['category'] = nextCategory
        self.listsTab(self.cacheFilters.get('tv_shows', []), cItem)
        
    def listNewCategory(self, cItem):
        printDBG("CartoonHD.listNewCategory")
        if {} == self.cacheFilters:
            self.fillCategories()
            
        cItem = dict(cItem)
        cItem.pop("category", None)
        #cItem['category'] = nextCategory
        self.listsTab(self.cacheFilters.get('new', []), cItem)
            
    def listItems(self, cItem, nextCategory=None):
        printDBG("CartoonHD.listItems")
        page = cItem.get('page', 1)
        
        url = cItem['url'] + '/' + cItem.get('sort_by', '') + '/' + str(page)
        
        params = dict(self.defaultParams)
        params['header'] = self.AJAX_HEADER
        sts, data = self.cm.getPage(url, params)
        if not sts: return
        
        nextPage = self.cm.ph.getDataBeetwenMarkers(data, '<label for="pagenav">', '</form>', False)[1]
        if '/{0}"'.format(page+1) in nextPage:
            nextPage = True
        else: nextPage = False
        
        data = self.cm.ph.getDataBeetwenMarkers(data, '<div class="flipBox">', '</main>', False)[1]
        data = data.split('</section>')
        if len(data): del data[-1]
        for item in data:
            icon = self.getFullUrl( self.cm.ph.getSearchGroups(item, 'src="([^"]+?\.jpg[^"]*?)"')[0] )
            desc = 'IMDb ' + self.cm.ph.getSearchGroups(item, '>([ 0-9.]+?)<')[0] + ', '
            desc += self.cleanHtmlStr(' '.join(self.cm.ph.getAllItemsBeetwenMarkers(item, '<p>', '</p>', False)))
            tmp   = self.cm.ph.rgetAllItemsBeetwenMarkers(item, '</a>', '<a', True)
            url = ''
            for t in tmp:
                if url == '': url = self.getFullUrl(self.cm.ph.getSearchGroups(t, '''href=["']([^"^']+?)['"]''')[0])
                title = self.cleanHtmlStr(t)
                if title != '': break
            if url.startswith('http'):
                params = {'title':title, 'url':url, 'desc':desc, 'icon':icon}
                if nextCategory == None:
                    self.addVideo(params)
                else:
                    params['category'] = nextCategory
                    params2 = dict(cItem)
                    params2.update(params)
                    self.addDir(params2)
        if nextPage:
            params = dict(cItem)
            params.update({'title':_("Next page"), 'page':page+1})
            self.addDir(params)
        
    def listSeasons(self, cItem, nextCategory):
        printDBG("CartoonHD.listSeasons")

        sts, data = self.cm.getPage(cItem['url'], self.defaultParams)
        if not sts: return
        
        data = self.cm.ph.getDataBeetwenMarkers(data, '<b>Season(s):</b>', '</div>', False)[1]
        data = re.compile('<a[^>]*?href="([^"]+?)"[^>]*?>([^>]+?)</a>').findall(data)
        for item in data:
            params = dict(cItem)
            url = self.getFullUrl(item[0])
            params.update({'url':url, 'title':_("Season") + ' ' + item[1], 'show_title':cItem['title'], 'category':nextCategory})
            self.addDir(params)
    
    def listEpisodes(self, cItem):
        printDBG("CartoonHD.listEpisodes")

        sts, data = self.cm.getPage(cItem['url'], self.defaultParams)
        if not sts: return
        
        showTitle = cItem.get('show_title', '')
        
        data = self.cm.ph.getDataBeetwenMarkers(data, '<div class="episode', '</article>', False)[1]
        data = data.split('<div class="episode')
        for item in data:
            url   = self.getFullUrl( self.cm.ph.getSearchGroups(item, 'href="([^"#]+?)"')[0] )
            desc  = self.cm.ph.getDataBeetwenMarkers(item, '<p>', '</p>', False)[1]
            title = self.cm.ph.getSearchGroups(item, 'title="([^"]+?)"')[0]
            icon  = self.getFullUrl( self.cm.ph.getSearchGroups(item, 'data-src="([^"]+?)"')[0] )
            if '' == icon: icon = cItem.get('icon', '')
            
            if url.startswith('http'):
                if showTitle != '': title = showTitle + ' ' + title 
                params = {'title':title, 'url':url, 'icon':icon, 'desc':desc}
                self.addVideo(params)

    def listSearchResult(self, cItem, searchPattern, searchType):
        printDBG("CartoonHD.listSearchResult cItem[%s], searchPattern[%s] searchType[%s]" % (cItem, searchPattern, searchType))
        
        sts, data = self.cm.getPage(self.MAIN_URL, self.defaultParams)
        if not sts: return
        
        tor = self._getToken(data)
        currid = self._makeid()
        
        q = searchPattern
        post_data = {'q':q, 'limit':100, 'timestamp':str(time.time()).split('.')[0], 'verifiedCheck':tor, 'set':currid, 'rt':self._rflix(tor+currid), 'sl':'c3037ef6538bf7e3c048fd6997ca37d3'}
        
        httpParams = dict(self.defaultParams)
        httpParams['header'] =  {'Referer':self.MAIN_URL, 'User-Agent':self.cm.HOST, 'X-Requested-With':'XMLHttpRequest', 'Content-Type':'application/x-www-form-urlencoded; charset=UTF-8'}
        sts, data = self.cm.getPage(self.SEARCH_URL, httpParams, post_data=post_data)
        if not sts: return
        printDBG(data)
        try:
            data = byteify(json.loads(data))
            for item in data:
                desc = item['meta']
                if 'movie' in desc.lower():
                    category = 'video'
                elif 'tv show' in desc.lower():
                    category = 'list_seasons'
                else:
                    category = None
                
                if None != category:
                    title = item['title']
                    url   = item['permalink'].replace('\\/', '/')
                    icon  = item.get('image', '').replace('\\/', '/')
                    if '' != url:
                        params = {'name':'category', 'title':title, 'url':self.getFullUrl(url), 'desc':desc, 'icon':self.getFullUrl(icon), 'category':category}
                        if category == 'video':
                            self.addVideo(params)
                        else:
                            self.addDir(params)
        except Exception:
            printExc()
    
    def getLinksForVideo(self, cItem):
        printDBG("CartoonHD.getLinksForVideo [%s]" % cItem)
        
        def gettt():
            data = str(int(time.time()))
            b64="ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/="
            i       = 0
            enc     = ""
            tmp_arr = []
            mask    = 0x3f
            while True:
                o1 = ord(data[i])
                i += 1
                if i < len(data):
                    o2 = ord(data[i])
                else:
                    o2 = 0
                i += 1
                if i < len(data):
                    o3 = ord(data[i])
                else:
                    o3 = 0
                i += 1
                bits = o1 << 16 | o2 << 8 | o3
                h1   = bits >> 18 & mask
                h2   = bits >> 12 & mask
                h3   = bits >> 6 & mask
                h4   = bits & mask
                tmp_arr.append( b64[h1] + b64[h2] + b64[h3] + b64[h4] )
                if i >= len(data):
                    break
            enc = ''.join(tmp_arr)
            r   = len(data) % 3
            if r > 0:
                fill = '==='
                enc  = enc[0:r-3] + fill[r:]
            return enc
        
        def getCookieItem(name):
            value = ''
            try:
                value = self.cm.getCookieItem(self.COOKIE_FILE, name)
            except Exception:
                printExc()
            return value
        
        urlTab = self.cacheLinks.get(cItem['url'],  [])
        if len(urlTab): return urlTab
        self.cacheLinks = {}
        
        sts, data = self.cm.getPage(cItem['url'], self.defaultParams)
        if not sts: return []
        
        tor  = self._getToken(data)
        elid = self.cm.ph.getSearchGroups(data, '''elid[\s]*=[\s]['"]([^"^']+?)['"]''')[0]
        if '' == elid: elid = self.cm.ph.getSearchGroups(data, 'data-id="([^"]+?)"')[0]
        if '' == elid: elid = self.cm.ph.getSearchGroups(data, 'data-movie="([^"]+?)"')[0]
        if '' == elid: return []
        
        if "movieInfo['season']" not in data and 'movieInfo["season"]' not in data:
            type = 'getMovieEmb'
        else: type = 'getEpisodeEmb'
        #if '/movie/' in cItem['url']:
        #    type = 'getMovieEmb'
        #else: type = 'getEpisodeEmb'
        
        tmp = self.cm.ph.getDataBeetwenMarkers(data, '<select', '</select>', False)[1]
        hostings = []
        tmp = re.compile('<option[^>]*?value="([^"]+?)"[^>]*?>([^<]+?)</option>').findall(tmp)
        for item in tmp:
            hostings.append({'id':item[0], 'name':item[1]})
        
        httpParams = dict(self.defaultParams)
        httpParams['header'] =  {'Referer':cItem['url'], 'User-Agent':self.cm.HOST, 'X-Requested-With':'XMLHttpRequest', 'Accept':'application/json, text/javascript, */*; q=0.01'}
        encElid = gettt()
        __utmx = getCookieItem('__utmx')
        httpParams['header']['Authorization'] = 'Bearer ' + urllib.unquote(__utmx)
        
        requestLinks = ['ajax/tnembeds.php']
        if 'class="play"' in data and 'id="updateSources"' not in data:
            requestLinks.append('ajax/embeds.php')
        
        #httpParams['header']['Cookie'] = '%s=%s; PHPSESSID=%s; flixy=%s;'% (elid, urllib.quote(encElid), getCookieItem('PHPSESSID'), getCookieItem('flixy'))
        for url in requestLinks:
            post_data = {'action':type, 'idEl':elid, 'token':tor, 'elid':urllib.quote(encElid)}
            sts, data = self.cm.getPage(self.getFullUrl(url), httpParams, post_data)
            if not sts: continue
            printDBG('===============================================================')
            printDBG(data)
            printDBG('===============================================================')
            printDBG(hostings)
            try:
                keys = re.compile('"(_[0-9]+?)"').findall(data)
                data = byteify(json.loads(data))
                for key in data.keys():
                    if key not in keys:
                        keys.append(key)
                for key in keys:
                    if key not in keys: continue
                    url  = data[key]['embed'].replace('\\/', '/')
                    url  = self.cm.ph.getSearchGroups(url, '''src=['"]([^"^']+?)['"]''', 1, ignoreCase=True)[0]
                    name = data[key]['type'] 
                    if 'googlevideo.com' in url or 'googleusercontent.com' in url:
                        need_resolve = 0
                    elif 1 == self.up.checkHostSupport(url):
                        need_resolve = 1
                    else: 
                        need_resolve = 0
                    if url.startswith('http'):
                        urlTab.append({'name':name, 'url':url, 'need_resolve':need_resolve})
            except Exception:
                printExc()
            if len(urlTab): break
        urlTab = urlTab[::-1]
        self.cacheLinks[cItem['url']] = urlTab
        return urlTab
        
    def getVideoLinks(self, videoUrl):
        printDBG("CartoonHD.getVideoLinks [%s]" % videoUrl)
        urlTab = []
        
        # mark requested link as used one
        if len(self.cacheLinks.keys()):
            key = self.cacheLinks.keys()[0]
            for idx in range(len(self.cacheLinks[key])):
                if videoUrl in self.cacheLinks[key][idx]['url']:
                    if not self.cacheLinks[key][idx]['name'].startswith('*'):
                        self.cacheLinks[key][idx]['name'] = '*' + self.cacheLinks[key][idx]['name']
                    break
        
        if self.cm.isValidUrl( videoUrl ):
            urlTab = self.up.getVideoLinkExt(videoUrl)
        return urlTab
        
    def getFavouriteData(self, cItem):
        return cItem['url']
        
    def getLinksForFavourite(self, fav_data):
        return self.getLinksForVideo({'url':fav_data})

    def tryTologin(self):
        printDBG('tryTologin start')
        login = config.plugins.iptvplayer.cartoonhd_login.value
        password = config.plugins.iptvplayer.cartoonhd_password.value
        
        if '' == login.strip() or '' == password.strip():
            printDBG('tryTologin wrong login data')
            #self.sessionEx.open(MessageBox, _('This host requires registration. \nPlease fill your login and password in the host configuration. Available under blue button.'), type = MessageBox.TYPE_ERROR, timeout = 10 )
            return False
        
        post_data = {'username':login, 'password':password, 'action':'login', 't':''}
        params = {'header':self.HEADER, 'cookiefile':self.COOKIE_FILE, 'use_cookie': True, 'save_cookie':True}
        sts, data = self.cm.getPage(self.MAIN_URL, params, post_data)
        if sts:
            if '>Logout<' in data:
                printDBG('tryTologin OK')
                return True
     
        self.sessionEx.open(MessageBox, _('Login failed.'), type = MessageBox.TYPE_ERROR, timeout = 10)
        printDBG('tryTologin failed')
        return False
        
    def handleService(self, index, refresh = 0, searchPattern = '', searchType = ''):
        printDBG('handleService start')
        
        if None == self.loggedIn:
            self.loggedIn = self.tryTologin()
        
        CBaseHostClass.handleService(self, index, refresh, searchPattern, searchType)

        name     = self.currItem.get("name", '')
        category = self.currItem.get("category", '')
        mode     = self.currItem.get("mode", '')
        
        printDBG( "handleService: |||||||||||||||||||||||||||||||||||| name[%s], category[%s] " % (name, category) )
        self.currList = []
        
    #MAIN MENU
        if name == None:
            self.listsTab(self.MAIN_CAT_TAB, {'name':'category'})
        elif category == 'new':
            self.listNewCategory(self.currItem)
        elif category == 'movies':
            self.listMoviesCategory(self.currItem, 'list_sortnav')
        elif category == 'tv_shows':
            self.listTVShowsCategory(self.currItem, 'list_sortnav')
            
        elif category == 'list_sortnav':
            self.listSortNav(self.currItem, 'list_items')
            if len(self.currList) == 0:
                category = 'list_items'
        if category == 'list_items':
            if mode == 'movies':
                self.listItems(self.currItem)
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
        CHostBase.__init__(self, CartoonHD(), True, [CDisplayListItem.TYPE_VIDEO, CDisplayListItem.TYPE_AUDIO])
