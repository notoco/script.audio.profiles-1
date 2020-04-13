# -*- coding: utf-8 -*-

import json, os, xbmc, xbmcaddon, xbmcvfs
import resources.lib.debug as debug

ADDON = xbmcaddon.Addon()
ADDON_ID = ADDON.getAddonInfo('id')
ADDON_PATH = xbmc.translatePath(ADDON.getAddonInfo('path'))
ADDON_PATH_DATA = xbmc.translatePath(os.path.join('special://profile/addon_data/', ADDON_ID)).replace('\\', '/') + '/'
ADDON_LANG = ADDON.getLocalizedString

profiles = ['1', '2', '3', '4']
map_type = {'movie': 'auto_movies', 'video': 'auto_videos', 'episode': 'auto_tvshows', 'channel': 'auto_pvr',
            'musicvideo': 'auto_musicvideo', 'song': 'auto_music', 'unknown': 'auto_unknown'}
susppend_auto_change = False
set_for_susspend = None


class Monitor(xbmc.Monitor):
    def __init__(self):
        xbmc.Monitor.__init__(self)

        # default for kodi start
        self.changeProfile(ADDON.getSetting('auto_default'))

    def onNotification(self, sender, method, data):
        global susppend_auto_change
        global set_for_susspend
        data = json.loads(data)

        if 'System.OnWake' in method:
            debug.debug("[MONITOR] METHOD: " + str(method) + " DATA: " + str(data))
            # default for kodi wakeup
            self.changeProfile(ADDON.getSetting('auto_default'))

        if 'Player.OnStop' in method:
            debug.debug("[MONITOR] METHOD: " + str(method) + " DATA: " + str(data))
            # gui
            susppend_auto_change = False
            self.changeProfile(ADDON.getSetting('auto_gui'))

        if 'Player.OnPlay' in method:
            debug.debug("[MONITOR] METHOD: " + str(method) + " DATA: " + str(data))
            # auto switch
            if 'item' in data and 'type' in data['item']:
                self.autoSwitch(data)

    def autoSwitch(self, data):
        global susppend_auto_change
        global set_for_susspend
        thetype = data['item']['type']
        theset = map_type.get(thetype)
        # auto show dialog
        if 'true' in ADDON.getSetting('player_show') and 'movie' in thetype and 'id' not in data['item']:
            xbmc.executebuiltin('XBMC.RunScript(' + ADDON_ID + ', popup)')

        # if video is not from library assign to auto_videos
        if 'movie' in thetype and 'id' not in data['item']:
            theset = 'auto_videos'

        # distinguish pvr TV and pvr RADIO
        if 'channel' in thetype and 'channeltype' in data['item']:
            if 'tv' in data['item']['channeltype']:
                theset = 'auto_pvr_tv'
            elif 'radio' in data['item']['channeltype']:
                theset = 'auto_pvr_radio'
            else:
                theset = None

        # detect cdda that kodi return as unknown
        if 'unknown' in thetype and 'player' in data and 'playerid' in data['player']:
            jsonS = xbmc.executeJSONRPC(
                '{"jsonrpc": "2.0", "id": "1", "method": "Player.GetItem", "params": {"playerid": ' + str(
                    data['player']['playerid']) + ', "properties": ["file"]}}')
            jsonR = json.loads(jsonS)
            try:
                file = jsonR['result']['item']['file']
            except (IndexError, KeyError, ValueError):
                file = ''
            if file.startswith('cdda://'):
                theset = 'auto_music'

        debug.debug("[MONITOR] Setting parsed: " + str(theset))

        # cancel susspend auto change when media thetype change
        if theset != set_for_susspend:
            susppend_auto_change = False
            set_for_susspend = set

        if theset is not None:
            self.changeProfile(ADDON.getSetting(theset))
            susppend_auto_change = True

    def changeProfile(self, profile):
        if profile in profiles:
            # get last loaded profile
            lastProfile = self.getLastProfile()
            debug.debug("[MONITOR] Last loaded profile: " + lastProfile + " To switch profile: " + profile)

            if lastProfile != profile and susppend_auto_change is not True:
                xbmc.executebuiltin('XBMC.RunScript(' + ADDON_ID + ', ' + profile + ')')
            else:
                debug.debug("[MONITOR] Switching omitted (same profile) or switching is susspend")

    def getLastProfile(self):
        try:
            f = xbmcvfs.File(ADDON_PATH_DATA + 'profile')
            p = f.read()
            f.close()
        except IOError:
            return ''
        if p in profiles:
            return p
        else:
            return ''