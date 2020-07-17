[![Contributors][contributors-shield]][contributors-url]
[![Forks][forks-shield]][forks-url]
[![Downloads][downloads-shield]][downloads-url]
[![Stargazers][stars-shield]][stars-url]
[![Issues][issues-shield]][issues-url]
[![MIT License][license-shield]][license-url]


<br />
<p align="center">
  <img src="https://raw.githubusercontent.com/ricky-davis/AstroLauncher/master/assets/astrolauncherlogo.ico" width="128px">
  <h3 align="center">AstroLauncher - Dedicated Server Launcher</h3>

  <p align="center">
    <a href="https://github.com/ricky-davis/AstroLauncher/issues">AstroLauncher Bugs</a>
    ·
    <a href="https://github.com/ricky-davis/AstroLauncher/issues">Request Feature</a>
  </p>
</p>

<!-- TABLE OF CONTENTS -->

## Table of Contents

- [Table of Contents](#table-of-contents)
- [Overview](#overview)
- [What does it do?](#what-does-it-do)
- [TODO](#todo)
- [INI File options](#ini-file-options)
- [Getting Started](#getting-started)
  - [Prerequisites](#prerequisites)
  - [Installation](#installation)
- [Usage](#usage)
  - [Building an EXE](#building-an-exe)
- [Contributing](#contributing)
- [License](#license)
- [Contact](#contact)

## Overview

This tool is perfect for you if you are hosting your own dedicated server for Astroneer. It has many features to make hosting a lot easier like automatic restarts, advanced logging, and a webinterface.

## What does it do?

1. Verifies your network settings to check for Port Forwarding/NAT Loopback
2. Automatically sets up the base Config files
3. Fixes the double server problem in the server list
4. Starts, and automatically restarts the server
5. Displays when users join/leave the server
6. Keeps a log of everything in the logs folder
7. Auto Restart every X hours
8. Backup Retention for X hours
9. Web Interface w/ login to monitor server data, force saves and restarts

## TODO

1. Build out Web Interface to have more management functions, including ban, kick, whitelist, and promote player


## INI File options

Below are the descriptions and defaults for the INI file options. Do not copy/paste this into the INI file, allow the INI file to be automatically generated. Every option must be present and set, and there must be no comments or extra options.
```python
# Disables Auto Update -- Notifies but does not download
DisableAutoUpdate = False

# Allows the launcher to autoUpdate every time the server restarts
UpdateOnServerRestart=True

# Disable the server console popup window.
HideServerConsoleWindow=False

# Disable the Launcher console popup window.
HideLauncherConsoleWindow=False

# Specifies how often the launcher will check for players joining/leaving
ServerStatusFrequency = 2

# Specifies how often the launcher will check for server registration status
PlayfabAPIFrequency = 2

# Disable Backup Retention
DisableBackupRetention = False

# How many hours of saves should the launcher retain
BackupRetentionPeriodHours= 76

# Location to backup the save files to
BackupRetentionFolderLocation = Astro\Saved\Backup\LauncherBackups

# Enable auto restart
EnableAutoRestart = False

# Timestamp you want to synchronize with. 00:00 or "midnight" work for midnight. Disable with "False". No quotes.
# Example: If set to 03:35, with AutoRestartEveryHours set to 6, it will restart at 03:35, 09:35, 15:35, and 21:35 every day
AutoRestartSyncTimestamp = 00:00

# After the first restart specified above, how often do you want to restart?
AutoRestartEveryHours = 24

# Disable the Port Forward / NAT Loopback check on startup
DisableNetworkCheck = False

# Enable/Disable showing server FPS in console. This will probably spam your console when playing are in your server
ShowServerFPSInConsole = True

# Disable the Web Management Server
DisableWebServer=False

# Set the port you want the Web Management Server to run on
WebServerPort=5000

# Automatically generated SHA256 password hash for the admin panel in the webserver
WebServerPasswordHash=

# Enable HTTPS for the webserver. If no/wrong Cert/Key files are specified, defaults to False
EnableWebServerSSL=False

# Port you want to use if SSL works
SSLPort=443

# Paths to Cert and Key files
SSLCertFile=
SSLKeyFile=

# CPU Affinity - Specify logical cores to run on. Automatically chooses if empty.
# ex:
#  CPUAffinity=0,1,3,5,9
CPUAffinity=

```


<!-- GETTING STARTED -->

## Getting Started

To get a local copy up and running follow these simple steps or check the [Latest Release](https://github.com/ricky-davis/AstroLauncher/releases/latest) for a download of the executable.

### Prerequisites

- Python 3.7
- pip / pipenv

### Installation

1. Clone the AstroLauncher repository

```sh
git clone https://github.com/ricky-davis/AstroLauncher.git
```

2. Install python modules using pip or pipenv

```sh
pip install -r requirements.txt
```

```sh
pipenv install
```

<br />

<!-- USAGE EXAMPLES -->

## Usage

Run the server launcher using the following command

```sh
pipenv run python AstroLauncher.py
```

<br /><br />
If not placed in the same directory as the server files, you can specify a server folder location like so

```sh
python AstroLauncher.py --path "steamapps\common\ASTRONEER Dedicated Server"
```

```sh
pipenv run python AstroLauncher.py -p "steamapps\common\ASTRONEER Dedicated Server"
```

<br />

### Building an EXE

1. If you want to turn this project into an executable, make sure to install pyinstaller using one of the following methods

```sh
pip install pyinstaller
```

```sh
pipenv install -d
```

2. Run pyinstaller with the all-in-one flag

```sh
pyinstaller AstroLauncher.py -F --add-data "assets;./assets" --icon=assets/astrolauncherlogo.ico
```
or just run the BuildEXE.py which automatically cleans up afterwards
```sh
python BuildEXE.py
```

1. Move the executable (in the new `dist` folder) to the directory of your choice. (If you want you can now delete the `dist` and `build` folders, as well as the `.spec` file)
2. Run AstroLauncher.exe

```sh
AstroLauncher.exe -p "steamapps\common\ASTRONEER Dedicated Server"
```

<!-- CONTRIBUTING -->

## Contributing

Contributions are what make the open source community such an amazing place to be learn, inspire, and create. Any contributions you make are **greatly appreciated**.

1. Fork the Project
2. Create your Feature Branch (`git checkout -b feature/AmazingFeature`)
3. Commit your Changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the Branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

<!-- LICENSE -->

## License

Distributed under the MIT License. See `LICENSE` for more information.

<!-- CONTACT -->

## Contact

Ricky Davis - Discord: @Spyci#0001

Project Link: [https://github.com/ricky-davis/AstroLauncher](https://github.com/ricky-davis/AstroLauncher)

<!-- MARKDOWN LINKS & IMAGES -->
<!-- https://www.markdownguide.org/basic-syntax/#reference-style-links -->

[contributors-shield]: https://img.shields.io/github/contributors/ricky-davis/AstroLauncher.svg?style=flat-square
[contributors-url]: https://github.com/ricky-davis/AstroLauncher/graphs/contributors
[forks-shield]: https://img.shields.io/github/forks/ricky-davis/AstroLauncher.svg?style=flat-square
[forks-url]: https://github.com/ricky-davis/AstroLauncher/network/members

[downloads-shield]:https://img.shields.io/github/downloads/ricky-davis/AstroLauncher/total
[downloads-url]:https://github.com/ricky-davis/AstroLauncher/releases/latest

[stars-shield]: https://img.shields.io/github/stars/ricky-davis/AstroLauncher.svg?style=flat-square
[stars-url]: https://github.com/ricky-davis/AstroLauncher/stargazers
[issues-shield]: https://img.shields.io/github/issues/ricky-davis/AstroLauncher.svg?style=flat-square
[issues-url]: https://github.com/ricky-davis/AstroLauncher/issues
[license-shield]: https://img.shields.io/github/license/ricky-davis/AstroLauncher.svg?style=flat-square
[license-url]: https://github.com/ricky-davis/AstroLauncher/blob/master/LICENSE.txt
