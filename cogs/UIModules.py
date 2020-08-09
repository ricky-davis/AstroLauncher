

import os

import tornado.web

# pylint: disable=arguments-differ


class ConsoleModule(tornado.web.UIModule):
    def render(self, launcher, isAdmin):
        return self.render_string(
            os.path.join(self.handler.application.assetDir, "uimodules", "console.html"), launcher=launcher, isAdmin=isAdmin)


class StatsModule(tornado.web.UIModule):
    def render(self, launcher, isAdmin):
        return self.render_string(
            os.path.join(self.handler.application.assetDir, "uimodules", "stats.html"), launcher=launcher, isAdmin=isAdmin)


class SaveGamesModule(tornado.web.UIModule):
    def render(self, launcher, isAdmin):
        return self.render_string(
            os.path.join(self.handler.application.assetDir, "uimodules", "saveGames.html"), launcher=launcher, isAdmin=isAdmin)


class PlayersModule(tornado.web.UIModule):
    def render(self, launcher, isAdmin, ptype):
        return self.render_string(
            os.path.join(self.handler.application.assetDir, "uimodules", "players.html"), launcher=launcher, isAdmin=isAdmin, ptype=ptype)


class WhitelistPlayersModule(tornado.web.UIModule):
    def render(self, launcher, isAdmin):
        return self.render_string(
            os.path.join(self.handler.application.assetDir, "uimodules", "whitelistPlayers.html"), launcher=launcher, isAdmin=isAdmin)


class HeadModule(tornado.web.UIModule):
    def render(self, launcher, isAdmin):
        return self.render_string(
            os.path.join(self.handler.application.assetDir, "uimodules", "head.html"), launcher=launcher, isAdmin=isAdmin)


class BannerModule(tornado.web.UIModule):
    def render(self, launcher, isAdmin):
        return self.render_string(
            os.path.join(self.handler.application.assetDir, "uimodules", "banner.html"), launcher=launcher, isAdmin=isAdmin)


class ScriptsModule(tornado.web.UIModule):
    def render(self, launcher, isAdmin):
        return self.render_string(
            os.path.join(self.handler.application.assetDir, "uimodules", "scripts.html"), launcher=launcher, isAdmin=isAdmin)
