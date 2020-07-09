

import os

import tornado.web

# pylint: disable=arguments-differ


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
