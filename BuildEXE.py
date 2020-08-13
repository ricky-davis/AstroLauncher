import os
import shutil

import PyInstaller.__main__

# pyinstaller AstroLauncher.py -F --add-data "assets/*;." --icon=assets/astrolauncherlogo.ico

PyInstaller.__main__.run([
    '--name=%s' % "AstroLauncher",
    '--onefile',
    '--add-data=%s' % "assets;./assets",
    '--icon=%s' % "assets/astrolauncherlogo.ico",
    'AstroLauncher.py'
])

shutil.rmtree("build")
os.remove("AstroLauncher.spec")
