import PyInstaller.__main__
import os
import shutil

PyInstaller.__main__.run([
    '--name=%s' % "AstroLauncher",
    '--onefile',
    '--add-data=%s' % "assets/*;.",
    '--icon=%s' % "assets/astrolauncherlogo.ico",
    'AstroLauncher.py'
])

shutil.rmtree("build")
os.remove("AstroLauncher.spec")
