# -*- coding: utf-8 -*-

###################################################
# LOCAL import
###################################################
from Plugins.Extensions.IPTVPlayer.tools.iptvtools           import printDBG, printExc, GetBinDir, GetTmpDir, GetPyScriptCmd, IsFPUAvailable
from Plugins.Extensions.IPTVPlayer.setup.iptvsetuphelper     import CBinaryStepHelper, CCmdValidator, SetupDownloaderCmdCreator
from Plugins.Extensions.IPTVPlayer.components.iptvplayerinit import TranslateTXT as _
###################################################

###################################################
# FOREIGN import
###################################################
from Screens.MessageBox  import MessageBox
from Components.config   import config, configfile
from Tools.BoundFunction import boundFunction
from Tools.Directories   import resolveFilename, SCOPE_PLUGINS
from os                  import path as os_path, chmod as os_chmod, remove as os_remove, listdir as os_listdir, getpid as os_getpid
import re
###################################################

class IPTVSetupImpl:
    def __init__(self, finished, chooseQuestion, showMessage, setInfo):
        printDBG("IPTVSetupImpl.__init__ -------------------------------")
        
        # callbacks
        self._finished    = finished
        self._chooseQuestion = chooseQuestion
        self._showMessage = showMessage
        self._setInfo     = setInfo
        self.workingObj   = None
        self.stepHelper   = None
        self.termination  = False
        
        self.tmpDir = GetTmpDir()
        self.resourceServers = ["http://iptvplayer.pl/resources/", "http://iptvplayer.vline.pl/resources/"]
        
        self.ffmpegVersion = ""
        self.gstreamerVersion = ""
        self.openSSLVersion = ""
        self.libSSLPath = ""
        self.supportedPlatforms = ["sh4", "mipsel", "i686", "armv7", "armv5t"]
        self.platform = "unknown"
        self.glibcVersion = -1
        
        # wget members
        self.wgetVersion = 15 # 1.15 
        self.wgetpaths = ["wget", "/usr/bin/wget", "/usr/bin/fullwget", GetBinDir("wget", "")]
        self._wgetInstallChoiseList = [(_('Install into the "%s".') % ("/usr/bin/fullwget " + _("recommended")), "/usr/bin/fullwget"),
                                       (_('Install into the "%s".') % "IPTVPlayer/bin/wget", GetBinDir("wget", "")),
                                       (_('Install into the "%s".') % "/usr/bin/wget", "/usr/bin/wget"),
                                       (_("Do not install (not recommended)"), "")]
        # rtmpdump members
        self.rtmpdumpVersion = {'sh4':'2015', 'mipsel':'2015', 'armv5t':'2015', 'armv7':'2015', 'default':"Compiled by samsamsam@o2.pl 2015-01-11"} #'K-S-V patch'
        self.rtmpdumppaths = ["/usr/bin/rtmpdump", "rtmpdump"]
        
        # f4mdump member
        self.f4mdumpVersion = 0.80
        self.f4mdumppaths = ["/usr/bin/f4mdump", GetBinDir("f4mdump", "")]
        self._f4mdumpInstallChoiseList = [(_('Install into the "%s".') % ("/usr/bin/f4mdump (%s)" % _("recommended")), "/usr/bin/f4mdump"),
                                          (_('Install into the "%s".') % "IPTVPlayer/bin/f4mdump", GetBinDir("f4mdump", "")),
                                          (_("Do not install (not recommended)"), "")]
        self._f4mdumpInstallChoiseList2 = [(_('Install into the "%s".') % ("/usr/bin/f4mdump static libstdc++ (%s)" % _("recommended")), "/usr/bin/f4mdump"),
                                          (_('Install into the "%s".') % "IPTVPlayer/bin/f4mdump _static_libstdc++", GetBinDir("f4mdump", "")),
                                          (_("Do not install (not recommended)"), "")]
                                          
        # uchardet member
        self.uchardetVersion = [0, 0, 6] #UCHARDET_VERSION_MAJOR, UCHARDET_VERSION_MINOR, UCHARDET_VERSION_REVISION
        self.uchardetpaths = ["/usr/bin/uchardet", GetBinDir("uchardet", "")]
        self._uchardetInstallChoiseList = [(_('Install into the "%s".') % ("/usr/bin/uchardet (%s)" % _("recommended")), "/usr/bin/uchardet"),
                                          (_('Install into the "%s".') % "IPTVPlayer/bin/uchardet", GetBinDir("uchardet", "")),
                                          (_("Do not install (not recommended)"), "")]
        self._uchardetInstallChoiseList2 = [(_('Install into the "%s".') % ("/usr/bin/uchardet static libstdc++ (%s)" % _("recommended")), "/usr/bin/uchardet"),
                                          (_('Install into the "%s".') % "IPTVPlayer/bin/uchardet _static_libstdc++", GetBinDir("uchardet", "")),
                                          (_("Do not install (not recommended)"), "")]
        # gstplayer
        self.gstplayerVersion = {'0.10':20, '1.0':10021}
        self.gstplayerpaths = ["/usr/bin/gstplayer", GetBinDir("gstplayer", "")]
        self._gstplayerInstallChoiseList = [(_('Install into the "%s".') % ("/usr/bin/gstplayer (%s)" % _("recommended")), "/usr/bin/gstplayer"),
                                          (_('Install into the "%s".') % "IPTVPlayer/bin/gstplayer", GetBinDir("gstplayer", "")),
                                          (_("Do not install (not recommended)"), "")]
        # exteplayer3
        self.exteplayer3Version = {'sh4': 33, 'mipsel': 33, 'armv7': 33, 'armv5t':33}
        self.exteplayer3paths = ["/usr/bin/exteplayer3", GetBinDir("exteplayer3", "")]
        self._exteplayer3InstallChoiseList = [(_('Install into the "%s".') % ("/usr/bin/exteplayer3 (%s)" % _("recommended")), "/usr/bin/exteplayer3"),
                                          (_('Install into the "%s".') % "IPTVPlayer/bin/exteplayer3", GetBinDir("exteplayer3", "")),
                                          (_("Do not install (not recommended)"), "")]
                                          
        # flumpegdemux
        self.flumpegdemuxVersion = "0.10.85"
        self.flumpegdemuxpaths = ["/usr/lib/gstreamer-0.10/libgstflumpegdemux.so"]
        
        # gstifdsrc
        self.gstifdsrcVersion = "1.1.1"
        self.gstifdsrcPaths = ["/usr/lib/gstreamer-1.0/libgstifdsrc.so"]
        
        # subparser
        self.subparserVersion = 0.4
        self.subparserPaths = [resolveFilename(SCOPE_PLUGINS, 'Extensions/IPTVPlayer/libs/iptvsubparser/_subparser.so')]
        
        # hlsdl
        self.hlsdlVersion = 0.03
        self.hlsdlPaths = [resolveFilename(SCOPE_PLUGINS, 'Extensions/IPTVPlayer/bin/hlsdl')]
        
        self.binaryInstalledSuccessfully = False
        self.tries = 0
        
    def __del__(self):
        printDBG("IPTVSetupImpl.__del__ -------------------------------")
        
    def terminate(self):
        printDBG("IPTVSetupImpl.terminate -------------------------------")
        self.termination  = True
        self._finished    = None
        self._chooseQuestion = None
        self._showMessage = None
        self._setInfo     = None 
        if self.workingObj: self.workingObj.terminate()
        
    def finish(self, sts=None, ret=None):
        printDBG("IPTVSetupImpl.finish")
        if self._finished: self._finished()
        
    def chooseQuestion(self, title, list, callback):
        printDBG("IPTVSetupImpl.chooseQuestion")
        if self._chooseQuestion: self._chooseQuestion(title, list, callback)
        
    def showMessage(self, message, type, callback):
        printDBG("IPTVSetupImpl.showMessage")
        if self._showMessage: self._showMessage(message, type, callback)
        
    def setInfo(self, title, message):
        printDBG("IPTVSetupImpl.setInfo")
        if self._setInfo: self._setInfo(title, message)
        
    def setInfoFromStepHelper(self, key):
        if None != self.stepHelper:
            self.setInfo(_(self.stepHelper.getMessage(key,0)), _(self.stepHelper.getMessage(key,1)))
       
    def start(self):
        printDBG("IPTVSetupImpl.showMessage")
        self.glibcVerDetect()
        
    ###################################################
    # STEP: GLIBC VERSION DETECTION
    ###################################################
    def glibcVerDetect(self):
        printDBG("IPTVSetupImpl.glibcVerDetect")
        self.setInfo(_("Detection of glibc version."), _("Detection version of installed standard C library."))
        cmdTabs = []
        cmdTabs.append("ls /lib/libc-*.so 2>&1")
        
        def _glibcVerValidator(code, data):
            printDBG("IPTVSetupImpl._glibcVerValidator")
            return True,False
        self.workingObj = CCmdValidator(self.glibcVerDetectFinished, _glibcVerValidator, cmdTabs)
        self.workingObj.start()
        
    def glibcVerDetectFinished(self, stsTab, dataTab):
        printDBG("IPTVSetupImpl.glibcVerDetectFinished")
        
        try: 
            self.glibcVersion = int(float(re.search("libc\-([0-9]+?\.[0-9]+?)\.", dataTab[-1]).group(1)) * 1000)
        except Exception: 
            self.glibcVersion = -1
            
        self.platformDetect()

    ###################################################
    # STEP: PLATFORM DETECTION
    ###################################################
    def platformDetect(self):
        printDBG("IPTVSetupImpl.platformDetect")
        self.setInfo(_("Detection of the platform."), _("Plugin can be run on one of the following platforms: sh4, mipsel, i686, armv7, armv5t."))
        cmdTabs = []
        for platform in self.supportedPlatforms:
            platformtesterPath = resolveFilename(SCOPE_PLUGINS, "Extensions/IPTVPlayer/bin/%s/platformtester" % platform)
            try: os_chmod(platformtesterPath, 0777)
            except Exception: printExc()
            cmdTabs.append(platformtesterPath + "  2>&1 ")
        def _platformValidator(code, data):
            printDBG("IPTVSetupImpl._platformValidator")
            if "Test platform OK" in data: return True,False
            else: return False,True
        self.workingObj = CCmdValidator(self.platformDetectFinished, _platformValidator, cmdTabs)
        self.workingObj.start()
        
    def platformDetectFinished(self, stsTab, dataTab):
        printDBG("IPTVSetupImpl.platformDetectFinished")
        def _saveConfig(platform):
            self.platform = platform
            config.plugins.iptvplayer.plarform.value = self.platform
            printDBG("IPTVSetupImpl.platformDetectFinished platform[%s]" % self.platform)
            config.plugins.iptvplayer.plarform.save()
            configfile.save()
        
        if len(stsTab) > 0 and True == stsTab[-1]:
            _saveConfig( self.supportedPlatforms[len(stsTab)-1] )
            self.getOpensslVersion()
        else:
            _saveConfig( "unknown" )
            self.showMessage(_("Fatal Error!\nPlugin is not supported with your platform."), MessageBox.TYPE_ERROR, boundFunction(self.finish, False) )
    
    ###################################################
    # STEP: OpenSSL DETECTION
    ###################################################
    def getOpensslVersion(self):
        printDBG("IPTVSetupImpl.getOpensslVersion")
        self.setInfo(_("Detection of the OpenSSL version."), _("OpenSSL lib is needed by wget and rtmpdump utilities."))
        
        def _verValidator(code, data):
            if code == 0: 
                return True,False
            else: 
                return False,True
        verCmdTab = []
        verCmdTab.append('openssl version -a')
        self.workingObj = CCmdValidator(self.getOpensslVersionFinished, _verValidator, verCmdTab)
        self.workingObj.start()
        
    def getOpensslVersionFinished(self, stsTab, dataTab):
        printDBG("IPTVSetupImpl.getOpensslVersionFinished")
        if len(stsTab) > 0 and True == stsTab[-1]:
            for ver in ['0.9.8', '1.0.0', '1.0.2']:
                if ver in dataTab[-1]:
                    self.openSSLVersion = '.' + ver
                    break
        
        if self.openSSLVersion == '':
            # use old detection manner
            self.setOpenSSLVersion()
        else:
            self.getGstreamerVer()
    
    def setOpenSSLVersion(self, ret=None):
        printDBG('Check opennSSL version')
        self.setInfo(_("Detection of the OpenSSL version."), _("OpenSSL lib is needed by wget and rtmpdump utilities."))
        for ver in ['.0.9.8', '.1.0.0']:
            libsslExist = False
            libcryptoExist = False
            libSSLPath = ''
            for path in ['/usr/lib/', '/lib/', '/usr/local/lib/', '/local/lib/', '/lib/i386-linux-gnu/']:
                try:
                    filePath = path + 'libssl.so' + ver
                    if os_path.isfile(filePath) and not os_path.islink(filePath):
                        libsslExist = True
                        libSSLPath = filePath
                    filePath = path + 'libcrypto.so' + ver
                    if os_path.isfile(filePath) and not os_path.islink(filePath):
                        libcryptoExist = True
                    if libsslExist and libcryptoExist:
                        break
                except Exception:
                    printExc()
                    continue
            if libsslExist and libcryptoExist:
                break
        if libsslExist and libcryptoExist:
            self.openSSLVersion = ver
            self.libSSLPath = libSSLPath
            if '.1.0.0' != ver:
                # old ssl version 0.9.8
                self.getGstreamerVer()
            else:
                # we need check if 1.0.0 it is real 1.0.0 version with OPENSSL_1.0.0 symbol
                # or new version without this symbol
                self.getOpenssl1Ver()
        else:
            self.openSSLVersion = ""
            self.showMessage(_("Fatal Error!\nOpenssl could not be found. Please install it and retry."), MessageBox.TYPE_ERROR, boundFunction(self.finish, False) )
            
    ###################################################
    # STEP: CHECK OPENSSL 1.0.0 VERSION
    ###################################################
    def getOpenssl1Ver(self):
        printDBG("IPTVSetupImpl.getOpenssl1Ver")
        self.setInfo(_("Detection of the OpenSSL 1.0.0 version."), None)
        
        def _verValidator(code, data):
            if '1.0.0' in data: 
                return True,False
            else: 
                return False,True
        verCmdTab = []
        verCmdTab.append('grep OPENSSL_1.0.0 "%s"' % self.libSSLPath)
        self.workingObj = CCmdValidator(self.getOpenssl1Finished, _verValidator, verCmdTab)
        self.workingObj.start()
        
    def getOpenssl1Finished(self, stsTab, dataTab):
        printDBG("IPTVSetupImpl.getOpenssl1Finished")
        if len(stsTab) == 0 or False == stsTab[-1]:
            # we detect new version OpenSSL without symbol OPENSSL_1.0.0
            self.openSSLVersion = '.1.0.2'
            self.libSSLPath = ""
            # we already we have packages for OpenSSL 1.0.2 for all supported platforms
            #if self.platform != 'mipsel':
            #    self.showMessage(_("OpenSSL in your image is not supported.\nSome functions may not work correctly."), MessageBox.TYPE_WARNING, self.getGstreamerVer )
            #    return
        self.getGstreamerVer()
        
    ###################################################
    # STEP: GSTREAMER VERSION
    ###################################################
    def getGstreamerVer(self, arg=None):
        printDBG("IPTVSetupImpl.getGstreamerVer >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>> [%s]" % os_getpid())
        self.setInfo(_("Detection of the gstreamer version."), None)
        def _verValidator(code, data):
            if 'libgstbase-' in data: 
                return True,False
            elif 'GStreamer Core Library version ' in data: 
                return True,False
            else: 
                return False,True
        verCmdTab = []
        verCmdTab.append('cat /proc/%s/maps | grep libgst' % os_getpid())
        verCmdTab.append('gst-launch-1.0 --gst-version')
        verCmdTab.append('gst-launch --gst-version')
        self.workingObj = CCmdValidator(self.getGstreamerVerFinished, _verValidator, verCmdTab)
        self.workingObj.start()
        
    def getGstreamerVerFinished(self, stsTab, dataTab):
        printDBG("IPTVSetupImpl.getGstreamerVerFinished")
        if len(stsTab) > 0 and True == stsTab[-1]:
            if 'libgstbase-1.0.so' in dataTab[-1]:
                self.gstreamerVersion = "1.0"
            elif 'libgstbase-0.10.so' in dataTab[-1]:
                self.gstreamerVersion = "0.10"
            elif ' version 1.' in dataTab[-1]:
                self.gstreamerVersion = "1.0"
            elif ' version 0.' in dataTab[-1]:
                self.gstreamerVersion = "0.10"
            else: 
                self.gstreamerVersion = ""
        else: self.gstreamerVersion = ""
        self.getFFmpegVer()
        
    ###################################################
    # STEP: GSTREAMER VERSION
    ###################################################
    def getFFmpegVer(self):
        printDBG("IPTVSetupImpl.getFFmpegVer")
        self.setInfo(_("Detection of the ffmpeg version."), None)
        def _verValidator(code, data):
            if 0 == code: return True,False
            else: return False,True
        self.workingObj = CCmdValidator(self.getFFmpegVerFinished, _verValidator, ['ffmpeg -version'])
        self.workingObj.start()
        
    def getFFmpegVerFinished(self, stsTab, dataTab):
        printDBG("IPTVSetupImpl.getFFmpegVerFinished")
        if len(stsTab) > 0 and True == stsTab[-1]:
            try: 
                self.ffmpegVersion = re.search("ffmpeg version ([0-9.]+?)[^0-9^.]", dataTab[-1]).group(1)
                if '.' == self.ffmpegVersion[-1]: self.ffmpegVersion = self.ffmpegVersion[:-1]
            except Exception: self.ffmpegVersion = ""
        else: self.ffmpegVersion = ""
        self.wgetStep()
            
    ###################################################
    # STEP: WGET
    ###################################################
    def wgetStep(self, ret=None):
        printDBG("IPTVSetupImpl.wgetStep")
        def _detectValidator(code, data):
            if 'BusyBox' not in data and '+https' in data: 
                try: ver = int(re.search("GNU Wget 1\.([0-9]+?)[^0-9]", data).group(1))
                except Exception: ver = 0
                if ver >= self.wgetVersion: return True,False
            return False,True
        def _deprecatedHandler(paths, stsTab, dataTab):
            sts, retPath = False, ""
            for idx in range(len(dataTab)):
                if 'BusyBox' not in dataTab[idx] and '+https' in dataTab[idx]: sts, retPath = True, paths[idx]
            return sts, retPath
        
        self.stepHelper = CBinaryStepHelper("wget", self.platform, self.openSSLVersion, config.plugins.iptvplayer.wgetpath)
        self.stepHelper.updateMessage('detection', (_('The "%s" utility is used by the IPTVPlayer to buffering and downloading [%s] links.') % ('wget', 'http, https, f4m, uds, hls')), 1)
        self.stepHelper.setInstallChoiseList( self._wgetInstallChoiseList )
        self.stepHelper.setPaths( self.wgetpaths )
        self.stepHelper.setDetectCmdBuilder( lambda path: path + " -V 2>&1 " )
        self.stepHelper.setDetectValidator( _detectValidator )
        self.stepHelper.setDeprecatedHandler( _deprecatedHandler )
        self.stepHelper.setFinishHandler( self.wgetStepFinished )
        self.binaryDetect()

    def wgetStepFinished(self, sts, ret=None):
        printDBG("IPTVSetupImpl.wgetStepFinished sts[%r]" % sts)
        self.rtmpdumpStep()
        
    ###################################################
    # STEP: RTMPDUMP
    ###################################################
    def rtmpdumpStep(self, ret=None):
        printDBG("IPTVSetupImpl.rtmpdumpStep")
        def _detectValidator(code, data):
            if self.rtmpdumpVersion.get(self.platform, self.rtmpdumpVersion['default']) in data: return True,False
            else: return False,True
        def _deprecatedHandler(paths, stsTab, dataTab):
            sts, retPath = False, ""
            for idx in range(len(dataTab)):
                if 'RTMPDump v2.4' in dataTab[idx]: sts, retPath = True, paths[idx]
            return sts, retPath
        def _downloadCmdBuilder(binName, platform, openSSLVersion, server, tmpPath):
            url = server + ('rtmpdump_%s_libssl.so%s.tar.gz' % (platform, openSSLVersion))
            tmpFile = tmpPath + 'rtmpdump.tar.gz' 
            cmd = SetupDownloaderCmdCreator(url, tmpFile) + ' > /dev/null 2>&1'
            return cmd
        def _installCmdBuilder(binName, binaryInstallPath, tmpPath):
            sourceArchive = tmpPath + 'rtmpdump.tar.gz'         
            cmd = 'tar -xzf "%s" -C / 2>&1' % sourceArchive
            return cmd
            
        self.stepHelper = CBinaryStepHelper("rtmpdump", self.platform, self.openSSLVersion, config.plugins.iptvplayer.rtmpdumppath)
        self.stepHelper.updateMessage('detection', (_('The "%s" utility is used by the IPTVPlayer to buffering and downloading [%s] links.') % ('rtmpdump', 'rtmp, rtmpt, rtmpe, rtmpte, rtmps')), 1)
        self.stepHelper.setInstallChoiseList( [('rtmpdump', '/usr/bin/rtmpdump')] )
        self.stepHelper.setPaths( self.rtmpdumppaths )
        self.stepHelper.setDetectCmdBuilder( lambda path: path + " -V 2>&1 " )
        self.stepHelper.setDetectValidator( _detectValidator )
        self.stepHelper.setDeprecatedHandler( _deprecatedHandler )
        self.stepHelper.setDownloadCmdBuilder( _downloadCmdBuilder )
        self.stepHelper.setInstallCmdBuilder( _installCmdBuilder )
        self.stepHelper.setFinishHandler( self.rtmpdumpStepFinished )
        self.binaryDetect()

    def rtmpdumpStepFinished(self, sts, ret=None):
        printDBG("IPTVSetupImpl.rtmpdumpStepFinished sts[%r]" % sts)
        self.uchardetStep()
        
    ###################################################
    # STEP: uchardet
    ###################################################
    def uchardetStep(self, ret=None):
        printDBG("IPTVSetupImpl.uchardetStep")
        self.binaryInstalledSuccessfully = False
        def _detectValidator(code, data):
            if self.binaryInstalledSuccessfully: self.stepHelper.setInstallChoiseList( self._uchardetInstallChoiseList2 )
            else: self.stepHelper.setInstallChoiseList( self._uchardetInstallChoiseList )
            try: 
                rawVer = re.search("Version\s([0-9])\.([0-9])\.([0-9])", data)
                UCHARDET_VERSION_MAJOR     = int(rawVer.group(1))
                UCHARDET_VERSION_MINOR     = int(rawVer.group(2))
                UCHARDET_VERSION_REVISION  = int(rawVer.group(3))
                if (UCHARDET_VERSION_MAJOR > self.uchardetVersion[0]) or \
                   (UCHARDET_VERSION_MAJOR == self.uchardetVersion[0] and UCHARDET_VERSION_MINOR > self.uchardetVersion[1]) or \
                   (UCHARDET_VERSION_MAJOR == self.uchardetVersion[0] and UCHARDET_VERSION_MINOR == self.uchardetVersion[1] and UCHARDET_VERSION_REVISION >= self.uchardetVersion[2]):
                    return True,False
            except Exception:
                printExc()
            return False,True
        def _deprecatedHandler(paths, stsTab, dataTab):
            sts, retPath = False, ""
            for idx in range(len(dataTab)):
                if 'Author: BYVoid' in dataTab[idx]: sts, retPath = True, paths[idx]
            return sts, retPath
        def _downloadCmdBuilder(binName, platform, openSSLVersion, server, tmpPath):
            if self.binaryInstalledSuccessfully:
                url = server + 'bin/' + platform + ('/%s' % binName) + '_static_libstdc++'
                self.binaryInstalledSuccessfully = False
            else: url = server + 'bin/' + platform + ('/%s' % binName)
                
            tmpFile = tmpPath + binName
            cmd = SetupDownloaderCmdCreator(url, tmpFile) + ' > /dev/null 2>&1'
            return cmd
            
        self.stepHelper = CBinaryStepHelper("uchardet", self.platform, self.openSSLVersion, config.plugins.iptvplayer.uchardetpath)
        self.stepHelper.updateMessage('detection', _('The "%s" utility is used by the IPTVPlayer to determine the encoding of the text.') % 'uchardet', 1)
        self.stepHelper.setInstallChoiseList( self._uchardetInstallChoiseList )
        self.stepHelper.setPaths( self.uchardetpaths )
        self.stepHelper.setDetectCmdBuilder( lambda path: path + " --version 2>&1 " )
        self.stepHelper.setDetectValidator( _detectValidator )
        self.stepHelper.setDownloadCmdBuilder( _downloadCmdBuilder )
        self.stepHelper.setDeprecatedHandler( _deprecatedHandler )
        self.stepHelper.setFinishHandler( self.uchardetStepFinished )
        self.binaryDetect()

    def uchardetStepFinished(self, sts, ret=None):
        printDBG("IPTVSetupImpl.uchardetStepFinished sts[%r]" % sts)
        self.subparserStep()
        
    ###################################################
    # STEP: subparser
    ###################################################
    def subparserStep(self, ret=None):
        printDBG("IPTVSetupImpl.subparserStep")
        
        def _detectCmdBuilder(path):
            cmd = GetPyScriptCmd('subparserversion') + ' "%s" ' % resolveFilename(SCOPE_PLUGINS, 'Extensions/IPTVPlayer/libs/')
            return cmd
            
        def _detectValidator(code, data):
            if 0 == code:
                try: 
                    if float(data.strip()) >= self.subparserVersion:
                        return True,False
                except Exception: 
                    pass
            return False,True
        
        def _deprecatedHandler(paths, stsTab, dataTab):
            try: 
                ver = float(dataTab[0].strip())
                return True,self.subparserPaths[0]
            except Exception: 
                pass
            return False,""
        
        def _downloadCmdBuilder(binName, platform, openSSLVersion, server, tmpPath):
            url = server + 'bin/' + platform + ('/%s' % binName)
            if 'mipsel' == self.platform and IsFPUAvailable():
                url += '.fpu'
            tmpFile = tmpPath + binName
            cmd = SetupDownloaderCmdCreator(url, tmpFile) + ' > /dev/null 2>&1'
            return cmd
        
        self.stepHelper = CBinaryStepHelper("_subparser.so", self.platform, self.openSSLVersion, None)
        msg1 = _("C subtitle parser")
        msg2 = _("\nFor more info please ask the author samsamsam@o2.pl")
        msg3 = _('It improves subtitles parsing.\n')
        self.stepHelper.updateMessage('detection', msg1, 0)
        self.stepHelper.updateMessage('detection', msg2, 1)
        self.stepHelper.updateMessage('not_detected_2', msg1 + _(' has not been detected. \nDo you want to install it? ') + msg3 + msg2, 1)
        self.stepHelper.updateMessage('deprecated_2', msg1 + _(' is deprecated. \nDo you want to install new one? ') + msg3 + msg2, 1)
        
        self.stepHelper.setInstallChoiseList( [('_subparser.so', self.subparserPaths[0])] )
        self.stepHelper.setPaths( self.subparserPaths )
        self.stepHelper.setDetectCmdBuilder( _detectCmdBuilder )
        self.stepHelper.setDetectValidator( _detectValidator )
        self.stepHelper.setDownloadCmdBuilder( _downloadCmdBuilder )
        self.stepHelper.setDeprecatedHandler( _deprecatedHandler )
        self.stepHelper.setFinishHandler( self.subparserStepFinished )
        self.binaryDetect()
    
    def subparserStepFinished(self, sts, ret=None):
        printDBG("IPTVSetupImpl.subparserStepFinished sts[%r]" % sts)
        self.hlsdlStep()
    
    ###################################################
    # STEP: hlsdl
    ###################################################
    def hlsdlStep(self, ret=None):
        printDBG("IPTVSetupImpl.hlsdlStep")
        self.binaryInstalledSuccessfully = False
            
        def _detectValidator(code, data):
            if 'hlsdl v' in data:
                try:
                    tmp = re.search("hlsdl v([0-9.]+?)[^0-9^.]", data).group(1)
                    if float(tmp) >= self.hlsdlVersion:
                        return True,False
                except Exception:
                    printExc()
            return False,True
        
        def _deprecatedHandler(paths, stsTab, dataTab):
            sts, retPath = False, ""
            for idx in range(len(dataTab)):
                if 'hlsdl v' in dataTab[idx]: sts, retPath = True, paths[idx]
            return sts, retPath
        
        def _downloadCmdBuilder(binName, platform, openSSLVersion, server, tmpPath):
            old = ''
            versions = {'sh4':2190, 'mipsel':2200}
            
            if platform in ['sh4', 'mipsel'] and (self.binaryInstalledSuccessfully or self.glibcVersion < versions[platform] ):
                old = '_old'
            
            if old == '' and platform == 'mipsel' and not IsFPUAvailable():
                old = '_softfpu'
            
            url = server + 'bin/' + platform + ('/%s%s' % (binName, old)) + '_static_curl_openssl' + openSSLVersion
            if self.binaryInstalledSuccessfully:
                self.binaryInstalledSuccessfully = False
                
            tmpFile = tmpPath + binName
            cmd = SetupDownloaderCmdCreator(url, tmpFile) + ' > /dev/null 2>&1'
            return cmd
        
        self.stepHelper = CBinaryStepHelper("hlsdl", self.platform, self.openSSLVersion, config.plugins.iptvplayer.hlsdlpath)
        msg1 = _("hlsdl downloader")
        msg2 = _("\nFor more info please ask samsamsam@o2.pl")
        msg3 = _('It improves HLS/M3U8 stream download.\n')
        self.stepHelper.updateMessage('detection', msg1, 0)
        self.stepHelper.updateMessage('detection', msg2, 1)
        self.stepHelper.updateMessage('not_detected_2', msg1 + _(' has not been detected. \nDo you want to install it? ') + msg3 + msg2, 1)
        self.stepHelper.updateMessage('deprecated_2', msg1 + _(' is deprecated. \nDo you want to install new one? ') + msg3 + msg2, 1)
        
        self.stepHelper.setInstallChoiseList( [('hlsdl', self.hlsdlPaths[0])] )
        self.stepHelper.setPaths( self.hlsdlPaths )
        self.stepHelper.setDetectCmdBuilder( lambda path: path + " 2>&1 " )
        self.stepHelper.setDetectValidator( _detectValidator )
        self.stepHelper.setDownloadCmdBuilder( _downloadCmdBuilder )
        self.stepHelper.setDeprecatedHandler( _deprecatedHandler )
        self.stepHelper.setFinishHandler( self.hlsdlStepFinished )
        self.binaryDetect()
    
    def hlsdlStepFinished(self, sts, ret=None):
        printDBG("IPTVSetupImpl.hlsdlStepFinished sts[%r]" % sts)
        self.f4mdumpStep()
        
    ###################################################
    # STEP: F4MDUMP
    ###################################################
    def f4mdumpStep(self, ret=None):
        printDBG("IPTVSetupImpl.f4mdumpStep")
        self.binaryInstalledSuccessfully = False
        def _detectValidator(code, data):
            if self.binaryInstalledSuccessfully: self.stepHelper.setInstallChoiseList( self._f4mdumpInstallChoiseList2 )
            else: self.stepHelper.setInstallChoiseList( self._f4mdumpInstallChoiseList )
            if 'F4MDump v' in data:
                try:
                    tmp = re.search("F4MDump v([0-9.]+?)[^0-9^.]", data).group(1)
                    if float(tmp) >= self.f4mdumpVersion:
                        return True,False
                except Exception:
                    printExc()
            return False,True
        def _deprecatedHandler(paths, stsTab, dataTab):
            sts, retPath = False, ""
            for idx in range(len(dataTab)):
                if 'F4MDump v' in dataTab[idx]: sts, retPath = True, paths[idx]
            return sts, retPath
        def _downloadCmdBuilder(binName, platform, openSSLVersion, server, tmpPath):
            if self.binaryInstalledSuccessfully:
                url = server + 'bin/' + platform + ('/%s_openssl' % binName) + openSSLVersion + '_static_libstdc++'
                self.binaryInstalledSuccessfully = False
            else: url = server + 'bin/' + platform + ('/%s_openssl' % binName) + openSSLVersion
                
            tmpFile = tmpPath + binName
            cmd = SetupDownloaderCmdCreator(url, tmpFile) + ' > /dev/null 2>&1'
            return cmd
            
        self.stepHelper = CBinaryStepHelper("f4mdump", self.platform, self.openSSLVersion, config.plugins.iptvplayer.f4mdumppath)
        self.stepHelper.updateMessage('detection', (_('The "%s" utility is used by the IPTVPlayer to buffering and downloading [%s] links.') % ('f4mdump', 'f4m, uds')), 1)
        self.stepHelper.setInstallChoiseList( self._f4mdumpInstallChoiseList )
        self.stepHelper.setPaths( self.f4mdumppaths )
        self.stepHelper.setDetectCmdBuilder( lambda path: path + " 2>&1 " )
        self.stepHelper.setDetectValidator( _detectValidator )
        self.stepHelper.setDownloadCmdBuilder( _downloadCmdBuilder )
        self.stepHelper.setDeprecatedHandler( _deprecatedHandler )
        self.stepHelper.setFinishHandler( self.f4mdumpStepFinished )
        self.binaryDetect()

    def f4mdumpStepFinished(self, sts, ret=None):
        printDBG("IPTVSetupImpl.f4mdumpStepFinished sts[%r]" % sts)
        shortFFmpegVersion = self.ffmpegVersion
        if len(self.ffmpegVersion) >= 5:
            shortFFmpegVersion = self.ffmpegVersion[:-2]
            
        if self.platform in ['sh4'] and shortFFmpegVersion in ['1.0', '1.1', '1.2', '2.0', '2.2', '2.5', '2.6', '2.7', '2.8', '3.0', '3.1', '3.2']: 
            self.ffmpegVersion = shortFFmpegVersion
            self.exteplayer3Step()
        elif self.platform in ['mipsel'] and shortFFmpegVersion in ['2.8', '3.0', '3.1', '3.2']:
            self.ffmpegVersion = shortFFmpegVersion
            self.exteplayer3Step()
        elif self.platform in ['armv7'] and shortFFmpegVersion in ['2.8', '3.0', '3.1', '3.2']:
            self.ffmpegVersion = shortFFmpegVersion
            self.exteplayer3Step()
        elif self.platform in ['armv5t'] and shortFFmpegVersion in ['2.8', '3.0', '3.1', '3.2']:
            self.ffmpegVersion = shortFFmpegVersion
            self.exteplayer3Step()
        elif "" != self.gstreamerVersion: self.gstplayerStep()
        else: self.finish()
    # self.ffmpegVersion
    ###################################################
    # STEP: exteplayer3
    ###################################################
    def exteplayer3Step(self, ret=None):
        printDBG("IPTVSetupImpl.exteplayer3Step")
        def _detectValidator(code, data):
            if '{"EPLAYER3_EXTENDED":{"version":' in data: 
                try: ver = int(re.search('"version":([0-9]+?)[^0-9]', data).group(1))
                except Exception: ver = 0
                if ver >= self.exteplayer3Version.get(self.platform, 0): return True,False
            return False,True
        def _deprecatedHandler(paths, stsTab, dataTab):
            sts, retPath = False, ""
            for idx in range(len(dataTab)):
                if '{"EPLAYER3_EXTENDED":{"version":' in dataTab[idx]: sts, retPath = True, paths[idx]
            return sts, retPath
        def _downloadCmdBuilder(ffmpegVersion, binName, platform, openSSLVersion, server, tmpPath):
            url = server + 'bin/' + platform + ('/%s_ffmpeg' % binName) + ffmpegVersion
            tmpFile = tmpPath + binName
            cmd = SetupDownloaderCmdCreator(url, tmpFile) + ' > /dev/null 2>&1'
            return cmd
        self.stepHelper = CBinaryStepHelper("exteplayer3", self.platform, self.openSSLVersion, config.plugins.iptvplayer.exteplayer3path)
        self.stepHelper.updateMessage('detection', _('The "%s" utility is used by the IPTVPlayer as external movie player based on the ffmpeg and libeplayer.') % ('exteplayer3'), 1)
        self.stepHelper.setInstallChoiseList( self._exteplayer3InstallChoiseList )
        self.stepHelper.setPaths( self.exteplayer3paths )
        self.stepHelper.setDetectCmdBuilder( lambda path: path + " 2>&1 " )
        self.stepHelper.setDetectValidator( _detectValidator )
        self.stepHelper.setDownloadCmdBuilder( boundFunction(_downloadCmdBuilder, self.ffmpegVersion) )
        self.stepHelper.setDeprecatedHandler( _deprecatedHandler )
        self.stepHelper.setFinishHandler( self.exteplayer3StepFinished )
        self.binaryDetect()

    def exteplayer3StepFinished(self, sts, ret=None):
        printDBG("IPTVSetupImpl.exteplayer3StepFinished sts[%r]" % sts)
        if "" != self.gstreamerVersion: self.gstplayerStep()
        else: self.finish()
    
    ###################################################
    # STEP: GSTPLAYER
    ###################################################
    def gstplayerStep(self, ret=None):
        printDBG("IPTVSetupImpl.gstplayerStep")
        if self.gstreamerVersion == "0.10" and self.platform in ['armv5t']:
            printDBG('Skip gstplayer 0.10 step installation - no binary for armv5t platform')
            self.gstplayerStepFinished(False)
        else:
            def _detectValidator(code, data):
                if '{"GSTPLAYER_EXTENDED":{"version":' in data: 
                    try: ver = int(re.search('"version":([0-9]+?)[^0-9]', data).group(1))
                    except Exception: ver = 0
                    if '0.10' != self.gstreamerVersion or ver < 10000:
                        if ver >= self.gstplayerVersion.get(self.gstreamerVersion, 0): 
                            return True,False
                return False,True
            def _deprecatedHandler(paths, stsTab, dataTab):
                sts, retPath = False, ""
                for idx in range(len(dataTab)):
                    if '{"GSTPLAYER_EXTENDED":{"version":' in dataTab[idx]: sts, retPath = True, paths[idx]
                return sts, retPath
            def _downloadCmdBuilder(binName, platform, openSSLVersion, server, tmpPath):
                url = server + 'bin/' + platform + ('/%s_gstreamer' % binName) + self.gstreamerVersion
                tmpFile = tmpPath + binName
                cmd = SetupDownloaderCmdCreator(url, tmpFile) + ' > /dev/null 2>&1'
                return cmd
            self.stepHelper = CBinaryStepHelper("gstplayer", self.platform, self.openSSLVersion, config.plugins.iptvplayer.gstplayerpath)
            self.stepHelper.updateMessage('detection', _('The "%s" utility is used by the IPTVPlayer as external movie player.') % ('gstplayer'), 1)
            self.stepHelper.setInstallChoiseList( self._gstplayerInstallChoiseList )
            self.stepHelper.setPaths( self.gstplayerpaths )
            self.stepHelper.setDetectCmdBuilder( lambda path: path + " 2>&1 " )
            self.stepHelper.setDetectValidator( _detectValidator )
            self.stepHelper.setDownloadCmdBuilder( _downloadCmdBuilder )
            self.stepHelper.setDeprecatedHandler( _deprecatedHandler )
            self.stepHelper.setFinishHandler( self.gstplayerStepFinished )
            self.binaryDetect()

    def gstplayerStepFinished(self, sts, ret=None):
        printDBG("IPTVSetupImpl.gstplayerStepFinished sts[%r]" % sts)
        if sts:
            if '0.10' == self.gstreamerVersion:
                self.flumpegdemuxStep()
            else: 
                self.gstifdsrcStep()
        else:
            self.finish()
        
    ###################################################
    # STEP: FLUENDO MPEGDEMUX
    ###################################################
    def flumpegdemuxStep(self, ret=None):
        printDBG("IPTVSetupImpl.flumpegdemuxStep")
        def _detectValidator(code, data):
            # some grep return code 1 even if the pattern has been found  and printed
            if 0 == code or self.flumpegdemuxVersion in data: return True,False
            return False,True
        def _deprecatedHandler(paths, stsTab, dataTab):
            sts, retPath = False, ""
            try: currentSize = os_path.getsize(self.flumpegdemuxpaths[0])
            except Exception: currentSize = -1
            if -1 < currentSize: sts, retPath = True, paths[0]
            return sts, retPath
        def _downloadCmdBuilder(binName, platform, openSSLVersion, server, tmpPath):
            url = server + 'bin/' + platform + ('/%s_gstreamer' % binName) + "0.10"
            tmpFile = tmpPath + binName
            cmd = SetupDownloaderCmdCreator(url, tmpFile) + ' > /dev/null 2>&1'
            return cmd
        self.stepHelper = CBinaryStepHelper("libgstflumpegdemux.so", self.platform, self.openSSLVersion, None)
        msg1 = _("Fluendo mpegdemux for GSTREAMER 0.10")
        msg2 = _("\nFor more info please visit http://fluendo.com/")
        msg3 = _('It improves playing of streams hls/m3u8.\n')
        self.stepHelper.updateMessage('detection', msg1, 0)
        self.stepHelper.updateMessage('detection', msg2, 1)
        self.stepHelper.updateMessage('not_detected_2', msg1 + _(' has not been detected. \nDo you want to install it? ') + msg3 + msg2, 1)
        self.stepHelper.updateMessage('deprecated_2', msg1 + _(' is deprecated. \nDo you want to install new one? ') + msg3 + msg2, 1)
        
        self.stepHelper.setInstallChoiseList( [('gst-fluendo-mpegdemux', self.flumpegdemuxpaths[0])] )
        self.stepHelper.setPaths( self.flumpegdemuxpaths )
        self.stepHelper.setDetectCmdBuilder( lambda path: ('grep "%s" "%s" 2>&1 ' % (self.flumpegdemuxVersion, path)) )
        self.stepHelper.setDetectValidator( _detectValidator )
        self.stepHelper.setDownloadCmdBuilder( _downloadCmdBuilder )
        self.stepHelper.setDeprecatedHandler( _deprecatedHandler )
        self.stepHelper.setFinishHandler( self.flumpegdemuxStepFinished )
        self.binaryDetect()
        
    def flumpegdemuxStepFinished(self, sts, ret=None):
        printDBG("IPTVSetupImpl.flumpegdemuxStepFinished sts[%r]" % sts)
        self.finish()
    
    ###################################################
    # STEP: GST IFDSRC
    ###################################################
    def gstifdsrcStep(self, ret=None):
        printDBG("IPTVSetupImpl.gstifdsrcStep")
        def _detectValidator(code, data):
            # some grep return code 1 even if the pattern has been found  and printed
            if 0 == code or self.gstifdsrcVersion in data: return True,False
            return False,True
        def _deprecatedHandler(paths, stsTab, dataTab):
            sts, retPath = False, ""
            try: currentSize = os_path.getsize(self.gstifdsrcPaths[0])
            except Exception: currentSize = -1
            if -1 < currentSize: sts, retPath = True, paths[0]
            return sts, retPath
        def _downloadCmdBuilder(binName, platform, openSSLVersion, server, tmpPath):
            url = server + 'bin/' + platform + ('/%s_gstreamer' % binName) + "1.0"
            tmpFile = tmpPath + binName
            cmd = SetupDownloaderCmdCreator(url, tmpFile) + ' > /dev/null 2>&1'
            return cmd
        self.stepHelper = CBinaryStepHelper("libgstifdsrc.so", self.platform, self.openSSLVersion, None)
        msg1 = _("GST-IFDSRC for GSTREAMER 1.X")
        msg2 = _("\nFor more info please ask the author samsamsam@o2.pl")
        msg3 = _('It improves buffering mode with the gstplayer.\n')
        self.stepHelper.updateMessage('detection', msg1, 0)
        self.stepHelper.updateMessage('detection', msg2, 1)
        self.stepHelper.updateMessage('not_detected_2', msg1 + _(' has not been detected. \nDo you want to install it? ') + msg3 + msg2, 1)
        self.stepHelper.updateMessage('deprecated_2', msg1 + _(' is deprecated. \nDo you want to install new one? ') + msg3 + msg2, 1)
        
        self.stepHelper.setInstallChoiseList( [('gst-ifdsrc', self.gstifdsrcPaths[0])] )
        self.stepHelper.setPaths( self.gstifdsrcPaths )
        self.stepHelper.setDetectCmdBuilder( lambda path: ('grep "%s" "%s" 2>&1 ' % (self.gstifdsrcVersion, path)) )
        self.stepHelper.setDetectValidator( _detectValidator )
        self.stepHelper.setDownloadCmdBuilder( _downloadCmdBuilder )
        self.stepHelper.setDeprecatedHandler( _deprecatedHandler )
        self.stepHelper.setFinishHandler( self.gstifdsrcStepFinished )
        self.binaryDetect()

    def gstifdsrcStepFinished(self, sts, ret=None):
        printDBG("IPTVSetupImpl.gstifdsrcStepFinished sts[%r]" % sts)
        self.finish()

    ###################################################
    ###################################################
    ###################################################
        
    ###################################################
    # STEP: SEARCHING FOR binary
    ###################################################
    def binaryDetect(self, ret=None):
        printDBG("IPTVSetupImpl.binaryDetect")
        self.setInfoFromStepHelper('detection')
        self.workingObj = CCmdValidator(self.binaryDetectFinished, self.stepHelper.getDetectValidator(), self.stepHelper.getDetectCmds())
        self.workingObj.start()
        
    def binaryDetectFinished(self, stsTab, dataTab):
        printDBG("IPTVSetupImpl.binaryDetectFinished")
        
        if len(stsTab) > 0 and True == stsTab[-1]:
            path = self.stepHelper.getPaths()[len(stsTab)-1]
            self.stepHelper.getSaveConfigOptionHandler()( self.stepHelper.getConfigOption(), path )
            # NEXT STEP
            if self.stepHelper.isDebugMessagesAllowed():
                self.showMessage(_("[%s] will be used by IPTVPlayer.") % path, MessageBox.TYPE_INFO, self.finish)
            else:
                self.stepHelper.getFinishHandler()(True)
        else:
            path = ""
            sts = False
            if 0 < len(dataTab) and None != self.stepHelper.getDeprecatedHandler():
                sts,path = self.stepHelper.getDeprecatedHandler()(self.stepHelper.getPaths(), stsTab, dataTab)
            self.stepHelper.getSaveConfigOptionHandler()( self.stepHelper.getConfigOption(), path )
            installChoiseList = self.stepHelper.getInstallChoiseList()
            if 1 < len(installChoiseList):
                if not sts: message = self.stepHelper.getMessage('not_detected_1', 1)
                else: message = message = self.stepHelper.getMessage('deprecated_1', 1)
                self.chooseQuestion(message, installChoiseList, self.binaryDownload_1)
            elif 1 == len(installChoiseList):
                if not sts: message = self.stepHelper.getMessage('not_detected_2', 1)
                else: message = message = self.stepHelper.getMessage('deprecated_2', 1)
                self.showMessage(message, MessageBox.TYPE_YESNO, self.binaryDownload_2)
            else:
                self.stepHelper.getFinishHandler()(False)
    ###################################################
    # STEP: binary DOWNLOAD
    ###################################################
    def binaryDownload(self):
        self.setInfoFromStepHelper('download')
        cmdTabs = []
        for server in self.resourceServers:
            cmd = self.stepHelper.getDownloadCmdBuilder()(self.stepHelper.getName(), self.platform, self.openSSLVersion, server, self.tmpDir)
            cmdTabs.append(cmd)
        self.workingObj = CCmdValidator(self.binaryDownloadFinished, self.stepHelper.getDownloadValidator(), cmdTabs)
        self.workingObj.start()
    
    def binaryDownload_1(self, ret=None):
        printDBG("IPTVSetupImpl.binaryDownload_1")
        if ret: self._binaryInstallPath = ret[1]
        else: self._binaryInstallPath = ""
        if "" != self._binaryInstallPath: self.binaryDownload()
        else: self.stepHelper.getFinishHandler()(False)
        
    def binaryDownload_2(self, ret=None):
        printDBG("IPTVSetupImpl.binaryDownload_2")
        if ret:
            self._binaryInstallPath = self.stepHelper.getInstallChoiseList()[0][1]
            self.binaryDownload()
        else:
            self._binaryInstallPath = ""
            self.stepHelper.getFinishHandler()(False)
        
    def binaryDownloadFinished(self, stsTab, dataTab):
        printDBG("IPTVSetupImpl.binaryDownloadFinished")
        if len(stsTab) > 0 and True == stsTab[-1]:
            # NEXT STEP
            self.binaryInstall()
        else: self.showMessage(self.stepHelper.getMessage('dwn_failed', 1), MessageBox.TYPE_YESNO, self.binaryDownloadRetry)
            
    def binaryDownloadRetry(self, ret=None):
        printDBG("IPTVSetupImpl.binaryDownloadRetry")
        if ret: self.binaryDetect()
        else: self.stepHelper.getFinishHandler()(False)
            
    ###################################################
    # STEP: binary Install
    ###################################################
    def binaryInstall(self, ret=None):
        printDBG("IPTVSetupImpl.binaryInstall")
        self.setInfoFromStepHelper('install')
        cmd = self.stepHelper.getInstallCmdBuilder()(self.stepHelper.getName(), self._binaryInstallPath, self.tmpDir)
        self.workingObj = CCmdValidator(self.binaryInstallFinished, self.stepHelper.getInstallValidator(), [cmd])
        self.workingObj.start()
        
    def binaryInstallFinished(self, stsTab, dataTab):
        printDBG("IPTVSetupImpl.binaryInstallFinished")
        if len(stsTab) > 0 and True == stsTab[-1]:
            self.binaryInstalledSuccessfully = True
            # NEXT STEP
            self.binaryDetect() # run detect step once again to make sure that installed binary will be detected
        else: self.showMessage(_("Installation binary failed. Retry?"), MessageBox.TYPE_YESNO, self.binaryInstallRetry)
        
    def binaryInstallRetry(self, ret=None):
        printDBG("IPTVSetupImpl.binaryInstallRetry")
        if ret: self.binaryInstall()
        else: self.stepHelper.getFinishHandler()(False)