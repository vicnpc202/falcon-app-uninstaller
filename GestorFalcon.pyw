# SPDX-License-Identifier: GPL-3.0-only
"""Panel de inventario de Falcon. Iniciar con python gestor.py o python gestor.py --falcon."""
import argparse
import zipfile

__version__ = "1.0.2"
import csv
import hashlib
import json
import os
import queue
import sys
import threading
import time
import tkinter as tk
import uuid
import unicodedata
from pathlib import Path
from datetime import datetime
from tkinter import filedialog, messagebox, ttk

"""Inventario local y campañas de desinstalación por aplicación."""
import hashlib
import json
import re
import sqlite3
import uuid
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone, timedelta


def now():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


LEGACY_RULES = {
    "Juegos": ["Minecraft", "Fortnite", "Roblox", "Valorant", "League of Legends",
               "Counter-Strike", "Dota 2", "Rocket League", "Among Us", "The Sims"],
    "Plataformas de juegos": ["Steam", "Epic Games Launcher", "Battle.net", "Ubisoft Connect", "EA app"],
    "Navegadores": ["Chrome", "Google Chrome", "Microsoft Edge", "Firefox", "Mozilla Firefox", "Brave"],
    "Ofimática": ["Microsoft 365", "Microsoft Office", "LibreOffice", "Microsoft Excel", "Microsoft Word"],
    "Comunicación": ["Microsoft Teams", "Zoom", "Slack", "Discord", "Webex"],
    "Desarrollo": ["Visual Studio Code", "Microsoft Visual Studio", "Python", "Git", "Node.js"],
    "Multimedia": ["VLC", "Spotify", "Audacity", "OBS Studio"],
    "Utilidades": ["7-Zip", "WinRAR", "PowerToys", "Notepad++"],
}


# Los alias específicos tienen prioridad sobre la familia (Chrome Remote Desktop / Chrome).
RULES = {key:list(values) for key,values in LEGACY_RULES.items()}
EXTRA = {
    "Juegos": ["Chess.app","Microsoft Solitaire Collection","Solitaire & Casual Games","GGPoker","PokerStars",
               "Pokémon Trading Card Game Live","JuegosJuegos","RobloxPlayerBeta","RobloxStudioBeta"],
    "Plataformas de juegos": ["Google Play Games","Riot Client","Xbox Game Bar","Moonlight Game Streaming Client"],
    "Componentes de juegos": ["Epic Online Services","Riot Vanguard","Microsoft Windows GameInput","GameInput"],
    "Emuladores": ["BlueStacks","GameLoop","MuMuPlayer","LDPlayer","NoxPlayer"],
    "Acceso remoto": ["Chrome Remote Desktop","AnyDesk","Radmin","RealVNC","VNC Server","VNC Viewer",
                      "TightVNC","UltraVNC","TeamViewer","MeshCentral Agent","Aranda Remote Control Workstation","Remmina"],
    "VPN y proxy": ["FortiClient VPN","Cisco AnyConnect","AnyConnect Secure Mobility Client","Cisco Secure Client",
                    "OpenVPN","eduVPN","NordVPN","ExpressVPN","Hola VPN","WireGuard","Proxifier","AVG Secure VPN"],
    "Seguridad": ["CrowdStrike","Kaspersky","Agente de red de Kaspersky","FortiClient","XProtect.app","360 Total Security",
                  "Malwarebytes","Defender Engine","Defender Signature","Microsoft Defender"],
    "Navegadores": ["Opera","Vivaldi","Internet Explorer","CCleaner Browser","Hola Browser"],
    "Extensiones de navegador": ["Roblox+","Google Keep Chrome Extension","Zoom Chrome Extension","Adblock Plus",
                                "AdBlock — block ads across the web","Custom Cursor for Chrome","Chrome Web Store Payments"],
    "Instaladores y actualizaciones": ["Chrome Installer","Edge Installer","Zoom Installer","Zoom Meetings Installer",
               "Update for","Security Update for","Definition Update for","Service Pack 2 for","Acrobat Update Service",
               "Adobe Updater Startup Utility","Adobe Update Service","Foxit Updater","Opera auto-updater","Opera GX auto-updater"],
    "PDF y OCR": ["Adobe Acrobat","Adobe Reader","Acrobat","AcroCEF","AcroTray","Nitro Pro","ABBYY PDF Transformer","ABBYY FineReader",
                  "PDF24","PDF24 Creator","PDF Creator","PDF Reader","PDF-Viewer","PDF Arranger","Foxit PDF","UniPDF"],
    "Ofimática": ["Aplicaciones de Microsoft 365","2007 Microsoft Office","Microsoft Word","Microsoft PowerPoint",
                  "Microsoft OneNote","OpenOffice","Apache OpenOffice","Power BI Desktop"],
    "Comunicación": ["Skype","Skype For Business","WeChat","Thunderbird","Microsoft Outlook","Zoom Workplace",
                     "Webex Meetings","AChat","BeeBEEP","Microsoft Skype","FaceTime.app","Vypress Chat"],
    "Almacenamiento en la nube": ["OneDrive","Microsoft OneDrive","Dropbox","Google Drive","iCloud Drive.app"],
    "Desarrollo": ["Visual Studio","GitHub Desktop","Git for Windows","PyCharm","IntelliJ IDEA","Eclipse IDE"],
    "Bases de datos": ["SQL Server","Microsoft SQL Server","ODBC Driver For SQL Server","PostgreSQL","MySQL","MariaDB","DBeaver"],
    "Multimedia": ["5KPlayer","K-Lite","Movavi Video","Winamp","4K Video Downloader","Freemake Video Converter","Any Video Converter",
                   "VLC media player","Microsoft.MediaPlayer"],
    "Diseño y CAD": ["Adobe Photoshop","Adobe Illustrator","AutoCAD","Autodesk AutoCAD","AcCoreConsole","GIMP","Inkscape"],
    "Redes y diagnóstico": ["Wireshark","Nmap","Burp Suite","WinPcap","Npcap","PuTTY"],
    "Descargas y P2P": ["JDownloader","Internet Download Manager","uTorrent","µTorrent","qBittorrent","BitTorrent"],
    "Impresión y escaneo": ["HP Laser","HP LaserJet","HP Scanjet","HP Scan Software","HP Easy Printer Manager",
                           "HPPrintScanDoctor","Scanner Tools Utility","Lexmark Printer","Lexmark Universal","Lexmark Network Twain"],
    "Componentes del sistema": [".NET Framework","Microsoft .NET","ASP .Net Core","Microsoft Visual C++",
                                "WebView2 Runtime de Microsoft Edge","Microsoft Edge WebView2 Runtime"],
    "Utilidades": ["Glary Utilities","CCleaner","Advanced SystemCare","IObit Uninstaller","PowerToys","WinZip","PeaZip"],
    "Asistentes de IA": ["ChatGPT","GitHub Copilot CLI","365 Copilot"],
    "Virtualización": ["VMware Workstation","VMware Tools","Oracle VM VirtualBox","VirtualBox","Parallels Desktop"],
    "Servidores web": ["Apache HTTP Server","nginx","Apache Tomcat","IIS Express"],
    "Administración de equipos": ["GLPI Agent","GLPI-Agent","Aranda Agent","Microsoft Intune","Intune Management Extension"],
    "Respaldo y recuperación": ["Wondershare Recoverit","Veeam Agent","Veeam Backup","Acronis True Image"],
    "Aplicaciones institucionales": [],
    "Paquetes de distribución Linux": [],
    "Gestión bibliográfica": ["Zotero"],
    "Entornos de ejecución": ["Java(TM) Platform", "Java Platform SE", "OpenJDK", "Eclipse Temurin"],
    "Herramientas del fabricante": [],
    "Controladores y hardware": ["Intel Driver & Support Assistant","NVIDIA Graphics Driver","Lenovo System Update",
                                "NVIDIA Controlador","Realtek Audio Service","HD Graphics Drivers For Windows",
                                "Logi Options+","Lenovo Hotkey Features","HP Digital Imaging","CrystalDiskInfo","Driver Booster",
                                "HP Support Assistant","HP Display Control Service","AMD Software"],
}
for group, names in {
    "Plataformas de juegos": ["Steam Client", "Steam.app", "SteamSetup", "Steam Launcher",
                              "EpicGamesLauncher", "GOG Galaxy", "Rockstar Games Launcher", "EA Desktop",
                              "Game Center.app", "Ubisoft Game Launcher"],
    "Componentes de juegos": ["SteamWebHelper", "Steam Client WebHelper", "Steam Client Service",
                               "Microsoft GameInput", "Roblox Bootstrapper", "Google Play Games Services"],
    "Juegos": ["CounterStrike", "Fall Guys", "Warframe", "Genshin Impact", "The Sims 4",
               "Apex Legends", "Terraria", "Overwatch", "World of Warcraft", "Team Fortress 2",
               "Grand Theft Auto V", "Geometry Dash", "Stardew Valley", "Hollow Knight"],
    "Aplicaciones institucionales": [],
    "Impresión y escaneo": ["CLPrint", "ecoEndPoint", "VueScan", "hpScanDispatch", "Kofax VRS", "PrinterControl4"],
    "PDF y OCR": ["PDFill FREE PDF", "PDF Architect"],
    "Ofimática": ["Aplicación WordPad de Windows"],
    "Acceso remoto": ["Conexión a Escritorio remoto"],
    "Bases de datos": ["Quest Software Toad Data Modeler"],
    "Desarrollo": ["IntelliJ Platform", "oneAPI Level Zero"],
    "Respaldo y recuperación": ["DataRecoveryService"],
    "Instaladores y actualizaciones": ["Java Platform SE Auto Updater", "Microsoft Update Assistant.app",
                                      "NVIDIA Install Application", "HP Installer"],
    "Controladores y hardware": ["IGCC Service", "HP PSDr NTService Component", "Intel Management Engine Driver",
                                 "ALPSALPINE Touch Pad Driver", "BroadcomWifi", "HP Accessory WMI Provider",
                                 "HP Hotkey Support","HP Audio Control","Rapid Storage Technology Service",
                                 "Controlador de bus Bluetooth","Intel(R) Management Engine","Intel(R) Extreme Tuning Utility"],
    "Seguridad": ["Falcon Sensor","Local Administrator Password Solution","SafeNet Authentication Client"],
    "Almacenamiento en la nube": ["Nextcloud","ownCloud"],
    "Componentes del sistema": ["Internet Low Mic Utility","Widgets Platform Runtime","CrossDeviceService"],
    "Multimedia": ["Reproductor de Windows Media","Visualizador de fotos de Windows"],
}.items():
    EXTRA[group].extend(names)
for group, aliases in EXTRA.items():
    RULES.setdefault(group, []).extend(aliases)


def normalize(value):
    return " ".join(value.casefold().replace("®","").replace("™","").split())



# Familias ampliadas a partir del inventario; gana siempre el alias más específico.
CATALOG_RULES = {'Diseño y CAD': ['Adobe InDesign', 'Adobe InCopy', 'Adobe Lightroom', 'Adobe Bridge', 'Adobe Animate', 'Adobe Fireworks', 'Adobe Express', 'Adobe Substance', 'Affinity', 'CorelDRAW', 'Corel PHOTO-PAINT', 'SketchUp', 'Revit', 'Autodesk Revit', 'Autodesk 3ds Max', 'Autodesk Maya', 'Autodesk Inventor', 'Autodesk Fusion', 'Autodesk Civil', 'Autodesk Navisworks', 'Blender', 'FreeCAD', 'LibreCAD', 'QCAD', 'ZWCAD', 'ArchiCAD', 'Graphisoft', 'eDrawings', 'Figma', 'draw.io', 'Xmind', 'yEd Graph Editor', 'Wondershare EdrawMax', 'paint.net', 'Krita', 'digiKam', 'XnView', 'XnConvert'], 'Multimedia': ['Adobe Premiere', 'Adobe Premiere Pro', 'Adobe Premiere Rush', 'Adobe After Effects', 'Adobe Audition', 'Adobe Media Encoder', 'Wondershare Filmora', 'Wondershare UniConverter', 'Wondershare Uniconverter', 'Wondershare DVD Creator', 'Wondershare Video Repair', 'AIMP', 'AIMP2', 'AVS Audio', 'AVS Video', 'Ableton Live', 'ASIO4ALL', 'Audacity', 'foobar2000', 'ffmpeg', 'mpv', 'ocenaudio', 'kdenlive', 'Shotcut', 'OpenShot', 'DaVinci Resolve', 'HandBrake', 'MediaInfo', 'PotPlayer', 'KMPlayer', 'GOM Player', 'QuickTime', 'iTunes', 'iMovie', 'GarageBand', 'Apple Music', 'Apple TV', 'YouTube Music', 'Stremio', 'stremio-shell-ng', 'Camtasia', 'Bandicam', 'Lightshot', 'ShareX', 'Greenshot', 'Snagit', 'OBS', 'vMix', 'rekordbox', 'Nero', 'Roxio', 'Winamp', 'jetAudio', 'fre:ac', 'mp3DirectCut', 'dBpoweramp', 'X Codec Pack'], 'PDF y OCR': ['Wondershare PDFelement', 'Wondershare PDF', 'iLovePDF', 'iTop PDF', 'PDFsam', 'pdfFactory', 'doPDF', 'novaPDF', 'qpdf', 'Xpdf', 'SumatraPDF', 'Sumatra PDF', 'PDF-XChange', 'PDFCreator', 'PDF Architect', 'PDFill', 'ABBYY OCR', 'ABBYY Recognition', 'Nuance PDF', 'Nuance Power PDF', 'Kofax Power PDF', 'Tungsten Power PDF', 'CutePDF', 'Bullzip PDF', 'freepdfcompressor'], 'Comunicación': ['WhatsApp', 'Telegram', 'Signal', 'Zimbra', 'Rocket.Chat', 'eM Client', 'Zoiper', 'mIRC', 'AdiIRC', 'Winpopup LAN Messenger', 'Mattermost', 'Element', 'Jitsi', 'Google Chat', 'Google Meet', 'LINE', 'Viber', 'Cisco Jabber', 'Cisco Webex', 'Citrix HDX RealTime Media Engine'], 'Ofimática': ['ONLYOFFICE', 'WPS Office', 'SoftMaker', 'FreeOffice', 'AbleWord', 'WordPad', 'Wordpad Application', 'WordPad for Windows', 'Microsoft Visio', 'Microsoft Project', 'Microsoft Publisher', 'Microsoft Access', 'LibreOffice', 'OpenOffice', 'think-cell', 'Writage', 'ASAP Utilities', 'Pages.app', 'Numbers.app', 'Keynote.app'], 'Bases de datos': ['pgAdmin', 'pgAgent', 'psqlODBC', 'dbForge', 'Toad', 'Quest Toad', 'Oracle Database', 'Oracle AI Database', 'Oracle Client', 'Oracle Data Provider', 'Oracle SQL Developer', 'Oracle Provider', 'Oracle MTS', 'Oracle Instant Client', 'oracle-instantclient', 'SQLDeveloper', 'SQL Server', 'Microsoft SQL Server', 'Microsoft ODBC', 'Microsoft OLE DB', 'SQL Native Client', 'Azure Data Studio', 'SQLite', 'DB Browser for SQLite', 'MongoDB', 'Redis', 'MariaDB', 'MySQL', 'HeidiSQL', 'Robo 3T', 'Studio 3T', 'Access Database Engine', 'Microsoft Access Database Engine'], 'Desarrollo': ['Visual Studio Code', 'VSCodium', 'Cursor', 'Windsurf', 'Sublime Text', 'Atom', 'Notepad++', 'Android Studio', 'Android SDK', 'Xcode', 'NetBeans', 'Apache NetBeans', 'Oracle JDeveloper', 'JetBrains', 'WebStorm', 'PhpStorm', 'Rider', 'GoLand', 'DataGrip', 'CLion', 'RustRover', 'Postman', 'Insomnia', 'Fiddler', 'GitKraken', 'SourceTree', 'TortoiseGit', 'TortoiseSVN', 'WinMerge', 'Beyond Compare', 'Node.js', 'Node', 'npm', 'Yarn', 'Go Programming Language', 'Rust', 'Ruby', 'ActivePerl', 'Strawberry Perl', 'MinGW', 'MSYS2', 'CMake', 'GitHub CLI', 'glab', 'Docker CLI', 'Azure CLI', 'Microsoft Windows SDK', 'Windows SDK', 'Windows Software Development Kit', 'Microsoft .NET SDK', 'NuGet', 'MSBuild', 'Microsoft Build Tools', 'Build Tools for Visual Studio'], 'Entornos de ejecución': ['Java', 'Java(TM)', 'Java JRE', 'JDK', 'AdoptOpenJDK', 'Amazon Corretto', 'Azul Zulu', 'Zulu', 'ojdkbuild', 'Microsoft OpenJDK', 'Microsoft Build of OpenJDK', 'Eclipse Temurin', 'Eclipse OpenJ9', 'Microsoft Edge WebView2 Runtime', 'Adobe AIR', 'Adobe Flash Player', 'Microsoft Silverlight'], 'Navegadores': ['360 Extreme Browser', 'AVG Secure Browser', 'AVG Browser', 'Avast Secure Browser', 'CCleaner Browser', 'Tor Browser', 'Tor Browser Bundle', 'Waterfox', 'Pale Moon', 'Maxthon', 'Comodo Dragon', 'Comet', 'Zen Browser', 'Safari', 'Chromium', 'Yandex', 'DuckDuckGo', 'Arc'], 'Seguridad': ['1Password', 'Bitwarden', 'KeePass', 'KeePassXC', 'LastPass', 'Dashlane', 'AdGuard', 'AdwCleaner', 'McAfee', 'Norton', 'Avast', 'AVG AntiVirus', 'AVG Antivirus', 'AVG Internet Security', 'Avira', 'ESET', 'Bitdefender', 'Sophos', 'Trend Micro', 'Panda', 'Comodo Internet Security', '360 Internet Security', 'Windows Defender', 'Microsoft Security Essentials', 'Microsoft Safety Scanner', 'Spybot', 'SUPERAntiSpyware', 'HitmanPro', 'SentinelOne', 'Trellix', 'Carbon Black'], 'Virtualización': ['Oracle VirtualBox', 'VirtualBox', 'Docker Desktop', 'Docker Engine', 'Podman', 'QEMU', 'Hyper-V', 'Windows Subsystem for Linux', 'Windows Subsystem for Android', 'Windows XP Mode', 'viBoot'], 'Redes y diagnóstico': ['Advanced IP Scanner', 'Advanced Port Scanner', 'Angry IP Scanner', 'IP Scanner', 'PingPlotter', 'WinMTR', 'WinBox', 'Tftpd64', 'Tftpd32', '3CDaemon', 'OpenSSH', 'Xshell', 'MobaXterm', 'Netcat', 'Zabbix', 'PRTG', 'iperf', 'cloudflared', 'ngrok', 'Fing'], 'Acceso remoto': ['RustDesk', 'Splashtop', 'ScreenConnect', 'ConnectWise Control', 'Remote Utilities', 'Supremo', 'AeroAdmin', 'DWAgent', 'NoMachine', 'Parsec', 'mRemoteNG', 'Royal TS', 'Remote Desktop Connection Manager', 'Microsoft Remote Desktop', 'Windows App', 'Citrix Workspace', 'Citrix Receiver', 'VMware Horizon Client', 'Omnissa Horizon Client'], 'VPN y proxy': ['Tailscale', 'ZeroTier', 'Proton VPN', 'ProtonVPN', 'Surfshark', 'TunnelBear', 'Windscribe', 'SoftEther', 'GlobalProtect', 'Pulse Secure', 'Ivanti Secure Access', 'Check Point Endpoint Security VPN', 'SonicWall NetExtender', 'SonicWall Global VPN', 'Wire VPN'], 'Almacenamiento en la nube': ['iCloud', 'iCloud+', 'Box Drive', 'Box Sync', 'MEGAsync', 'pCloud', 'Nextcloud', 'ownCloud', 'Syncthing', 'Resilio Sync'], 'Respaldo y recuperación': ['AOMEI Backupper', 'AOMEI Cloner', 'Macrium Reflect', 'EaseUS Todo Backup', 'EaseUS Data Recovery', 'Recuva', 'Wise Data Recovery', 'Wondershare Data Recovery', 'Wondershare UBackit', 'Acronis Backup', 'Acronis Cyber Protect', 'Veritas Backup Exec', 'MiniTool Power Data Recovery', 'R-Studio', 'TestDisk', 'PhotoRec'], 'Utilidades': ['7Z Extractor', 'PeaZip', 'Bandizip', 'WinZip', '7Caps', '8GadgetPack', 'PowerToys', 'Everything', 'WizTree', 'WizFile', 'TreeSize', 'XYplorer', 'xplorer²', 'Total Commander', 'FreeCommander', 'Double Commander', 'Q-Dir', 'Advanced Renamer', 'Bulk Rename Utility', 'dupeGuru', 'Agent Ransack', 'grepWin', 'Rufus', 'Ventoy', 'balenaEtcher', 'CPU-Z', 'GPU-Z', 'HWiNFO', 'HWMonitor', 'AIDA64', 'CrystalDiskMark', 'CrystalDiskInfo', 'Speccy', 'Process Explorer', 'Process Monitor', 'Autoruns', 'Disk2vhd', 'TCPView', 'RAMMap', 'Handle', 'Wise Disk Cleaner', 'Wise Registry Cleaner', 'Wise Program Uninstaller', 'Wise Memory Optimizer', 'Wise Care', 'IObit Uninstaller', 'Smart Defrag', 'Advanced SystemCare', 'AOMEI Partition Assistant', 'MiniTool Partition Wizard', 'EaseUS Partition Master', '4DDiG Partition Manager', 'f.lux', 'X-Mouse Button Control', 'AutoHotkey', 'AutoIt'], 'Plataformas de juegos': ['Xbox', 'Amazon Games', 'GOG Galaxy', 'Rockstar Games Launcher', 'Ubisoft Connect', 'EA Desktop', 'EA app', 'Battle.net', 'Riot Client', 'Playnite'], 'Juegos': ['Age of Empires', 'AoE2 DE', 'Age of Mythology', '3D Pinball', 'osu!', 'ACR Poker', 'War Thunder', 'Warframe', 'Hearthstone', 'Diablo', 'StarCraft', 'Starcraft', 'The Elder Scrolls', 'The Witcher', 'Cyberpunk 2077', 'Baldur', 'Hogwarts Legacy', 'PUBG', 'PLAYERUNKNOWN', 'Fall Guys', 'Fallout', 'Geometry Dash', 'Hollow Knight', 'Among Us', 'Left 4 Dead', 'Team Fortress', 'Grand Theft Auto', 'Euro Truck Simulator', 'American Truck Simulator', 'Forza', 'Plants vs. Zombies', 'Plants vs Zombies', 'PlantsVsZombies'], 'Componentes de juegos': ['Xbox Service', 'Xbox.Apps.GameOverlay', 'Xbox.Apps.GamingOverlay', 'Xbox.Apps.TCUI', 'Gaming Services', 'Microsoft Gaming Services', 'Steamworks', 'Easy Anti-Cheat', 'EasyAntiCheat', 'BattlEye', 'Unity Web Player'], 'Emuladores': ['mGBA', 'Dolphin Emulator', 'PCSX2', 'PPSSPP', 'RPCS3', 'RetroArch', 'Citra', 'Ryujinx', 'MEmu', 'BlueStacks', 'X360 Controller Emulator'], 'Servidores web': ['XAMPP', 'Wampserver', 'WAMP', 'Laragon', 'Abyss Web Server', 'Apache HTTP', 'Apache Tomcat', 'nginx', 'hMailServer'], 'Impresión y escaneo': ['Epson', 'EPSON', 'Canon IJ', 'Canon MF', 'Canon LBP', 'Canon i-SENSYS', 'Canon Generic', 'Canon Inkjet', 'Canon Printer', 'Canon Print', 'Canon Scan', 'Samsung Easy Printer', 'Samsung Universal Print', 'Samsung Scan', 'Samsung Printer', 'Xerox', 'Ricoh', 'RICOH', 'Kyocera', 'KYOCERA', 'Brother', 'brother', 'Zebra', 'ZDesigner', 'Pantum', 'PaperCut', 'NAPS2', 'VueScan', 'FinePrint', 'PrintHand'], 'Administración de equipos': ['Zabbix Agent', 'GLPI', 'OCS Inventory', 'Lansweeper', 'ManageEngine Endpoint Central', 'Desktop Central', 'PDQ Inventory', 'PDQ Deploy', 'Microsoft Configuration Manager', 'Microsoft Endpoint Configuration Manager', 'Microsoft System Center', 'Absolute Persistence Agent'], 'Firma digital': ['AutoFirma', 'FirmaEC', 'XolidoSign', 'Adobe Acrobat Sign', 'APP Nativa Signador', 'Agile ChileCompra Firma Digital'], 'Análisis de datos': ['RStudio', 'Positron', 'R for Windows', 'R Statistics', 'IBM SPSS', 'SPSS', 'Stata', 'jamovi', 'JASP', 'Minitab', 'MATLAB', 'GNU Octave', 'Tableau', 'Qlik', 'ATLAS.ti', 'NVivo', 'QGIS', 'ArcGIS', 'ArcMap'], 'Videovigilancia': ['iVMS-4200', 'Hikvision', 'Dahua', 'SmartPSS', 'Agent DVR', 'iSpy', 'exacqVision', 'AXIS Device Manager', 'AXIS IP Utility', 'AXIS Media Control', 'Milestone XProtect']}
for group, aliases in CATALOG_RULES.items():
    RULES.setdefault(group, []).extend(aliases)

ALIASES = {normalize(alias):group for group,aliases in RULES.items() for alias in aliases}
FAMILY = re.compile("^(" + "|".join(re.escape(n) for n in sorted(ALIASES,key=len,reverse=True)) + r")(?=$|[\s(.\-:®™]|\d)")
MS_NAMES = {
    "Navegadores": ["Edge"], "Comunicación": ["Teams","Outlook"],
    "Ofimática": ["365 Apps","Excel","Powerpoint","Onenote","Office","Publisher","Access","Word","Visio Viewer","Sharepoint"],
    "Componentes del sistema": ["Windows","MSXML","Hypervisor","Vbscript","Jscript"],
    "Asistentes de IA": ["Copilot"], "Administración de equipos": ["Intune"],
    "Multimedia": ["Photos"], "Utilidades": ["Calculator","Paint"],
    "Desarrollo": ["Visual c++"], "Componentes de juegos": ["Game Bar"],
    "Instaladores y actualizaciones": ["Update Health Tools"],
}
MS_ALIASES = {normalize(n):g for g,names in MS_NAMES.items() for n in names}


def classify(name, vendor="", platform="", software_type=""):
    label, publisher = normalize(name),normalize(vendor)
    if normalize(software_type).replace("_"," ").replace("-"," ") == "browser extension":
        return "Extensiones de navegador"
    # SDK e IDE no son lo mismo que los redistribuibles de ejecución.
    if re.search(r"(?:visual c\+\+|visual studio).*?(?:redistributable|redistribuible|runtime|minimum|additional)",label):
        return "Componentes del sistema"
    if re.search(r"(?:\.net|asp\.?\s*\.net).*?(?:sdk|targeting pack|developer pack)",label):
        return "Desarrollo"
    if re.match(r"(?:microsoft )?(?:\.net|asp\.?\s*\.net)(?:$|[ .-])",label):
        return "Componentes del sistema"
    if publisher.startswith("microsoft") and re.match(r"(?:actualización (?:de seguridad |acumulativa )?para|security update for|update for|hotfix for)",label):
        return "Instaladores y actualizaciones"
    if re.search(r"(?:driver|controlador)(?:s|es)?(?:$|[ (.-])",label) and not re.search(r"odbc|oledb|ole db|jdbc|sql",label) and platform.casefold() != "linux":
        return "Impresión y escaneo" if re.search(r"print|printer|impres|scan|epson|canon|xerox|brother",label) else "Controladores y hardware"
    if platform.casefold() == "linux" and publisher.startswith(("ubuntu", "xubuntu", "canonical", "debian", "rocky", "centos", "fedora", "red hat", "almalinux", "remi", "oracle america")):
        return "Paquetes de distribución Linux"
    if publisher in {"microsoft","microsoft corporation"} and label in MS_ALIASES:
        return MS_ALIASES[label]
    if publisher in {"google","google llc"} and label=="update":
        return "Instaladores y actualizaciones"
    match = FAMILY.match(label)
    if match and not (software_type and ALIASES[match[1]] == "Extensiones de navegador"):
        return ALIASES[match[1]]
    if publisher.startswith("cisco") and label == "secure client":
        return "VPN y proxy"
    if publisher.startswith("oracle") and re.match(r"java\s+\d",label):
        return "Entornos de ejecución"
    if publisher.startswith("oracle") and label.startswith("sql*plus"):
        return "Bases de datos"
    if (publisher.startswith("microsoft") and label=="windows terminal") or (
        publisher=="strawberry perl" and label=="strawberry perl"):
        return "Desarrollo"
    if publisher.startswith("microsoft") and label.startswith(("office service","office push","clicktorun")):
        return "Ofimática"
    if publisher.startswith("microsoft") and label in {"local ai","artificial intelligence"}:
        return "Asistentes de IA"
    if publisher.startswith("adobe") and label in {"web installer","adobe cpinstcu"}:
        return "Instaladores y actualizaciones"
    if publisher.startswith(("lexmark international","kyocera document solutions","brother industries")):
        return "Impresión y escaneo"
    if publisher=="the document foundation":
        return "Ofimática"
    if publisher.startswith("eclipse adoptium"):
        return "Entornos de ejecución"
    if platform.casefold() == "linux" and publisher.startswith(("ubuntu core developers", "xubuntu developers", "canonical kernel team", "debian", "almalinux", "oracle america")):
        return "Paquetes de distribución Linux"
    if publisher.startswith("apple") and platform.casefold() in {"mac", "macos"}:
        if label in {"safari.app"}: return "Navegadores"
        if label in {"pages.app", "numbers.app", "keynote.app", "notes.app", "reminders.app", "calendar.app"}: return "Ofimática"
        if label in {"music.app", "tv.app", "photos.app", "quicktime player.app", "podcasts.app", "books.app"}: return "Multimedia"
        if label in {"messages.app", "mail.app", "contacts.app", "facetime.app"}: return "Comunicación"
        if any(word in label for word in ("agent", "service", "helper", "daemon", "uiserver")):
            return "Componentes del sistema"
        if label in {"activity monitor.app", "disk utility.app", "console.app", "system settings.app", "system preferences.app", "archive utility.app", "keychain access.app", "automator.app", "terminal.app", "calculator.app", "app store.app"}:
            return "Utilidades"
    if publisher.startswith(("seiko epson", "epson america", "canon inc", "canon electronics", "xerox corporation", "ricoh", "kyocera document")):
        return "Impresión y escaneo"
    if publisher.startswith(("postgresql global development", "quest software", "quest software inc")) and re.search(r"postgres|pgadmin|pgagent|sql|database|toad", label):
        return "Bases de datos"
    if publisher.startswith(("adobe",)) and any(word in label for word in ("updat", "install", "setup", "download manager")):
        return "Instaladores y actualizaciones"
    if publisher.startswith("adobe") and any(word in label for word in ("licens", "genuine", "crash", "ipc", "cef helper", "cep html", "desktop service", "gcclient")):
        return "Componentes de aplicaciones"
    if publisher in {"hp","hp inc.","hewlett-packard","lenovo","lenovo group limited","intel","intel corporation",
                     "intel(r) corporation","nvidia corporation","asustek computer inc."}:
        return "Herramientas del fabricante"
    if platform.casefold()=="linux" and (
        publisher in {"rocky enterprise software foundation","centos","fedora project","rocky","red hat, inc."}
        or publisher.startswith(("ubuntu developers", "ubuntu desktop team", "ubuntu kernel team",
                                 "remi's rpm repository", "remi collet"))
    ):
        return "Paquetes de distribución Linux"
    return "Sin clasificar"


def migrate_categories(db):
    if db.execute("SELECT 1 FROM meta WHERE key='catalog_v3'").fetchone():
        return
    with db:
        rows = db.execute("""SELECT id,name,vendor,platform,category FROM app
            WHERE id NOT IN (SELECT app_id FROM manual_category)""").fetchall()
        for app_id,name,vendor,platform,previous in rows:
            if previous in {"Extensiones de navegador", "Paquetes de distribución Linux"}:
                continue
            category = classify(name,vendor,platform,"application")
            if category != "Sin clasificar" and category != previous:
                db.execute("UPDATE app SET category=? WHERE id=?",(category,app_id))
        db.execute("INSERT OR REPLACE INTO meta VALUES('catalog_v3','1')")


def classify_pending(db):
    rows = db.execute("""SELECT id,name,vendor,platform FROM app
                         WHERE category='Sin clasificar' AND draft='' AND script=''
                         AND id NOT IN (SELECT app_id FROM manual_category)""").fetchall()
    updates = []
    for app_id, name, vendor, platform in rows:
        category = classify(name, vendor, platform, "application")
        if category != "Sin clasificar":
            updates.append((category, app_id))
    with db:
        db.executemany("""UPDATE app SET category=? WHERE id=? AND category='Sin clasificar'
                          AND draft='' AND script=''""", updates)
    return len(updates)


def db_open(path):
    db = sqlite3.connect(path, timeout=30)
    db.row_factory = sqlite3.Row
    db.execute("PRAGMA journal_mode=WAL")
    db.executescript("""
        CREATE TABLE IF NOT EXISTS app (
          id INTEGER PRIMARY KEY, name TEXT, vendor TEXT, platform TEXT, category TEXT,
          draft TEXT DEFAULT '', script TEXT DEFAULT '', UNIQUE(name,vendor,platform));
        CREATE TABLE IF NOT EXISTS inventory (
          app_id INTEGER, host_key TEXT, aid TEXT, hostname TEXT, installed INTEGER, used INTEGER,
          PRIMARY KEY(app_id, host_key));
        CREATE TABLE IF NOT EXISTS meta (key TEXT PRIMARY KEY, value TEXT);
        CREATE TABLE IF NOT EXISTS manual_category (app_id INTEGER PRIMARY KEY);
        CREATE TABLE IF NOT EXISTS job (
          id INTEGER PRIMARY KEY, campaign TEXT, app_id INTEGER, aid TEXT, hostname TEXT,
          script TEXT, offline INTEGER, status TEXT, session TEXT DEFAULT '', request TEXT DEFAULT '',
          seq INTEGER DEFAULT 0, output TEXT DEFAULT '', detail TEXT DEFAULT '', updated TEXT);
        CREATE UNIQUE INDEX IF NOT EXISTS one_active ON job(app_id,aid)
          WHERE status IN ('Preparado','Enviando','Revisar en Falcon','En cola','Enviado','En curso');
        CREATE TABLE IF NOT EXISTS removal (id INTEGER PRIMARY KEY, app_id INTEGER, host_key TEXT,
          hostname TEXT, stamp TEXT);
        CREATE INDEX IF NOT EXISTS removals_by_app ON removal(app_id,stamp);
        CREATE TABLE IF NOT EXISTS verified_job (id INTEGER PRIMARY KEY);
        CREATE INDEX IF NOT EXISTS inventory_by_host ON inventory(host_key);
        CREATE TABLE IF NOT EXISTS loading_inventory (
          app_id INTEGER, host_key TEXT, aid TEXT, hostname TEXT, installed INTEGER, used INTEGER,
          installed_at TEXT, PRIMARY KEY(app_id,host_key));
        CREATE TABLE IF NOT EXISTS loading_run (
          id INTEGER PRIMARY KEY CHECK(id=1), started TEXT, cursor TEXT, scanned INTEGER, ready INTEGER);
        CREATE TABLE IF NOT EXISTS event (id INTEGER PRIMARY KEY, job_id INTEGER,
          stamp TEXT, status TEXT, detail TEXT);
        CREATE TABLE IF NOT EXISTS policy (app_id INTEGER PRIMARY KEY, script TEXT, offline INTEGER);
        CREATE TABLE IF NOT EXISTS handled (app_id INTEGER, aid TEXT, installed_at TEXT,
          PRIMARY KEY(app_id,aid));
    """)
    if "installed_at" not in {r[1] for r in db.execute("PRAGMA table_info(inventory)")}:
        db.execute("ALTER TABLE inventory ADD COLUMN installed_at TEXT DEFAULT ''")
    migrate_categories(db)
    if not db.execute("SELECT 1 FROM meta WHERE key='catalog_v4'").fetchone():
        classify_pending(db)
        with db:
            db.execute("INSERT OR IGNORE INTO meta VALUES('catalog_v4','1')")
    return db


def is_application(row):
    kind = re.sub(r"[^a-z0-9]", "", str(row.get("software_type") or "").casefold())
    extension = row.get("browser_extension")
    evidence = any(extension.values()) if isinstance(extension,dict) else bool(extension)
    if row.get("extension_id") or evidence:
        return False
    if "_catalog_application" in row:
        return row["_catalog_application"]
    if kind:
        return kind in {"application","app","desktopapplication","installedapplication","softwareapplication"}
    return classify(row.get("name") or "",row.get("vendor") or "") != "Extensiones de navegador"


def ingest_pages(db, pages, progress, label, check_hosts=None, *, staging=False, cache=None, products=None):
    cache = {} if cache is None else cache
    target = "loading_inventory" if staging else "inventory"
    upsert = f"""INSERT INTO {target} VALUES(?,?,?,?,?,?,?)
        ON CONFLICT(app_id,host_key) DO UPDATE SET hostname=excluded.hostname,
        installed=max(installed,excluded.installed),used=max(used,excluded.used),
        installed_at=max(installed_at,excluded.installed_at)"""
    count = 0
    for page in pages:
        batch = []
        for row in page:
            if not is_application(row):
                continue
            name = str(row.get("name") or "").strip()
            if not name:
                continue
            host = row.get("host") or {}
            identity = (name, row.get("vendor") or "", host.get("platform_name") or "Desconocida")
            if identity not in cache:
                if products is not None:
                    products.add(name.casefold())
                db.execute("INSERT OR IGNORE INTO app(name,vendor,platform,category) VALUES(?,?,?,?)",
                           (*identity, classify(*identity, software_type=row.get("software_type") or "")))
                cache[identity] = db.execute("SELECT id FROM app WHERE name=? AND vendor=? AND platform=?",
                                             identity).fetchone()[0]
            aid = str(host.get("aid") or "").lower()
            if not re.fullmatch("[0-9a-f]{32}", aid):
                aid = ""
            key = aid or host.get("id") or row.get("id")
            if not key:
                raise ValueError("Falcon devolvió una detección sin identificador.")
            methods = {str(m).strip().casefold() for m in row.get("discovery_methods") or []}
            usage_methods = {"used", "usage", "process activity"}
            usage_only = bool(methods) and methods <= usage_methods
            installed_at = row.get("installation_timestamp") or ""
            if installed_at.startswith("0001-01-01"):
                installed_at = ""
            installed = bool(methods & {"installed", "installation", "installation record"}
                             or (not usage_only and (installed_at or row.get("installation_paths"))))
            if check_hosts is not None and aid and not installed:
                prior = db.execute("SELECT installed FROM inventory WHERE app_id=? AND host_key=?",
                                   (cache[identity],key)).fetchone()
                if prior and prior[0]:
                    check_hosts.add(aid)
            entry = (cache[identity],key,aid,host.get("hostname") or key,installed,
                     bool(row.get("last_used_timestamp") or methods & usage_methods), installed_at if installed else "")
            if staging:
                batch.append(entry)
            else:
                db.execute(upsert,entry)
            count += 1
        if staging:
            db.executemany(upsert,batch)
        else:
            progress(f"{label} · {count:,} registros leídos · {len(cache):,} fichas")


def load_catalog(db, service, progress, *, restart=False):
    with db:
        db.execute("INSERT OR IGNORE INTO loading_run VALUES(1,?,'',0,0)",(now(),))
    run = db.execute("SELECT * FROM loading_run").fetchone()
    cache = {} if restart else {(r["name"],r["vendor"],r["platform"]):r["id"] for r in db.execute(
        "SELECT * FROM app WHERE id IN (SELECT DISTINCT app_id FROM loading_inventory)")}
    products = {key[0].casefold() for key in cache}
    scanned = 0 if restart else run["scanned"]
    started = now() if restart else run["started"]
    initial_count = scanned
    began = time.monotonic()
    if restart or not run["ready"]:
        pages = service.batches(after="" if restart else run["cursor"],previous=scanned)
        for page, cursor, total in prefetch_pages(pages):
            with db:
                if restart:
                    db.execute("DELETE FROM loading_inventory")
                    db.execute("UPDATE loading_run SET started=? WHERE id=1",(started,))
                    restart = False
                ingest_pages(db,[page],progress,"Catálogo",staging=True,cache=cache,products=products)
                scanned += len(page)
                db.execute("UPDATE loading_run SET cursor=?,scanned=?,ready=? WHERE id=1",
                           (cursor or "",scanned,int(not cursor)))
            amount = f"{scanned:,} de {total:,}" if isinstance(total,int) and total>=scanned else f"{scanned:,}"
            elapsed = time.monotonic() - began
            speed = ""
            if elapsed >= 5 and scanned > initial_count:
                rate = (scanned-initial_count)*60/elapsed
                speed = f" · {rate:,.0f} reg/min"
                if isinstance(total,int) and total > scanned:
                    speed += f" · quedan aprox. {max(1,round((total-scanned)/rate))} min"
            progress(f"Catálogo parcial · {len(products):,} aplicaciones · {amount} registros{speed}")
    progress("Publicando el inventario de aplicaciones…")
    classify_pending(db)
    with db:
        db.execute("BEGIN")
        comparable = db.execute("SELECT 1 FROM meta WHERE key='applications_scope'").fetchone()
        if comparable:
            capture_installs(db)
        db.execute("DELETE FROM inventory")
        db.execute("INSERT INTO inventory SELECT * FROM loading_inventory")
        if comparable:
            finish_comparison(db,now())
        db.execute("DELETE FROM loading_inventory")
        db.execute("DELETE FROM loading_run")
        db.executemany("INSERT OR REPLACE INTO meta VALUES(?,?)",
                       [("applications_scope","1"),("sync",now()),("full_sync",started),("watermark",started)])


def prefetch_pages(pages):
    # Un solo lector de red. SQLite guarda en orden únicamente las páginas completas.
    with ThreadPoolExecutor(max_workers=1) as reader:
        page = next(pages, None)
        while page is not None:
            following = reader.submit(next, pages, None) if page[1] else None
            yield page
            page = following.result() if following else None


def capture_installs(db, *, reviewed_hosts=False, app_id=None):
    db.execute("DROP TABLE IF EXISTS temp.previous_installs")
    sql = "SELECT app_id,host_key,hostname FROM inventory WHERE installed=1"
    if reviewed_hosts:
        sql += " AND host_key IN (SELECT aid FROM review_hosts)"
    if app_id is not None:
        sql += " AND app_id=?"
    db.execute("CREATE TEMP TABLE previous_installs AS " + sql, (app_id,) if app_id is not None else ())


def finish_comparison(db, stamp):
    db.execute("""INSERT INTO removal(app_id,host_key,hostname,stamp)
               SELECT p.app_id,p.host_key,p.hostname,? FROM previous_installs p
               WHERE NOT EXISTS(SELECT 1 FROM inventory i WHERE i.app_id=p.app_id
               AND i.host_key=p.host_key AND i.installed=1)""",(stamp,))
    db.execute("""DELETE FROM handled WHERE (app_id,aid) IN (
        SELECT p.app_id,p.host_key FROM previous_installs p WHERE NOT EXISTS
        (SELECT 1 FROM inventory i WHERE i.app_id=p.app_id AND i.host_key=p.host_key AND i.installed=1))""")
    db.execute("DROP TABLE previous_installs")


def replace_inventory(db, pages, progress, started=None):
    started = started or now()
    with db:
        db.execute("BEGIN")
        capture_installs(db)
        db.execute("DELETE FROM inventory")
        ingest_pages(db,pages,progress,"Lectura completa")
        finish_comparison(db,now())
        db.executemany("INSERT OR REPLACE INTO meta VALUES(?,?)",
                       [("sync",now()),("watermark",started),("full_sync",started)])


def demo_removals(db, service):
    service.removed = set(tuple(r) for r in db.execute("""SELECT a.name,j.aid FROM job j JOIN app a
        ON a.id=j.app_id WHERE j.status='Ausencia confirmada por script'"""))


def verify_product(db, service, app_id, progress):
    app = db.execute("SELECT name,vendor,platform FROM app WHERE id=?",(app_id,)).fetchone()
    name = app["name"].replace("\\","\\\\").replace("'","\\'")
    if isinstance(service,Demo):
        demo_removals(db,service)
        pages = service.pages()
    else:
        pages = service.pages(f"name:'{name}'")
    def matching_pages():
        for page in pages:
            yield [r for r in page if (str(r.get("name") or "").strip(),r.get("vendor") or "",
                   (r.get("host") or {}).get("platform_name") or "Desconocida")==tuple(app)]
    with db:
        db.execute("BEGIN")
        capture_installs(db,app_id=app_id)
        db.execute("DELETE FROM inventory WHERE app_id=?",(app_id,))
        ingest_pages(db,matching_pages(),progress,app["name"])
        finish_comparison(db,now())


def update_inventory(db, service, progress, full=False):
    meta = dict(db.execute("SELECT key,value FROM meta"))
    started = now()
    last_full = meta.get("full_sync") or meta.get("sync")
    due = not last_full or datetime.fromisoformat(started)-datetime.fromisoformat(last_full)>=timedelta(days=7)
    if isinstance(service,Demo):
        demo_removals(db,service)
        full = True
    if isinstance(service,Falcon) and (full or due or "applications_scope" not in meta or
                                       db.execute("SELECT 1 FROM loading_run").fetchone()):
        try:
            load_catalog(db,service,progress,restart=full)
        except ExpiredSearch:
            progress("Caducó la búsqueda en Falcon. Iniciando una lectura completa desde la primera página…")
            try:
                load_catalog(db,service,progress,restart=True)
            except ExpiredSearch as err:
                raise ValueError("Falcon volvió a caducar la búsqueda. El avance parcial está guardado. "
                                 "Pulsa Actualizar para volver a intentarlo.") from err
        return
    if full or due:
        replace_inventory(db,service.pages(),progress,started)
        return
    # La versión anterior guardaba el fin de la lectura, pero no su inicio.
    anchor = datetime.fromisoformat(meta.get("watermark") or meta["sync"])
    overlap = timedelta(minutes=15) if "watermark" in meta else timedelta(days=1)
    since = (anchor-overlap).astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    with db:
        db.execute("BEGIN")
        pending = db.execute("""SELECT j.id,j.aid,j.app_id,j.status FROM job j WHERE
            j.status IN ('Ausencia confirmada por script','Finalizado · verificar','Finalizado con errores')
            AND NOT EXISTS(SELECT 1 FROM verified_job v WHERE v.id=j.id)""").fetchall()
        hosts = {r["aid"] for r in pending}
        ingest_pages(db,service.pages(f"last_updated_timestamp:>='{since}'"),progress,"Cambios",hosts)
        if hosts:
            db.execute("CREATE TEMP TABLE IF NOT EXISTS review_hosts(aid TEXT PRIMARY KEY)")
            db.execute("DELETE FROM review_hosts")
            db.executemany("INSERT INTO review_hosts VALUES(?)",((h,) for h in hosts))
            capture_installs(db,reviewed_hosts=True)
            db.execute("DELETE FROM inventory WHERE host_key IN (SELECT aid FROM review_hosts)")
            ordered = sorted(hosts)
            for pos in range(0,len(ordered),40):
                batch = ordered[pos:pos+40]
                if not all(re.fullmatch("[0-9a-f]{32}",aid) for aid in batch):
                    raise ValueError("Identificador de sensor inesperado al comprobar instalaciones.")
                fql = "host.aid:[" + ",".join("'" + aid + "'" for aid in batch) + "]"
                ingest_pages(db,service.pages(fql),progress,f"Verificando {pos+len(batch)} de {len(hosts)} equipos")
            finish_comparison(db,now())
            for j in pending:
                db.execute("""INSERT OR IGNORE INTO verified_job SELECT ? WHERE ?='Finalizado con errores' OR NOT EXISTS(
                    SELECT 1 FROM inventory WHERE app_id=? AND host_key=? AND installed=1)""",
                           (j["id"],j["status"],j["app_id"],j["aid"]))
        db.executemany("INSERT OR REPLACE INTO meta VALUES(?,?)",
                       [("sync",now()),("watermark",started),("full_sync",last_full)])


def cloud_name(app, source):
    slug = re.sub(r"[^a-zA-Z0-9]+", "-", app["name"]).strip("-")[:32] or "App"
    digest = hashlib.sha256(source.encode("utf-8")).hexdigest()[:16]
    return f"Desinstalar-{slug}-{digest}"


# Resultado visible: conservar siempre el estado RTR original en job/event.
JOB_RESULT_SQL = """CASE WHEN j.status IN (
    'Finalizado con errores','Finalizado · verificar','Ausencia confirmada por script')
    AND EXISTS(SELECT 1 FROM removal r WHERE r.app_id=j.app_id AND r.host_key=j.aid
               AND julianday(r.stamp)>=julianday(j.updated))
    AND NOT EXISTS(SELECT 1 FROM inventory i WHERE i.app_id=j.app_id
                   AND i.host_key=j.aid AND i.installed=1)
    THEN 'Ya no figura instalado' ELSE j.status END"""


def job_result(db, job_id):
    return db.execute("SELECT "+JOB_RESULT_SQL+" FROM job j WHERE j.id=?",(job_id,)).fetchone()[0]


def set_state(db, job, status, detail="", **fields):
    values = dict(status=status, detail=detail[:4000], updated=now(), **fields)
    with db:
        db.execute("UPDATE job SET " + ",".join(f"{k}=?" for k in values) + " WHERE id=?",
                   (*values.values(), job))
        db.execute("INSERT INTO event(job_id,stamp,status,detail) VALUES(?,?,?,?)",
                   (job, values["updated"], status, values["detail"]))


def plan_rows(db, app_id, aids, offline, campaign):
    created = []
    for aid in dict.fromkeys(aids):
        cur = db.execute("""INSERT OR IGNORE INTO job
            (campaign,app_id,aid,hostname,script,offline,status,updated)
            SELECT ?,app.id,i.aid,i.hostname,app.script,?,'Preparado',?
            FROM inventory i JOIN app ON app.id=i.app_id
            WHERE app.id=? AND i.aid=? AND i.aid<>'' AND i.installed=1 AND app.script<>''""",
                         (campaign, offline, now(), app_id, aid))
        if cur.rowcount:
            created.append(cur.lastrowid)
            db.execute("INSERT INTO event(job_id,stamp,status,detail) VALUES(?,?,'Preparado','')",
                       (cur.lastrowid, now()))
    return created


def plan(db, app_id, aids, offline, campaign):
    with db:
        return plan_rows(db, app_id, aids, offline, campaign)


def disable_policy(db, app_id):
    with db:
        db.execute("DELETE FROM policy WHERE app_id=?", (app_id,))
        db.execute("DELETE FROM handled WHERE app_id=?", (app_id,))
        for r in db.execute("SELECT id FROM job WHERE app_id=? AND campaign LIKE 'Auto-%' AND status='Preparado'",
                            (app_id,)).fetchall():
            db.execute("UPDATE job SET status='Cancelado',updated=? WHERE id=?", (now(), r[0]))
            db.execute("INSERT INTO event(job_id,stamp,status,detail) VALUES(?,?,'Cancelado','Regla desactivada')",
                       (r[0],now()))


def automatic_jobs(db):
    """Evaluar solo después de descargar un inventario completo."""
    with db:
        db.execute("""DELETE FROM handled WHERE NOT EXISTS (SELECT 1 FROM inventory i
            WHERE i.app_id=handled.app_id AND i.aid=handled.aid AND i.installed=1)""")
        rows = db.execute("""SELECT i.app_id,i.aid,i.installed_at,p.offline
            FROM policy p JOIN app a ON a.id=p.app_id AND a.script=p.script
            JOIN inventory i ON i.app_id=a.id AND i.installed=1 AND i.aid<>''
            LEFT JOIN handled h ON h.aid=i.aid AND h.app_id=i.app_id
            WHERE h.aid IS NULL OR (i.installed_at<>'' AND i.installed_at>h.installed_at)""").fetchall()
        campaign = "Auto-" + uuid.uuid4().hex[:8]
        for row in rows:
            plan_rows(db,row["app_id"],[row["aid"]],row["offline"],campaign)
            db.execute("INSERT OR REPLACE INTO handled VALUES(?,?,?)",
                       (row["app_id"],row["aid"],row["installed_at"]))
        # No enviar una orden preparada antes de un cierre si la instalación ya desapareció.
        stale = db.execute("""SELECT j.id FROM job j WHERE j.status='Preparado' AND j.campaign LIKE 'Auto-%'
            AND NOT EXISTS (SELECT 1 FROM inventory i JOIN policy p ON p.app_id=i.app_id
            WHERE i.app_id=j.app_id AND i.aid=j.aid AND i.installed=1 AND j.script=p.script)""").fetchall()
        for r in stale:
            db.execute("UPDATE job SET status='Cancelado',updated=? WHERE id=?", (now(),r[0]))
            db.execute("INSERT INTO event(job_id,stamp,status,detail) VALUES(?,?,'Cancelado','Detección o regla ausente')",
                       (r[0],now()))
        return [r[0] for r in db.execute("SELECT id FROM job WHERE campaign LIKE 'Auto-%' AND status='Preparado'")]


class FalconError(RuntimeError):
    def __init__(self, code, message):
        super().__init__(f"Falcon ({code}) · {message}")
        self.code = code


class ExpiredSearch(FalconError):
    """Falcon rechazó la continuación de una consulta paginada."""


def body(response):
    code = response["status_code"]
    data = response.get("body") or {}
    errors = data.get("errors", []) if isinstance(data, dict) else []
    if not 200 <= code < 300 or errors:
        raise FalconError(code, " / ".join(str(e.get("message") or e) for e in errors) or "Solicitud rechazada")
    return data


class ScriptNotPublished(ValueError):
    pass


def rtr_script_binding(record, platform):
    """Validate the exact remote script before linking it to an application."""
    name = record.get("name", "")
    if not isinstance(name, str) or not re.fullmatch(r"[\w .()-]{1,200}", name):
        raise ValueError("El nombre del script no es compatible con el comando RTR.")
    platforms = record.get("platform", [])
    if isinstance(platforms, str):
        platforms = [platforms]
    expected = {"macos":"mac"}.get(platform.casefold(), platform.casefold())
    if not isinstance(platforms, list) or expected not in [str(p).casefold() for p in platforms]:
        raise ValueError("La plataforma del script no coincide con la aplicación.")
    content = record.get("content")
    digest = str(record.get("sha256") or "").lower()
    if (not isinstance(content, str) or not content.strip() or not record.get("id")
            or hashlib.sha256(content.encode("utf-8")).hexdigest() != digest):
        raise ValueError("Falcon no devolvió contenido, identificador y hash verificables del script.")
    return content, {"name":name, "id":record["id"], "sha256":digest}


def save_uninstaller(db, service, app, source, binding):
    digest = hashlib.sha256(source.encode("utf-8")).hexdigest()
    linked = bool(binding and digest == binding["sha256"])
    name = binding["name"] if linked else (cloud_name(app, source) if source.strip() else "")
    policy = db.execute("SELECT script FROM policy WHERE app_id=?", (app["id"],)).fetchone()
    if policy and policy[0] != name:
        raise ValueError("Desactiva la regla de este programa antes de cambiar su script.")
    with db:
        db.execute("UPDATE app SET draft=?,script=? WHERE id=?", (source, name, app["id"]))
        key = "rtr_binding:" + str(app["id"])
        if linked:
            db.execute("INSERT OR REPLACE INTO meta VALUES(?,?)", (key, json.dumps(binding)))
        else:
            db.execute("DELETE FROM meta WHERE key=?", (key,))
    if linked:
        service.script_bindings[name] = dict(binding)
    return name


class Falcon:
    def __init__(self, client_id, secret, region):
        from falconpy import Discover, Hosts, RealTimeResponse, RealTimeResponseAdmin
        options = dict(client_id=client_id, client_secret=secret, base_url=region, timeout=45)
        self.discover = Discover(**options)
        self.hosts = Hosts(**options)
        self.rtr = RealTimeResponse(**options)
        self.admin = RealTimeResponseAdmin(**options)
        self.application_kinds = {"application","app","desktopapplication","installedapplication","softwareapplication"}
        self.script_bindings = {}
        self.remote_type = ""
        self.include_untyped = False

    def inspect_inventory(self):
        """Comprobar la forma de los datos con lecturas pequeñas en la cuenta conectada."""
        facets = ["host_info","install_usage","browser_extension"]
        examples = []
        app_kind = ""
        ext_kind = ""
        for name in ("Chrome","Adblock Plus - free ad blocker","Roblox Studio"):
            rows = body(self.discover.query_combined_applications(
                filter=f"name:'{name}'",limit=2,facet=facets))["resources"]
            for r in rows:
                kind = str(r.get("software_type") or "")
                ext = r.get("browser_extension") or {}
                examples.append({"name":r.get("name"),"vendor":r.get("vendor"),"software_type":kind,
                                 "discovery_methods":r.get("discovery_methods"),"extension_id_present":bool(r.get("extension_id")),
                                 "extension_fields":sorted(ext) if isinstance(ext,dict) else [],
                                 "fields":sorted(r),"host_fields":sorted(r.get("host") or {})})
                if name=="Chrome" and str(r.get("vendor") or "").casefold() in {"google","google llc","google inc."}:
                    app_kind = kind
                if name.startswith("Adblock"):
                    ext_kind = kind
        chrome = [r for r in examples if r["name"]=="Chrome" and not r["software_type"]]
        extensions = [r for r in examples if r["name"]=="Adblock Plus - free ad blocker"]
        self.include_untyped = bool(chrome and extensions and all(
            r["extension_id_present"] or r["extension_fields"] or "extension" in r["software_type"].casefold()
            for r in extensions))
        if re.fullmatch(r"[\w -]{1,50}",app_kind) and ext_kind and ext_kind!=app_kind:
            self.application_kinds.add(re.sub(r"[^a-z0-9]","",app_kind.casefold()))
            try:
                for name,expected in (("Chrome",True),("Adblock Plus - free ad blocker",False)):
                    probe = body(self.discover.query_combined_applications(
                        filter=f"name:'{name}'+software_type:'{app_kind}'",limit=1,facet=facets))
                    if bool(probe["resources"])!=expected:
                        break
                else:
                    self.remote_type = app_kind
            except FalconError as err:
                if err.code not in (400,422):
                    raise
        return {"examples":examples,"server_filter":self.remote_type,"observed":now()}

    def pages(self, fql="name:!null"):
        for rows,_,_ in self.batches(fql):
            yield rows

    def batches(self, fql="name:!null", after="", previous=0):
        if self.remote_type:
            fql += f"+software_type:'{self.remote_type}'"
        params = dict(limit=1000, filter=fql, facet=["host_info", "install_usage","browser_extension"])
        seen = set()
        if after:
            params["after"] = after
            seen.add(after)
        count = previous
        while True:
            try:
                data = body(self.discover.query_combined_applications(**params))
            except FalconError as err:
                message = str(err).casefold()
                cursor_error = (any(word in message for word in ("cursor","after","search context","pagination token"))
                                and any(word in message for word in ("expir","invalid","no longer valid","not found")))
                if params.get("after") and err.code in (400,404,410) and (cursor_error or err.code==410):
                    raise ExpiredSearch(err.code,"El punto de continuación de Falcon ha caducado.") from err
                raise
            rows = data["resources"]
            for row in rows:
                if isinstance(row,dict):
                    kind = re.sub(r"[^a-z0-9]","",str(row.get("software_type") or "").casefold())
                    row["_catalog_application"] = kind in self.application_kinds if kind else self.include_untyped
            count += len(rows)
            paging = data["meta"]["pagination"]
            token = paging.get("after")
            if token in seen:
                raise ValueError("Falcon repitió una página. Se conserva el inventario anterior.")
            if not token:
                if int(paging.get("total") or 0) > count:
                    raise ValueError("Falta la página siguiente. Se conserva el inventario anterior.")
            yield rows,token,paging.get("total")
            if not token:
                return
            seen.add(token)
            params["after"] = token

    def online_states(self, aids):
        rows = body(self.hosts.get_online_state(ids=list(aids)))["resources"]
        labels = {"online":"En línea", "offline":"Desconectado", "unknown":"Desconocido"}
        return {r["id"]:labels.get(str(r.get("state")).strip().lower(), "Desconocido") for r in rows if r.get("id")}

    def host_presence(self,aids):
        aids = list(aids)
        states = self.online_states(aids)
        last_seen = {}
        warning = ""
        for start in range(0,len(aids),100):
            try:
                records = body(self.hosts.get_device_details(ids=aids[start:start+100]))["resources"]
                for record in records:
                    aid = record.get("device_id") or record.get("id")
                    if aid and record.get("last_seen"):
                        last_seen[aid] = record["last_seen"]
            except Exception:
                warning = "Last seen no disponible; revisa el acceso a Hosts o vuelve a consultar."
        return states,last_seen,warning

    def session(self, job):
        return body(self.rtr.init_session(device_id=job["aid"], queue_offline=bool(job["offline"])))["resources"][0]

    def library_scripts(self):
        offset = "0"
        records = []
        seen = set()
        used_offsets = set()
        while True:
            used_offsets.add(offset)
            data = body(self.admin.list_scripts(limit=100, offset=offset))
            ids = data["resources"]
            if not ids:
                break
            pagination = data.get("meta",{}).get("pagination") or {}
            fresh = list(dict.fromkeys(i for i in ids if i not in seen))
            if not fresh:
                detail = json.dumps({"offset_solicitado":offset,"recibidos":len(ids),
                                     "unicos_leidos":len(seen),"paginacion":pagination},ensure_ascii=False)
                raise ValueError("La biblioteca RTR no avanzó de página. Detalle: " + detail)
            seen.update(fresh)
            for start in range(0,len(fresh),100):
                metadata = body(self.admin.get_scripts_v2(ids=fresh[start:start+100]))["resources"]
                records.extend(metadata)
            # Sin metadatos de paginación, RTR devuelve una lista completa.
            # No inventar una continuación a partir de la cantidad solicitada.
            if not pagination:
                break
            total = pagination.get("total")
            total = int(total) if str(total).isdigit() else None
            if total is not None and len(seen) >= total:
                break
            server_limit = pagination.get("limit")
            server_limit = int(server_limit) if str(server_limit).isdigit() and int(server_limit)>0 else 100
            if total is None and len(ids)<server_limit:
                break
            supplied_offset = pagination.get("offset")
            # Conservar los cursores opacos cuando Falcon los proporcione.
            if supplied_offset is not None and not str(supplied_offset).isdigit():
                next_offset = str(supplied_offset)
            else:
                current = int(offset) if offset.isdigit() else len(seen)-len(fresh)
                next_offset = str(current+len(ids))
            if next_offset in used_offsets:
                raise ValueError("Falcon devolvió una continuación RTR repetida: " + json.dumps(pagination))
            offset = next_offset
        return records

    def verify(self, script):
        binding = getattr(self,"script_bindings",{}).get(script)
        if binding:
            matches = [r for r in body(self.admin.get_scripts_v2(ids=[binding["id"]]))["resources"] if r.get("name")==script]
        else:
            if not re.fullmatch(r"Desinstalar-[a-zA-Z0-9-]+-[0-9a-f]{16}", script):
                raise ValueError("Publica el script desde la ficha de la aplicación antes de enviarlo.")
            matches = [r for r in self.library_scripts() if r.get("name")==script]
        if not matches:
            raise ScriptNotPublished("El script no está publicado. Usa Publicar en Falcon en la ficha.")
        if len(matches) != 1:
            raise ValueError("Hay varios scripts con el mismo nombre RTR. Revisa la biblioteca de Falcon.")
        metadata = matches[0]
        digest = str(metadata.get("sha256") or "").lower()
        expected = binding["sha256"] if binding else script.rsplit("-",1)[1]
        if metadata.get("name") != script or not (digest == expected if binding else digest.startswith(expected)):
            raise ValueError("El contenido publicado en RTR difiere del archivo exportado.")

    def publish_script(self, app, source):
        if not source.strip():
            raise ValueError("El script está vacío.")
        platform = {"windows":"windows","mac":"mac","macos":"mac","linux":"linux"}.get(app["platform"].casefold())
        if platform is None:
            raise ValueError("Plataforma no compatible con scripts RTR.")
        name = cloud_name(app,source)
        try:
            self.verify(name)
            return "El script ya estaba publicado y su contenido coincide."
        except ScriptNotPublished:
            pass
        ext = ".ps1" if platform=="windows" else ".sh"
        body(self.admin.create_scripts(
            name=name,description="Desinstalador de "+app["name"]+" · GestorFalcon",
            platform=platform,permission_type="group",
            comments_for_audit_log="Publicación desde GestorFalcon",
            files=[("file",(name+ext,source.encode("utf-8"),"application/script"))]))
        self.verify(name)
        return "Script publicado y contenido verificado en Falcon."

    def submit(self, job, session):
        script = job["script"]
        return body(self.admin.execute_admin_command(session_id=session, base_command="runscript",
                    command_string=f'runscript -CloudFile="{script}"', persist=bool(job["offline"])))["resources"][0]

    def status(self, job):
        return body(self.admin.check_admin_command_status(cloud_request_id=job["request"],
                                                          sequence_id=job["seq"]))["resources"][0]


def dispatch(db, service, ids, progress):
    verified = {}
    for index, jid in enumerate(ids, 1):
        job = db.execute("SELECT * FROM job WHERE id=?", (jid,)).fetchone()
        if job["status"] != "Preparado":
            continue
        submitting = False
        try:
            script = job["script"]
            if script not in verified:
                try:
                    service.verify(script)
                    verified[script] = ""
                except ValueError as err:
                    verified[script] = str(err)
            if verified[script]:
                raise ValueError(verified[script])
            session = service.session(job)
            sid = session["session_id"]
            set_state(db, jid, "Enviando", session=sid)
            submitting = True
            result = service.submit(job, sid)
            queued = result.get("queued_command_offline", session.get("offline_queued", False))
            set_state(db, jid, "En cola" if queued else "Enviado", request=result["cloud_request_id"])
        except Exception as err:
            uncertain = submitting and not (isinstance(err, FalconError) and 400 <= err.code < 500)
            set_state(db, jid, "Revisar en Falcon" if uncertain else "Error", str(err))
            if isinstance(err, FalconError) and err.code in (401, 403, 429):
                raise ValueError(f"{err}. Los envíos aún preparados se pueden retomar desde Seguimiento.") from err
        progress(f"Campaña · {index} de {len(ids)} equipos tramitados")


def poll(db, service, progress):
    jobs = db.execute("SELECT * FROM job WHERE status IN ('En cola','Enviado','En curso') ORDER BY updated,id").fetchall()
    for index, job in enumerate(jobs, 1):
        try:
            result = service.status(job)
            output = (job["output"] + str(result.get("stdout") or ""))[-10000:]
            error = str(result.get("stderr") or "")
            seq = job["seq"]
            if result.get("complete") is True:
                state = "Finalizado · verificar"
                if error or "[stderr]" in output:
                    state = "Finalizado con errores"
                elif "APP_ABSENT" in output.splitlines():
                    state = "Ausencia confirmada por script"
                set_state(db, job["id"], state, error or output, output=output)
            elif result.get("stdout") or error:
                seq = int(result.get("sequence_id", seq)) + 1
                if error:
                    output = (output + "\n[stderr] " + error + "\n")[-10000:]
                set_state(db, job["id"], "En curso", error or output, seq=seq, output=output)
        except Exception as err:
            message = str(err)
            if message != job["detail"]:
                set_state(db, job["id"], job["status"], message)
            if isinstance(err, FalconError) and err.code in (401, 403, 429):
                break
        progress(f"Seguimiento · {index} de {len(jobs)}")


class Demo:
    def online_states(self, aids):
        return {aid:("Desconectado" if aid.endswith("3") else "En línea") for aid in aids}

    def verify(self, script):
        pass

    def pages(self):
        records = []
        for name, vendor, targets in [
            ("Minecraft", "Mojang", [1, 2, 3]), ("Roblox Studio", "Roblox Corporation", [1, 2, 3]),
            ("Roblox Player", "Roblox Corporation", [2]), ("Steam", "Valve", [1, 3]),
            ("Chrome", "Google", [1, 2, 3, 4]), ("Chrome Installer", "Google", [4]),
            ("Juego del laboratorio", "Estudio Demo", [2]), ("7-Zip", "Igor Pavlov", [2, 3]),
        ]:
            for n in targets:
                if (name,f"{n:032x}") in getattr(self,"removed",set()):
                    continue
                records.append(dict(name=name, vendor=vendor, host=dict(aid=f"{n:032x}", hostname=f"PC-DEMO-{n:02}",
                                    platform_name="Windows"), installation_paths=[] if name=="Chrome Installer" else ["demo"],
                                    last_used_timestamp="2026-01-01"))
        yield records

    def host_presence(self,aids):
        states = self.online_states(aids)
        return states,{aid:(datetime.now(timezone.utc)-timedelta(
            hours=26 if state=="Desconectado" else 0)).isoformat(timespec="seconds")
            for aid,state in states.items()},""

    def session(self, job):
        offline = job["aid"].endswith("3")
        if offline and not job["offline"]:
            raise ValueError("Equipo de demostración apagado.")
        return dict(session_id="demo-" + job["aid"], offline_queued=offline)

    def submit(self, job, session):
        return dict(cloud_request_id=f"demo-{job['id']}")

    def status(self, job):
        # Un ciclo de seguimiento simula la reconexión y la salida del desinstalador.
        return dict(complete=True, stdout="APP_ABSENT\n")


def read_theme(directory):
    try:
        return (directory/"tema.txt").read_text(encoding="utf8").strip()=="oscuro"
    except OSError:
        return False


def product_icon(root, name, size):
    name=name.casefold()
    image=tk.PhotoImage(master=root,width=size,height=size)
    for y in range(size):
        for x in range(size):
            u,v=(x+.5)/size,(y+.5)/size
            if name.startswith("roblox"):
                dx,dy=u-.5,v-.5
                edge=max(abs(.96*dx+.28*dy),abs(-.28*dx+.96*dy))
                if not .105<edge<.37:
                    continue
                color="#1598de" if "studio" in name else "#717781"
            elif name=="steam":
                if (u-.5)**2+(v-.5)**2>.225:
                    continue
                gear=(u-.69)**2+(v-.34)**2
                arm=abs(v-(.98-.9*u))<.055 and .34<u<.69
                color="#f0f6fc" if .007<gear<.022 or arm else "#214868"
            else:
                if not (.09<u<.91 and .15<v<.85):
                    continue
                color="#b02a44" if v<.35 or u<.16 or u>.84 or v>.77 else "#f5ccd4"
            image.put(color,(x,y))
    return image


def icon_family(name):
    label = name.casefold()
    if label.startswith("roblox studio"):
        return "roblox-studio"
    if label.startswith("roblox"):
        return "roblox-player"
    if label == "steam" or label.startswith("steam "):
        return "steam"
    return "generico"


def custom_icon_filename(name):
    slug = re.sub(r"[^a-z0-9]+","-",name.casefold()).strip("-")[:60] or "aplicacion"
    digest = hashlib.sha256(name.casefold().encode("utf-8")).hexdigest()[:10]
    return slug+"-"+digest+".png"


def normalize_icon_name(name):
    name = unicodedata.normalize("NFKC",name).casefold().replace("®","").replace("™","")
    name = re.sub(r"\.(app|exe)$","",name)
    return " ".join(name.split())


def ensure_icon_assets(directory):
    """Expand the bundled public graphics locally; never fetch an account's inventory."""
    directory = Path(directory)
    archive = directory / "recursos.zip"
    if not archive.exists():
        return
    digest = hashlib.sha256(archive.read_bytes()).hexdigest()
    marker = directory / ".recursos-version"
    try:
        if marker.read_text(encoding="ascii").strip() == digest:
            return
    except OSError:
        pass
    with zipfile.ZipFile(archive) as bundle:
        entries = bundle.infolist()
        if len(entries) > 6000 or sum(e.file_size for e in entries) > 100_000_000:
            raise ValueError("El paquete de iconos excede el tamaño admitido.")
        for entry in entries:
            if (not re.fullmatch(r"(?:familias|generados|fuentes-papirus)/[a-zA-Z0-9_.-]+\.(?:png|svg)", entry.filename)
                    or ".." in Path(entry.filename).parts or entry.file_size > 5_000_000):
                raise ValueError("Ruta no válida en el paquete de iconos.")
        for entry in entries:
            destination = directory / entry.filename
            destination.parent.mkdir(parents=True, exist_ok=True)
            temporary = destination.with_suffix(destination.suffix + ".tmp")
            temporary.write_bytes(bundle.read(entry))
            os.replace(temporary, destination)
    marker.write_text(digest + "\n", encoding="ascii")


class IconLibrary:
    def __init__(self, root, directory):
        self.root = root
        self.directory = Path(directory)
        ensure_icon_assets(self.directory)
        self.vendor_rules = self.read_rules("fabricantes.json", [])
        self.category_icons = self.read_rules("categorias.json", {})
        self.cache = {}
        self.catalog = {}
        self.brand_rules = []
        try:
            rules = json.loads((self.directory/"reglas.json").read_text(encoding="utf-8"))
            self.brand_rules = sorted((r for r in rules if isinstance(r,dict)
                and isinstance(r.get("alias"),str) and r["alias"]
                and isinstance(r.get("archivo"),str)
                and re.fullmatch(r"familias/[a-z0-9-]+\.png",r["archivo"])),
                key=lambda r:len(r["alias"]),reverse=True)
        except (OSError,ValueError,TypeError):
            pass
        self.exact_brand_rules = {r["alias"]:r for r in self.brand_rules if r.get("modo")=="exacto"}
        self.brand_rules = [r for r in self.brand_rules if r.get("modo")!="exacto"]
        self.dirty = True
        self.available = True
        try:
            (self.directory/"generados").mkdir(parents=True,exist_ok=True)
            (self.directory/"personalizados").mkdir(exist_ok=True)
            try:
                previous = json.loads((self.directory/"catalogo.json").read_text(encoding="utf-8"))
                if isinstance(previous,dict):
                    self.register(name for name in previous if isinstance(name,str))
            except (OSError,ValueError):
                pass
            for family in ("generico","roblox-player","roblox-studio","steam"):
                for size in (20,42):
                    self.generated(family,size)
        except (OSError,tk.TclError):
            self.available = False

    def read_rules(self, name, fallback):
        try:
            value = json.loads((self.directory/name).read_text(encoding="utf-8"))
            return value if isinstance(value, type(fallback)) else fallback
        except (OSError, ValueError):
            return fallback

    def register_apps(self, rows):
        """Derive manufacturer/category fallbacks from this installation's own inventory."""
        choices = {}
        for name, vendor, category, platform in rows:
            selected = self.brand_rule_for(name)
            if not selected:
                publisher = normalize_icon_name(vendor or "")
                for rule in self.vendor_rules:
                    alias = rule.get("alias", "")
                    if alias and (publisher == alias or (publisher.startswith(alias)
                            and publisher[len(alias):len(alias)+1] in " .,(-")):
                        selected = {"archivo": rule["archivo"], "tipo": "fabricante"}
                        break
            if not selected:
                selected = {"archivo": self.category_icons.get(category,
                    self.category_icons.get("Sin clasificar", "")), "tipo": "categoría"}
            choices.setdefault(name, []).append(selected)
        self.register(choices)
        for name, candidates in choices.items():
            logos = {candidate.get("archivo") for candidate in candidates}
            # One name may have several publishers; never assign one publisher to all of them.
            chosen = candidates[0] if len(logos) == 1 else {
                "archivo": self.category_icons.get("Sin clasificar", ""), "tipo": "categoría"}
            current = self.catalog[name]
            if current.get("logo") != chosen["archivo"] or current.get("logo_tipo") != chosen.get("tipo", "producto"):
                current.update(logo=chosen["archivo"], logo_tipo=chosen.get("tipo", "producto"))
                self.dirty = True
        self.register(())

    def generated(self,family,size):
        path = self.directory/"generados"/f"{family}-{size}.png"
        key = ("generated",family,size)
        if key not in self.cache:
            try:
                picture = tk.PhotoImage(master=self.root,file=str(path))
                if picture.width()!=size or picture.height()!=size:
                    raise tk.TclError("Dimensiones no válidas")
            except (OSError,tk.TclError):
                picture = product_icon(self.root,family.replace("-"," ") if family!="generico" else "",size)
                try:
                    picture.write(str(path),format="png")
                except (OSError,tk.TclError):
                    pass
            self.cache[key] = picture
        return self.cache[key]

    def brand_rule_for(self,name):
        label = normalize_icon_name(name)
        for rule in self.brand_rules:
            alias = rule["alias"]
            if label==alias:
                return rule
            if label.startswith(alias):
                tail = label[len(alias):]
                if tail and (tail[0].isspace() or tail[0] in "(.:-" or tail[0].isdigit()):
                    return rule
        return self.exact_brand_rules.get(label)

    def brand_for(self,name):
        rule = self.brand_rule_for(name)
        return rule["archivo"] if rule else None

    def register(self,names):
        for name in names:
            if name not in self.catalog:
                family = icon_family(name)
                self.catalog[name] = {
                    "personalizado":"personalizados/"+custom_icon_filename(name),
                    "generado_20":f"generados/{family}-20.png",
                    "generado_42":f"generados/{family}-42.png"}
                rule = self.brand_rule_for(name)
                if rule:
                    self.catalog[name]["logo"] = rule["archivo"]
                    self.catalog[name]["logo_tipo"] = rule.get("tipo","producto")
                self.dirty = True
        if self.dirty and self.available:
            try:
                destination = self.directory/"catalogo.json"
                temporary = self.directory/"catalogo.json.tmp"
                temporary.write_text(json.dumps(self.catalog,ensure_ascii=False,indent=2,sort_keys=True),encoding="utf-8")
                os.replace(temporary,destination)
                self.dirty = False
            except OSError:
                pass

    def load_png(self,path,size):
        revision = path.stat().st_mtime_ns
        key = ("png",str(path),size)
        cached = self.cache.get(key)
        if cached is None or cached[0]!=revision:
            original = tk.PhotoImage(master=self.root,file=str(path))
            extent = max(original.width(),original.height())
            if extent<=0:
                raise tk.TclError("Imagen vacía")
            if original.width()==size and original.height()==size:
                picture = original
            else:
                width = max(1,round(original.width()*size/extent))
                height = max(1,round(original.height()*size/extent))
                picture = tk.PhotoImage(master=self.root,width=width,height=height)
                for y in range(height):
                    sy = min(original.height()-1,int(y*original.height()/height))
                    for x in range(width):
                        sx = min(original.width()-1,int(x*original.width()/width))
                        self.root.tk.call(str(picture),"copy",str(original),"-from",sx,sy,sx+1,sy+1,"-to",x,y)
            self.cache[key] = (revision,picture)
        return self.cache[key][1]

    def get(self,name,size):
        paths = [self.directory/"personalizados"/custom_icon_filename(name)]
        logo = self.catalog.get(name,{}).get("logo") or self.brand_for(name)
        if logo:
            base = self.directory/logo
            paths += [base.with_name(base.stem+f"-{size}.png"),base]
        for path in paths:
            try:
                return self.load_png(path,size)
            except (OSError,tk.TclError):
                continue
        return self.generated(icon_family(name),size)


def create_root():
    if sys.platform == "win32":
        import ctypes
        user32 = ctypes.windll.user32
        try:
            user32.SetProcessDpiAwarenessContext(ctypes.c_void_p(-4))
        except AttributeError:
            user32.SetProcessDPIAware()
    return tk.Tk()


def rounded_button_image(root,fill,border):
    width,height,radius = 28,24,6
    image = tk.PhotoImage(master=root,width=width,height=height)
    def inside(x,y,inset):
        if not inset<=x<width-inset or not inset<=y<height-inset:
            return False
        r = radius-inset
        cx = min(max(x,radius),width-radius)
        cy = min(max(y,radius),height-radius)
        return (x-cx)**2+(y-cy)**2<=r*r
    for y in range(height):
        for x in range(width):
            if inside(x+.5,y+.5,0):
                image.put(fill if inside(x+.5,y+.5,1) else border,(x,y))
    return image


def install_button_styles(root,style,bg,fg,soft,muted,line,accent,selected,dark):
    generation = getattr(root,"_button_generation",0)+1
    root._button_generation = generation
    images = []
    configurations = (
        ("TButton",bg,line,soft,fg,("Segoe UI",10)),
        ("Accent.TButton","#2563eb","#2563eb","#1d4ed8","#ffffff",("Segoe UI",10,"bold")),
        ("Danger.TButton","#c8172c","#c8172c","#a91325","#ffffff",("Segoe UI",10,"bold")),
        ("Brand.TButton","#c8172c","#c8172c","#a91325","#ffffff",("Segoe UI",11,"bold")),
        ("Side.TButton",bg,bg,soft,muted,("Segoe UI",10)),
        ("Active.Side.TButton",selected,selected,selected,fg,("Segoe UI",10,"bold")),
        ("Chip.TButton",selected,selected,selected,accent,("Segoe UI",10)),
    )
    for index,(name,fill,edge,hover,text,font) in enumerate(configurations):
        normal = rounded_button_image(root,fill,edge)
        active = rounded_button_image(root,hover,edge)
        disabled = rounded_button_image(root,soft,line)
        focused = rounded_button_image(root,fill,accent)
        images.extend((normal,active,disabled,focused))
        element = f"GfButton{generation}_{index}"
        style.element_create(element,"image",normal,("disabled",disabled),("pressed",active),
                             ("focus",focused),("active",active),border=6,sticky="nswe")
        style.layout(name,[(element,{"sticky":"nswe","children":[
            ("Button.padding",{"sticky":"nswe","children":[("Button.label",{"sticky":"nswe"})]})]})])
        style.configure(name,padding=(11,6),font=font,foreground=text,anchor="center",borderwidth=0)
        style.map(name,foreground=[("disabled",muted),("!disabled",text)])
    style.layout("Compact.Side.TButton",style.layout("Side.TButton"))
    style.configure("Compact.Side.TButton",padding=(8,4),font=("Segoe UI",10))
    style.layout("Active.Compact.Side.TButton",style.layout("Active.Side.TButton"))
    style.configure("Active.Compact.Side.TButton",padding=(8,4),font=("Segoe UI",10,"bold"))
    style.configure("CompactBrand.TLabel",font=("Segoe UI",12,"bold"))
    root._button_images = images


def crowdstrike_image(root,directory):
    ensure_icon_assets(Path(directory)/"iconos")
    try:
        return tk.PhotoImage(master=root,file=str(Path(directory)/"iconos"/"familias"/"crowdstrike-42.png"))
    except (OSError,tk.TclError):
        return None


def palette(root, dark=False):
    style = ttk.Style(root)
    style.theme_use("clam")
    bg, fg, soft, muted, line = (
        ("#151a23","#e7edf5","#202837","#a4b0c0","#344054") if dark else
        ("#ffffff","#243044","#f3f5f8","#64748b","#e2e8f0"))
    red, selected, match = (("#93baff","#263c5b","#3c5274") if dark else
                            ("#2563eb","#e8f0ff","#dbeafe"))
    style.configure(".",font=("Segoe UI",11),background=bg,foreground=fg,fieldbackground=bg,
                    bordercolor=line,lightcolor=bg,darkcolor=bg,focuscolor=red,arrowcolor=fg)
    style.configure("Title.TLabel",font=("Segoe UI",20,"bold"))
    style.configure("Section.TLabel",font=("Segoe UI",13,"bold"))
    style.configure("Muted.TLabel",foreground=muted)
    style.configure("Chip.TButton",background=selected,foreground=red,padding=(8,3))
    style.layout("TNotebook",[("Notebook.client",{"sticky":"nsew"})])
    style.layout("TNotebook.Tab",[("Notebook.padding",{"sticky":"nswe","children":[("Notebook.label",{"sticky":"nswe"})]})])
    style.configure("TNotebook",borderwidth=0,tabmargins=(0,2,0,8),background=bg)
    style.configure("TNotebook.Tab",padding=(14,7),background=bg,foreground=muted)
    style.map("TNotebook.Tab",background=[("selected",selected)],foreground=[("selected",red)])
    style.layout("Shell.TNotebook.Tab",[])
    style.configure("TButton",padding=(12,8),borderwidth=0,background=soft,relief="flat")
    style.configure("TEntry",padding=(10,7),borderwidth=1,relief="flat")
    style.configure("TCombobox",padding=(10,7),borderwidth=1,relief="flat")
    style.configure("TSeparator",background=line)
    style.map("TButton",background=[("active",line)])
    style.configure("Accent.TButton",background="#2563eb",foreground="white",font=("Segoe UI",10,"bold"))
    style.map("Accent.TButton",background=[("disabled",soft),("active","#1d4ed8")],
              foreground=[("disabled",muted)])
    style.configure("TCheckbutton",indicatorbackground=bg,indicatorforeground=red)
    style.map("TCheckbutton",background=[("active",bg)])
    style.map("TCombobox",fieldbackground=[("readonly",soft)],foreground=[("readonly",fg)])
    style.configure("Treeview",background=bg,fieldbackground=bg,rowheight=root.winfo_pixels("28p"),borderwidth=0)
    style.configure("Treeview.Heading",background=soft,font=("Segoe UI",11,"bold"),padding=(2,6))
    style.layout("Treeview.Heading",[("Treeheading.cell",{"sticky":"nswe"}),("Treeheading.padding",{
        "sticky":"nswe","children":[("Treeheading.text",{"sticky":"we"})]})])
    style.configure("Treeview.Heading",borderwidth=0,relief="flat")
    style.map("Treeview.Heading",background=[("active",line)],foreground=[("active",fg)])
    style.map("Treeview",background=[("selected",selected)],foreground=[("selected",fg)])
    style.configure("TProgressbar",background="#2563eb",troughcolor=soft)
    style.configure("Brand.TLabel",foreground=fg,font=("Segoe UI",15,"bold"))
    style.configure("Side.TButton",width=0,background=bg,foreground=muted,padding=(11,7))
    style.map("Side.TButton",background=[("active",soft)])
    style.configure("Active.Side.TButton",background=selected,foreground=red,font=("Segoe UI",11,"bold"))
    style.map("Active.Side.TButton",background=[("active",selected)])
    style.configure("Stamp.TLabel",foreground=muted,font=("Segoe UI",10))
    style.configure("StampValue.TLabel",foreground=fg,font=("Segoe UI",10,"bold"))
    style.configure("Banner.TLabel",background=soft,foreground=fg,padding=(10,6))
    for name,fg_color,bg_color in (
        ("Pending", "#fdba74" if dark else "#c2410c","#402c1c" if dark else "#fff7ed"),
        ("Success", "#86efac" if dark else "#15803d","#17382b" if dark else "#f0fdf4"),
        ("Failed", "#ffc2c2" if dark else "#842d3a","#442e34" if dark else "#faedef")):
        style.configure(name+".TLabel",foreground=fg_color,background=bg_color)
    for name,color in (("ApiOnline", "#86efac" if dark else "#15803d"),
                       ("ApiOffline", "#fdba74" if dark else "#c2410c"),
                       ("ApiPending", muted)):
        style.configure(name+".TLabel",foreground=color,background=bg,font=("Segoe UI",10))
    style.configure("CrowdStrike.TLabel",foreground="#ff6979" if dark else "#c8172c",font=("Segoe UI",12,"bold"))
    install_button_styles(root,style,bg,fg,soft,muted,line,red,selected,dark)
    root.option_add("*TCombobox*Listbox.background",bg)
    root.option_add("*TCombobox*Listbox.foreground",fg)
    root.option_add("*Menu.background",bg)
    root.option_add("*Menu.foreground",fg)
    root.option_add("*Menu.activeBackground",selected)
    root.option_add("*Menu.activeForeground",fg)
    return dict(bg=bg,fg=fg,soft=soft,muted=muted,line=line,red=red,selected=selected,match=match)


def scrollable(widget, frame):
    bar=ttk.Scrollbar(frame,orient="vertical",command=widget.yview)
    def changed(first,last):
        bar.set(first,last)
        if float(first)<=0 and float(last)>=1:
            bar.pack_forget()
        elif not bar.winfo_manager():
            bar.pack(side="right",fill="y",before=widget)
    widget.configure(yscrollcommand=changed)


def style_rows(tree):
    style=ttk.Style(tree)
    tree.tag_configure("stripe",background=style.lookup("TFrame","background"))
    tree.tag_configure("online", foreground="#86efac" if style.lookup("TLabel", "foreground")=="#e7edf5" else "#15803d")
    tree.tag_configure("offline", foreground="#fdba74" if style.lookup("TLabel", "foreground")=="#e7edf5" else "#c2410c")
    tree.tag_configure("unknown", foreground="#facc15" if style.lookup("TLabel", "foreground")=="#e7edf5" else "#9a6700")
    for tag in ("pending","success","failed"):
        name=tag.capitalize()+".TLabel"
        tree.tag_configure(tag,foreground=style.lookup(name,"foreground"),background=style.lookup(name,"background"))


def table(parent, columns, multiple=False):
    frame = ttk.Frame(parent)
    frame.pack(fill="both", expand=True, pady=5)
    tree = ttk.Treeview(frame, columns=[c[0] for c in columns], show="headings",
                        selectmode="extended" if multiple else "browse")
    for label, width in columns:
        tree.heading(label, text=label)
        tree.column(label, width=width, minwidth=50)
    tree.pack(fill="both", expand=True)
    scrollable(tree,frame)
    style_rows(tree)
    return tree


def format_last_seen(value):
    if not value:
        return "Sin dato"
    try:
        stamp = datetime.fromisoformat(str(value).replace("Z","+00:00"))
        if stamp.tzinfo is None:
            stamp = stamp.replace(tzinfo=timezone.utc)
        return stamp.astimezone().strftime("%d/%m/%Y %H:%M")
    except (ValueError,TypeError,OverflowError,OSError):
        return "Sin dato"


class HostPicker(ttk.Frame):
    """Selección por sensor, conservada al filtrar y cambiar de página."""
    def __init__(self, parent, panel, app_id, on_change, verify):
        super().__init__(parent)
        self.panel, self.app_id, self.on_change = panel, app_id, on_change
        self.marked = set()
        self.states = {}
        self.last_seen = {}
        self.rows = []
        self.page = 0
        self.version = None
        self.outbox = queue.Queue()
        self.loading = False
        self.lookup_enabled = True
        self.notice = tk.StringVar()
        self.search = tk.StringVar()
        bar = ttk.Frame(self)
        bar.pack(fill="x",pady=(0,8))
        bar.columnconfigure(1,weight=1)
        search_label = ttk.Label(bar,text="Buscar equipo")
        search_label.grid(row=0,column=0,sticky="w")
        search_entry = ttk.Entry(bar,textvariable=self.search,width=18)
        search_entry.grid(row=0,column=1,sticky="ew",padx=(8,12))
        actions = ttk.Frame(bar)
        actions.grid(row=0,column=2,sticky="e")
        ttk.Button(actions,text="Actualizar conexión",command=self.lookup_again).pack(side="left",padx=(0,8))
        ttk.Button(actions,text="Verificar instalación",command=verify).pack(side="left")
        def fit_checks(event):
            needed = search_label.winfo_reqwidth()+160+actions.winfo_reqwidth()+28
            if event.width<needed:
                actions.grid_configure(row=1,column=0,columnspan=3,sticky="w",pady=(8,0))
            else:
                actions.grid_configure(row=0,column=2,columnspan=1,sticky="e",pady=0)
        bar.bind("<Configure>",fit_checks)
        footer = ttk.Frame(self)
        footer.pack(side="bottom",fill="x",pady=(6,0))
        footer.columnconfigure(1,weight=1)
        self.summary = ttk.Label(footer,style="StampValue.TLabel")
        self.summary.grid(row=0,column=0,sticky="w",padx=(0,18))
        self.notice_label = ttk.Label(footer,textvariable=self.notice,style="Stamp.TLabel",anchor="e",justify="right")
        self.notice_label.grid(row=0,column=1,sticky="e")
        self.paging=ttk.Frame(footer)
        for title, delta in (("Siguiente",1),("Anterior",-1)):
            ttk.Button(self.paging,text=title,style="Compact.Side.TButton",command=lambda d=delta:self.turn(d)).pack(side="right")
        def fit_summary(event):
            paging_width = self.paging.winfo_reqwidth() if self.paging.winfo_manager() else 0
            available = event.width-self.summary.winfo_reqwidth()-paging_width-24
            if available<120:
                self.notice_label.grid_configure(row=1,column=0,columnspan=3,sticky="w",pady=(3,0))
                self.notice_label.configure(wraplength=max(120,event.width-8))
            else:
                self.notice_label.grid_configure(row=0,column=1,columnspan=1,sticky="e",pady=0)
                self.notice_label.configure(wraplength=available)
        footer.bind("<Configure>",fit_summary)
        self.tree = table(self,[("Marcar",55),("Equipo",250),("Conexión del sensor",160),("Last seen (local)",180),("Última orden",210)])
        self.tree.column("Marcar",width=40,minwidth=36,stretch=False,anchor="center")
        self.tree.heading("Marcar",text="☐",command=self.toggle_all)
        for col,width in (("Equipo",120),("Conexión del sensor",125),("Last seen (local)",175),("Última orden",130)):
            self.tree.column(col,width=width)
        self.tree.bind("<Button-1>",self.click)
        self.tree.bind("<space>",lambda _:self.toggle(self.tree.focus()))
        self.search.trace_add("write",lambda *_: self.turn(-self.page))
        self.refresh_rows()
        self.timer=self.after(400,self.tick)

    def destroy(self):
        self.after_cancel(self.timer)
        super().destroy()

    def refresh_rows(self):
        self.version = self.panel.db.execute("PRAGMA data_version").fetchone()[0]
        partial = not self.panel.demo and not self.panel.db.execute(
            "SELECT 1 FROM meta WHERE key='applications_scope'").fetchone()
        table_name = "loading_inventory" if partial else "inventory"
        self.rows = self.panel.db.execute(f"""SELECT host_key,aid,hostname FROM {table_name}
            WHERE app_id=? AND installed=1 ORDER BY hostname COLLATE NOCASE,host_key""",(self.app_id,)).fetchall()
        used=self.panel.db.execute(f"SELECT count(*) FROM {table_name} WHERE app_id=? AND used=1",(self.app_id,)).fetchone()[0]
        self.panel.install_stats.set(f"{len(self.rows):,} instalados   ·   {used:,} con uso")
        self.orders = dict(self.panel.db.execute("SELECT j.aid,"+JOB_RESULT_SQL+" FROM job j WHERE j.app_id=? ORDER BY j.id",(self.app_id,)))
        self.marked.intersection_update(r["aid"] for r in self.rows if r["aid"])
        self.draw()

    def draw(self):
        query = self.search.get().strip().casefold()
        self.filtered = [r for r in self.rows if query in r["hostname"].casefold()]
        pages = max(1,(len(self.filtered)+79)//80)
        self.page = min(self.page,pages-1)
        self.visible = self.filtered[self.page*80:(self.page+1)*80]
        focused = self.tree.focus()
        self.tree.delete(*self.tree.get_children())
        for n,row in enumerate(self.visible):
            key = row["aid"]
            state = self.states.get(key,("Por consultar",0))[0] if key else "Sin sensor identificado"
            self.tree.insert("","end",iid=row["host_key"], values=(
                ("☑" if key in self.marked else "☐") if key else "—",row["hostname"],
                ("●  " if state in ("En línea","Desconectado","Desconocido") else "")+state,
                format_last_seen(self.last_seen.get(key)),
                self.orders.get(key,"—")),tags=(("online",) if state == "En línea" else ("offline",) if state == "Desconectado" else ("unknown",) if state == "Desconocido" else ()) + (("marked",) if key in self.marked else (("stripe",) if n%2 else ())))
        self.tree.tag_configure("marked",background=self.panel.colors["selected"])
        if focused and self.tree.exists(focused):
            self.tree.focus(focused)
        eligible = {r["aid"] for r in self.filtered if r["aid"]}
        head = "☑" if eligible and eligible <= self.marked else ("−" if eligible & self.marked else "☐")
        self.tree.heading("Marcar",text=head)
        if pages>1:
            self.paging.grid(row=0,column=2,sticky="e",padx=(8,0))
        else:
            self.paging.grid_remove()
        self.summary.configure(text=f"{len(self.filtered):,} equipos · {len(self.marked):,} seleccionados" +
                               (f" · {self.page+1}/{pages}" if pages>1 else ""))
        self.on_change(len(self.marked))
        self.lookup()

    def turn(self,delta):
        self.page=max(0,self.page+delta)
        self.draw()

    def click(self,event):
        key = self.tree.identify_row(event.y)
        if key and self.tree.identify_region(event.x,event.y) in ("tree","cell"):
            self.tree.focus(key)
            self.toggle(key)
            return "break"

    def toggle(self,key):
        aid = next((r["aid"] for r in self.visible if r["host_key"]==key),"")
        if aid:
            self.marked.symmetric_difference_update([aid])
            self.draw()
        return "break"

    def mark_all(self):
        self.marked.update(r["aid"] for r in self.filtered if r["aid"])
        self.draw()

    def toggle_all(self):
        eligible = {r["aid"] for r in self.filtered if r["aid"]}
        if eligible <= self.marked:
            self.marked.difference_update(eligible)
            self.draw()
        else:
            self.mark_all()

    def clear(self):
        self.marked.clear()
        self.draw()

    def lookup_again(self):
        self.lookup_enabled=True
        self.states.clear()
        self.draw()

    def lookup(self):
        keys = [r["aid"] for r in self.visible if r["aid"] and
                time.monotonic()-self.states.get(r["aid"],("",float("-inf")))[1] > 60]
        if self.loading or not self.lookup_enabled or not keys:
            return
        self.loading=True
        self.notice.set("Actualizando conexión…")
        def fetch():
            try:
                states,last_seen,warning = self.panel.service.host_presence(keys)
                self.outbox.put((keys,states,last_seen,None,warning))
            except Exception as err:
                self.outbox.put((keys,{},{},err,""))
        threading.Thread(target=fetch,daemon=True).start()

    def tick(self):
        try:
            keys,states,last_seen,error,warning=self.outbox.get_nowait()
        except queue.Empty:
            pass
        else:
            self.loading=False
            for key in keys:
                self.states[key]=(states.get(key,"Desconocido"),time.monotonic())
            self.last_seen.update(last_seen)
            self.lookup_enabled = error is None
            if error:
                self.notice.set("Para ver la conexión, habilita Hosts → Read." if
                    isinstance(error,FalconError) and error.code==403 else "Conexión sin confirmar. Pulsa Actualizar conexión para reintentar.")
            else:
                self.notice.set(f"Conexión: {time.strftime('%H:%M:%S')}. " + warning)
            self.draw()
        if self.version != self.panel.db.execute("PRAGMA data_version").fetchone()[0]:
            self.refresh_rows()
        else:
            self.lookup()
        self.timer=self.after(3000,self.tick)


class Panel:
    def __init__(self, root, path, service):
        self.root, self.path, self.service = root, path, service
        self.demo = isinstance(service, Demo)
        self.db = db_open(path)
        if not self.demo:
            self.service.script_bindings = {}
            for row in self.db.execute("SELECT value FROM meta WHERE key LIKE 'rtr_binding:%'"):
                try:
                    binding = json.loads(row[0])
                    self.service.script_bindings[binding["name"]] = binding
                except (ValueError,KeyError,TypeError):
                    pass
        self.busy = False
        self.reading = threading.Event()
        self.cancel_read = threading.Event()
        self.exit_after_read = False
        self.last_preview = 0.0
        self.app_groups = {}
        self.messages = queue.Queue()
        self.page = 0
        self.footer = tk.StringVar()
        self.find = tk.StringVar()
        self.scope = tk.StringVar(value="Todos los detectados")
        self.hist_filter = tk.StringVar()
        self.history_app = None
        self.category = tk.StringVar(value="Todas")
        root.title(f"GestorFalcon {__version__} · Falcon App Uninstaller")
        self.dark = read_theme(path.parent)
        self.colors = palette(root,self.dark)
        self.active_id = None
        self.active_group = ()
        self.pending_edits = {}
        self.icons = {}
        self.icon_library = IconLibrary(root,path.parent.parent/"iconos")
        self.install_stats=tk.StringVar()
        self.search_timer = None
        root.geometry(f"{min(1380,root.winfo_screenwidth()-45)}x{min(820,root.winfo_screenheight()-90)}")
        root.minsize(940,560)
        root.protocol("WM_DELETE_WINDOW", self.close)
        header=ttk.Frame(root,padding=(14,6))
        header.pack(fill="x")
        self.brand_image = crowdstrike_image(root,path.parent.parent)
        if self.brand_image is not None:
            self.brand_image = self.brand_image.subsample(2,2)
            ttk.Label(header,image=self.brand_image).pack(side="left",padx=(0,7))
        ttk.Label(header,text="GestorFalcon",style="CompactBrand.TLabel").pack(side="left",padx=(0,18))
        navigation = ttk.Frame(header)
        navigation.pack(side="left")
        self.nav=[]
        self.nav_indices=[]
        for idx,label in ((0,"Aplicaciones"),(1,"Seguimiento"),(3,"Historial"),(2,"Reglas")):
            button=ttk.Button(navigation,text=label,style="Compact.Side.TButton",command=lambda i=idx:self.tabs.select(i))
            button.pack(side="left",padx=(0,2))
            self.nav.append(button)
            self.nav_indices.append(idx)
        self.theme_btn=ttk.Button(header,text="◐",width=2,style="Compact.Side.TButton",command=self.toggle_theme)
        self.theme_btn.pack(side="right",padx=(6,0))
        self.api_results = queue.Queue()
        self.api_loading = False
        self.api_next = 0.0
        self.api_started = 0.0
        self.api_checked = "Sin comprobar"
        self.api_detail = "Esperando la primera comprobación."
        self.api_state = ttk.Label(header,text="● API · Por comprobar",style="ApiPending.TLabel",cursor="hand2",padding=(6,4))
        self.api_state.pack(side="right",padx=6)
        self.api_state.bind("<Button-1>",lambda event:self.connection_info())
        ttk.Separator(root).pack(fill="x")
        outer=ttk.Frame(root)
        outer.pack(fill="both",expand=True)
        status=ttk.Frame(outer,padding=(16,5))
        status.pack(side="bottom",fill="x")
        self.last_sync=tk.StringVar(value="Pendiente")
        ttk.Label(status,textvariable=self.last_sync,style="StampValue.TLabel").pack(side="right")
        ttk.Label(status,text="Última actualización",style="Stamp.TLabel").pack(side="right",padx=(10,6))
        self.activity=ttk.Progressbar(status,mode="indeterminate",length=48)
        self.status_text=ttk.Label(status,textvariable=self.footer,style="Stamp.TLabel")
        self.status_text.pack(side="left")
        ttk.Separator(outer).pack(side="bottom",fill="x")
        self.tabs=ttk.Notebook(outer,style="Shell.TNotebook")
        self.tabs.pack(fill="both",expand=True)
        inv=ttk.Frame(self.tabs)
        report=ttk.Frame(self.tabs,padding=14)
        rules=ttk.Frame(self.tabs,padding=14)
        archive=ttk.Frame(self.tabs,padding=14)
        for page,title in ((inv,"Aplicaciones"),(report,"Seguimiento"),(rules,"Reglas automáticas"),(archive,"Historial")):
            self.tabs.add(page,text=title)
            if page != inv:
                ttk.Label(page,text=title,style="Title.TLabel").pack(anchor="w",pady=(0,12))
        self.tabs.bind("<<NotebookTabChanged>>",self.update_nav)
        self.page_stats=[]
        for page in (rules,report,archive):
            label=ttk.Label(page,style="Muted.TLabel")
            label.pack(anchor="w",pady=(0,6))
            self.page_stats.append(label)
        archive_bar = ttk.Frame(archive)
        archive_bar.pack(fill="x")
        ttk.Label(archive_bar,text="Buscar programa").pack(side="left")
        ttk.Entry(archive_bar,textvariable=self.hist_filter,width=28).pack(side="left",padx=6)
        ttk.Button(archive_bar,text="Todos",command=lambda:self.hist_filter.set("")).pack(side="left")
        ttk.Button(archive_bar,text="Exportar CSV",command=self.export_history).pack(side="left",padx=8)
        self.hist_page = 0
        self.hist_count = ttk.Label(archive_bar)
        self.hist_count.pack(side="right")
        for label,step in (("Siguiente",1),("Anterior",-1)):
            ttk.Button(archive_bar,text=label,command=lambda s=step:self.show_archive(s)).pack(side="right")
        self.archive = table(archive,[("Fecha UTC",140),("Programa",155),("Fabricante",125),("Equipo",140),
                                     ("Fuente",80),("Resultado",235)])
        self.archive.bind("<Double-1>",lambda event:self.history(int(self.archive.focus().split(":")[1])) if self.archive.focus().startswith("RTR:") else None)
        self.hist_filter.trace_add("write", lambda *_:self.search_history())
        ttk.Label(rules,text="Reglas activas · revisión cada 15 minutos mientras el gestor esté abierto").pack(anchor="w")
        self.rules = table(rules,[("Programa",180),("Fabricante",130),("Plataforma",90),("Script RTR",250),("Cola",50)])
        ttk.Button(rules,text="Desactivar regla seleccionada",command=self.disable_selected).pack(anchor="w")
        inv.columnconfigure(2,weight=1)
        inv.rowconfigure(0,weight=1)
        catalog=ttk.Frame(inv,padding=(12,18,12,8),width=max(295,root.winfo_pixels("198p")))
        catalog.grid(row=0,column=0,sticky="ns")
        catalog.grid_propagate(False)
        catalog.columnconfigure(0,weight=1)
        catalog.rowconfigure(4,weight=1)
        ttk.Separator(inv,orient="vertical").grid(row=0,column=1,sticky="ns")
        self.detail=ttk.Frame(inv,padding=(22,18,22,10))
        self.detail.grid(row=0,column=2,sticky="nsew")
        ttk.Label(catalog,text="Aplicaciones",style="Title.TLabel").grid(row=0,column=0,sticky="w",pady=(0,12))
        self.search_box=tk.Frame(catalog,highlightthickness=2,bd=0)
        self.search_box.grid(row=1,column=0,sticky="ew")
        self.search_icon=tk.Label(self.search_box,text="⌕",font=("Segoe UI",16),padx=6)
        self.search_icon.pack(side="left")
        clear=ttk.Button(self.search_box,text="×",width=2,command=self.clear_search)
        clear.pack(side="right",padx=3)
        self.search_entry=tk.Entry(self.search_box,textvariable=self.find,relief="flat",bd=0,width=8,
                                   font=("Segoe UI",12))
        self.search_entry.pack(fill="x",expand=True,pady=9)
        self.search_hint=tk.Label(self.search_box,text="Buscar aplicaciones…",cursor="xterm")
        self.search_hint.bind("<Button-1>",lambda _:self.focus_search())
        self.search_entry.bind("<FocusIn>",lambda _:self.paint_search(True))
        self.search_entry.bind("<FocusOut>",lambda _:self.paint_search(False))
        root.bind("<Control-k>",self.focus_search)
        self.search_entry.bind("<Escape>",lambda _:self.clear_search())
        filterbar=ttk.Frame(catalog)
        filterbar.grid(row=2,column=0,sticky="ew",pady=(6,0))
        filters=ttk.Frame(filterbar)
        def toggle_filters():
            if filters.winfo_manager():
                filters.pack_forget()
            else:
                filters.pack(fill="x",pady=(4,4))
        self.filter_button=ttk.Button(filterbar,text="Filtros",style="Side.TButton",command=toggle_filters)
        self.filter_button.pack(anchor="w")
        self.cats=ttk.Combobox(filters,textvariable=self.category,state="readonly",width=17)
        self.cats.pack(fill="x")
        ttk.Combobox(filters,textvariable=self.scope,values=("Instalados","Todos los detectados"),
                     state="readonly").pack(fill="x",pady=(4,0))
        self.page_label=ttk.Label(catalog,style="Muted.TLabel")
        self.page_label.grid(row=3,column=0,sticky="w",pady=5)
        listframe=ttk.Frame(catalog)
        listframe.grid(row=4,column=0,sticky="nsew")
        self.apps=tk.Text(listframe,wrap="none",cursor="hand2",bd=0,highlightthickness=0,
                          width=12,height=8,padx=3,exportselection=False,takefocus=True)
        self.apps.pack(fill="both",expand=True)
        scrollable(self.apps,listframe)
        self.apps.bind("<Button-1>",self.catalog_click)
        self.apps.bind("<Down>",lambda _:self.move_selection(1))
        self.apps.bind("<Up>",lambda _:self.move_selection(-1))
        self.search_entry.bind("<Down>",lambda _:self.move_selection(1))
        inventory_actions=ttk.Frame(catalog)
        inventory_actions.grid(row=5,column=0,sticky="ew",pady=(10,0))
        ttk.Button(inventory_actions,text="Actualizar inventario",command=self.sync).pack(fill="x")
        ttk.Button(inventory_actions,text="Revisión completa",style="Compact.Side.TButton",command=lambda:self.sync(full=True)).pack(fill="x",pady=(3,0))
        foot=ttk.Frame(catalog)
        foot.grid(row=6,column=0,sticky="ew",pady=(6,0))
        for title,step in (("‹",-1),("›",1)):
            ttk.Button(foot,text=title,width=2,command=lambda d=step:self.turn(d)).pack(side="left",padx=1)
        self.paint_search(False)
        controls = ttk.Frame(report)
        controls.pack(fill="x")
        ttk.Button(controls, text="Consultar estados", command=self.check).pack(side="left")
        ttk.Button(controls, text="Ver historial del equipo", command=self.history).pack(side="left", padx=4)
        ttk.Button(controls, text="Retomar envíos preparados", command=self.resume).pack(side="left")
        self.jobs = table(report, [("Campaña",82),("Programa",145),("Equipo",135),("Estado",180),
                                   ("Último cambio (UTC)",145)])
        self.jobs.bind("<Double-1>", lambda e:self.history())
        for job in self.db.execute("SELECT id FROM job WHERE status='Enviando'").fetchall():
            set_state(self.db, job[0], "Revisar en Falcon", "Cierre durante el envío. Consultar sesión antes de repetir.")
        if self.demo and not self.db.execute("SELECT 1 FROM meta WHERE key='sync'").fetchone():
            replace_inventory(self.db, service.pages(), lambda msg:None)
            source = "# Ejemplo de demostración local. Sustituir por el desinstalador del producto."
            with self.db:
                for app in self.db.execute("SELECT * FROM app WHERE name IN ('Minecraft','Roblox Studio','Steam')").fetchall():
                    self.db.execute("UPDATE app SET draft=?,script=? WHERE id=?",
                                    (source, cloud_name(app, source), app["id"]))
        self.find.trace_add("write", self.search_changed)
        self.scope.trace_add("write",lambda *_:self.filter_changed())
        self.category.trace_add("write", lambda *_:self.filter_changed())
        self.refresh()
        root.after(150, self.read_messages)
        root.after(30000, self.auto_check)
        root.after(5000, self.scheduled_sync)
        root.after(200, self.api_tick)

    def close(self):
        if self.busy and self.reading.is_set():
            self.exit_after_read = True
            self.cancel_read.set()
            self.footer.set("Cerrando al terminar la solicitud actual…")
            return
        if self.busy:
            messagebox.showinfo("Operación en curso", "Espera a que termine la operación antes de cerrar.")
            return
        self.db.close()
        self.root.destroy()

    def start(self, action):
        if self.busy:
            messagebox.showinfo("Operación en curso", "Hay una operación en curso.")
            return
        self.busy = True
        self.activity.pack(side="left",before=self.status_text,padx=(0,8))
        self.activity.start(18)
        self.footer.set("Procesando…")
        def worker():
            db = None
            try:
                db = db_open(self.path)
                action(db, lambda msg:self.messages.put(("progress", msg)))
                self.messages.put(("done", "Operación terminada"))
            except InterruptedError:
                self.messages.put(("paused", "Lectura interrumpida"))
            except Exception as err:
                self.messages.put(("error", str(err)))
            finally:
                if db is not None:
                    db.close()
        threading.Thread(target=worker, daemon=True).start()

    def read_messages(self):
        while not self.messages.empty():
            kind, msg = self.messages.get()
            self.footer.set(msg)
            if msg.startswith("Catálogo parcial") and time.monotonic()-self.last_preview > 3:
                self.last_preview = time.monotonic()
                self.show_apps()
            if kind != "progress":
                self.busy = False
                self.reading.clear()
                if self.exit_after_read:
                    self.close()
                    return
                self.activity.stop()
                self.activity.pack_forget()
                self.refresh()
                if kind == "error":
                    messagebox.showerror("Operación interrumpida", msg)
        self.root.after(200, self.read_messages)

    def sync(self, full=False):
        if self.busy:
            return
        self.cancel_read.clear()
        self.reading.set()
        def synchronize(db,progress):
            def report(message):
                if self.cancel_read.is_set():
                    raise InterruptedError()
                progress(message)
            try:
                update_inventory(db,self.service,report,full)
            finally:
                self.reading.clear()
            if not self.cancel_read.is_set():
                dispatch(db,self.service,automatic_jobs(db),progress)
        self.start(synchronize)

    def scheduled_sync(self):
        if self.busy:
            self.root.after(10000,self.scheduled_sync)
            return
        self.sync()
        self.root.after(15*60*1000,self.scheduled_sync)

    def disable_selected(self):
        if self.busy or not self.rules.selection():
            return
        key = self.rules.selection()[0]
        if messagebox.askyesno("Desactivar regla","¿Detener futuros envíos automáticos para este programa? "
                               "Las órdenes ya recibidas por Falcon se consultan en Seguimiento."):
            disable_policy(self.db,key)
            self.refresh()

    def check(self):
        self.start(lambda db,progress:poll(db,self.service,progress))

    def auto_check(self):
        if not self.busy and not self.root.grab_current() and self.db.execute("SELECT 1 FROM job WHERE status IN ('En cola','Enviado','En curso') LIMIT 1").fetchone():
            self.check()
        self.root.after(30000, self.auto_check)

    def resume(self):
        ids = [r[0] for r in self.db.execute("SELECT id FROM job WHERE status='Preparado' AND campaign NOT LIKE 'Auto-%' ORDER BY id")]
        if not ids:
            messagebox.showinfo("Envíos", "No hay envíos manuales preparados. Los automáticos se retoman al sincronizar.")
        elif messagebox.askyesno("Retomar", f"¿Tramitar los {len(ids)} envíos previamente confirmados?"):
            self.start(lambda db,progress:dispatch(db,self.service,ids,progress))

    def search_history(self):
        self.history_app = None
        self.tabs.tab(3,text="Historial de desinstalaciones")
        self.show_archive(reset=True)

    def history_query(self):
        # El historial utiliza las fichas persistentes incluso sin equipos instalados.
        term = self.hist_filter.get().strip()
        query = """ FROM (
            SELECT j.id, j.updated stamp, j.app_id, j.hostname, 'RTR' source, """+JOB_RESULT_SQL+""" result, j.status execution_result
            FROM job j
            UNION ALL
            SELECT r.id,r.stamp,r.app_id,r.hostname,'Inventario','Ya no figura instalado',''
            FROM removal r
        ) h JOIN app a ON a.id=h.app_id WHERE instr(lower(a.name),lower(?))>0"""
        args = (term,)
        if self.history_app is not None:
            query += " AND a.id=?"
            args += (self.history_app,)
        return query, args

    def show_archive(self, step=0, reset=False):
        query, args = self.history_query()
        total = self.db.execute("SELECT count(*)"+query,args).fetchone()[0]
        pages = max(1,(total+99)//100)
        self.hist_page = 0 if reset else min(max(0,self.hist_page+step),pages-1)
        self.archive.delete(*self.archive.get_children())
        rows = self.db.execute("SELECT h.*,a.name,a.vendor"+query+
            " ORDER BY stamp DESC,source,id DESC LIMIT 100 OFFSET ?",(*args,self.hist_page*100))
        for idx,r in enumerate(rows):
            tag = self.status_tag(r["result"]) if r["source"]=="RTR" else "success"
            self.archive.insert("","end",iid=r["source"]+":"+str(r["id"]),values=(r["stamp"][:19].replace("T"," "),r["name"],r["vendor"],
                                r["hostname"],r["source"],r["result"]),tags=(tag or ("stripe" if idx%2 else ""),))
        self.hist_count.configure(text=f"   {self.hist_page+1} / {pages} · {total} registros")

    def export_history(self):
        query, args = self.history_query()
        if not self.db.execute("SELECT count(*)"+query,args).fetchone()[0]:
            messagebox.showinfo("Exportar CSV","No hay registros para exportar con este filtro.",parent=self.root)
            return
        filename = filedialog.asksaveasfilename(parent=self.root,title="Exportar historial",
            defaultextension=".csv",filetypes=[("Archivo CSV","*.csv")],
            initialfile="historial_"+datetime.now().strftime("%Y%m%d_%H%M%S")+".csv")
        if not filename:
            return
        try:
            rows = self.db.execute("SELECT h.*,a.name,a.vendor"+query+
                " ORDER BY stamp DESC,source,id DESC",args)
            count = 0
            with open(filename,"w",encoding="utf-8-sig",newline="") as output:
                writer = csv.writer(output,delimiter=";")
                writer.writerow(["Fecha UTC","Programa","Fabricante","Equipo","Fuente","Resultado","Estado original RTR"])
                for row in rows:
                    values = [row["stamp"],row["name"],row["vendor"],row["hostname"],row["source"],row["result"],row["execution_result"]]
                    # Evitar que Excel interprete nombres como fórmulas.
                    writer.writerow(["'"+str(v) if str(v or "").lstrip().startswith(("=","+","-","@")) else v for v in values])
                    count += 1
        except (OSError,sqlite3.Error,csv.Error) as error:
            messagebox.showerror("Exportar CSV",f"No se pudo exportar el historial: {error}",parent=self.root)
            return
        messagebox.showinfo("Exportar CSV",f"Se exportaron {count} registros.",parent=self.root)

    @staticmethod
    def status_tag(state):
        if state in ("Error","Finalizado con errores","Revisar en Falcon"):
            return "failed"
        if state in {"Ausencia confirmada por script","Ya no figura instalado"}:
            return "success"
        return "pending" if state in ("En cola","Preparado","Enviando","En curso","Enviado") else ""

    def refresh(self):
        self.icon_library.register_apps(self.db.execute("SELECT DISTINCT name,vendor,category,platform FROM app"))
        counts=self.db.execute("""SELECT (SELECT count(*) FROM policy),
            (SELECT count(DISTINCT aid) FROM job WHERE status='En cola'),(SELECT count(*) FROM removal)""").fetchone()
        for label,count,caption in zip(self.page_stats,counts,("reglas activas","equipos con órdenes en cola","salidas de inventario")):
            label.configure(text=f"{count:,} {caption}")
        values = set(RULES) | {"Sin clasificar"}
        values.update(r[0] for r in self.db.execute("SELECT DISTINCT category FROM app"))
        values.discard("Extensiones de navegador")
        self.cats["values"] = ["Todas", "Juegos y plataformas", *sorted(values - {"Juegos y plataformas"})]
        self.rules.delete(*self.rules.get_children())
        for r in self.db.execute("SELECT a.*,p.offline FROM policy p JOIN app a ON a.id=p.app_id ORDER BY a.name"):
            self.rules.insert("","end",iid=r["id"],values=(r["name"],r["vendor"],r["platform"],r["script"],
                                                          "Sí" if r["offline"] else "No"))
        self.show_apps()
        self.show_archive()
        self.jobs.delete(*self.jobs.get_children())
        for j in self.db.execute("""SELECT j.*,a.name FROM job j JOIN app a ON a.id=j.app_id ORDER BY j.id DESC"""):
            result = job_result(self.db,j["id"])
            self.jobs.insert("", "end", iid=str(j["id"]), values=(j["campaign"],j["name"],j["hostname"],result,
                                                                  j["updated"][:19].replace("T"," ")),tags=(self.status_tag(result),))
        stamp = self.db.execute("SELECT value FROM meta WHERE key='sync'").fetchone()
        valid = stamp and (self.demo or self.db.execute("SELECT 1 FROM meta WHERE key='applications_scope'").fetchone())
        self.last_sync.set(datetime.fromisoformat(stamp[0]).astimezone().strftime("%d/%m/%Y · %H:%M") if valid else "Pendiente")
        if not self.busy:
            self.footer.set("Inventario actualizado" if valid else "Esperando la primera lectura completa")

    def filter_changed(self):
        filters=[val for val,default in ((self.category.get(),"Todas"),(self.scope.get(),"Todos los detectados")) if val!=default]
        self.filter_button.configure(text=f"Filtros ({len(filters)}) ▾" if filters else "Filtros ▾")
        self.page = 0
        self.show_apps()

    def turn(self, delta):
        self.page = max(0, self.page + delta)
        self.show_apps()

    def show_apps(self):
        preview = not self.demo and not self.db.execute("SELECT 1 FROM meta WHERE key='applications_scope'").fetchone()
        source = "loading_inventory" if preview else "inventory"
        category, term = self.category.get(), self.find.get()
        if category=="Juegos y plataformas":
            category_sql = "a.category IN ('Juegos','Plataformas de juegos')"
            args = (term,term)
        else:
            category_sql = "(?='Todas' OR a.category=?)"
            args = (category,category,term,term)
        where = f"""WHERE EXISTS(SELECT 1 FROM {source} i WHERE i.app_id=a.id)
            AND {category_sql} AND (instr(lower(a.name),lower(?)) OR instr(lower(a.vendor),lower(?)))"""
        if self.scope.get()=="Instalados":
            where += f" AND EXISTS(SELECT 1 FROM {source} i WHERE i.app_id=a.id AND i.installed=1)"
        grouped = " FROM app a " + where + " GROUP BY a.name COLLATE NOCASE"
        total = self.db.execute("SELECT count(*) FROM (SELECT 1"+grouped+")",args).fetchone()[0]
        pages = max(1,(total+99)//100)
        self.page = min(self.page,pages-1)
        groups = self.db.execute("""SELECT min(a.id) id,min(a.name) name,group_concat(a.id) ids,
            group_concat(DISTINCT a.vendor) vendor, group_concat(DISTINCT a.platform) platform,
            group_concat(DISTINCT a.category) category""" + grouped +
            " ORDER BY a.name COLLATE NOCASE LIMIT 100 OFFSET ?",(*args,self.page*100))
        self.catalog_rows = list(groups)
        self.app_groups = {r["id"]:tuple(int(key) for key in r["ids"].split(",")) for r in self.catalog_rows}
        self.page_label.configure(text=f"{total:,} resultados · {self.page+1}/{pages}" + (" · parcial" if preview else ""))
        available = next((r["id"] for r in self.catalog_rows if self.active_id in self.app_groups[r["id"]]),None)
        self.select_group(available if available is not None else next(iter(self.app_groups),None))

    def paint_catalog(self):
        text = self.apps
        c = self.colors
        top = text.yview()[0]
        text.configure(state="normal",bg=c["bg"],fg=c["fg"])
        text.delete("1.0","end")
        text.tag_configure("name",font=("Segoe UI",12,"bold"),spacing1=8,lmargin1=7)
        text.tag_configure("vendor",font=("Segoe UI",10),foreground=c["muted"],lmargin1=36,spacing3=8)
        text.tag_configure("active",background=c["selected"])
        text.tag_configure("hit",underline=True)
        text.tag_raise("hit")
        term = self.find.get().strip().lower()
        for r in self.catalog_rows:
            active = ("active",) if r["id"]==self.group_key else ()
            for value,tag in ((r["name"],"name"),(r["vendor"] or "Fabricante desconocido","vendor")):
                value = " ".join(value.splitlines())
                if tag=="name":
                    text.image_create("end",image=self.icon(r["name"],20),padx=4)
                start=text.index("end-1c")
                text.insert("end",value+"\n",(tag,*active))
                pos=value.lower().find(term) if term else -1
                if pos>=0:
                    text.tag_add("hit",f"{start}+{pos}c",f"{start}+{pos+len(term)}c")
        text.configure(state="disabled")
        text.yview_moveto(top)

    def icon(self,name,size):
        return self.icon_library.get(name,size)

    def select_group(self,key,profile=None):
        ids=self.app_groups.get(key,())
        self.group_key=key
        aid = profile if profile in ids else (self.active_id if self.active_id in ids else next(iter(ids),None))
        self.paint_catalog()
        if self.active_group==ids and self.active_id==aid and self.detail.winfo_children():
            return
        if self.active_id is not None and hasattr(self,"remember_edits"):
            self.remember_edits()
        for widget in self.detail.winfo_children():
            widget.destroy()
        self.active_id,self.active_group=aid,ids
        if aid is None:
            ttk.Label(self.detail,text="Sin aplicaciones para esta búsqueda",style="Section.TLabel").pack(anchor="w")
            return
        self.open_profile(aid)

    def catalog_click(self,event):
        line=int(self.apps.index(f"@{event.x},{event.y}").split(".")[0])
        index=(line-1)//2
        if index<len(self.catalog_rows):
            self.apps.focus_set()
            self.select_group(self.catalog_rows[index]["id"])
        return "break"

    def move_selection(self,step):
        keys=list(self.app_groups)
        if keys:
            index=keys.index(self.group_key) if self.group_key in keys else -1
            index=max(0,min(len(keys)-1,index+step))
            self.select_group(keys[index])
            self.apps.see(f"{2*index+1}.0")
        return "break"

    def paint_search(self,focused):
        c=self.colors
        self.search_box.configure(bg=c["bg"],highlightbackground=c["red"] if focused else c["line"])
        self.search_icon.configure(bg=c["bg"],fg=c["red"])
        self.search_entry.configure(bg=c["bg"],fg=c["fg"],insertbackground=c["red"],
                                    selectbackground=c["selected"],selectforeground=c["fg"])
        self.search_hint.configure(bg=c["bg"],fg=c["muted"])
        if focused or self.find.get():
            self.search_hint.place_forget()
        else:
            self.search_hint.place(in_=self.search_entry,x=0,rely=.5,anchor="w")

    def focus_search(self,event=None):
        self.tabs.select(0)
        self.search_entry.focus_set()
        self.search_entry.selection_range(0,"end")
        return "break"

    def clear_search(self):
        self.find.set("")
        return self.focus_search()

    def search_changed(self,*_):
        self.paint_search(self.root.focus_get()==self.search_entry)
        if self.search_timer:
            self.root.after_cancel(self.search_timer)
        self.search_timer=self.root.after(180,self.run_search)

    def run_search(self):
        self.search_timer=None
        self.filter_changed()

    def update_nav(self,event=None):
        current=self.tabs.index("current")
        for idx,button in zip(self.nav_indices,self.nav):
            button.configure(style="Active.Compact.Side.TButton" if idx==current else "Compact.Side.TButton")

    def api_tick(self):
        if self.demo:
            self.api_state.configure(text="● API · Sin conectar",style="ApiPending.TLabel")
            self.api_detail = "Perfil local con datos de ejemplo. No hay una API conectada."
            return
        try:
            ok, detail = self.api_results.get_nowait()
        except queue.Empty:
            pass
        else:
            self.api_loading = False
            self.api_checked = time.strftime("%H:%M:%S")
            self.api_detail = detail
            self.api_state.configure(text="● API · " + ("Conectada" if ok else "Sin conexión"),
                                     style="ApiOnline.TLabel" if ok else "ApiOffline.TLabel")
            self.api_next = time.monotonic()+30
        current = time.monotonic()
        if self.api_loading and current-self.api_started > 50:
            self.api_state.configure(text="● API · Sin respuesta",style="ApiOffline.TLabel")
            self.api_detail = "La comprobación lleva más de 50 segundos sin responder."
        if not self.api_loading and current >= self.api_next:
            self.api_loading = True
            self.api_started = current
            # Retirar el verde mientras se confirma de nuevo el acceso.
            self.api_state.configure(text="● API · Comprobando",style="ApiPending.TLabel")
            def probe():
                try:
                    body(self.service.discover.query_combined_applications(limit=1))
                    result = (True,"Falcon responde y permite consultar el inventario.")
                except FalconError as err:
                    detail = {401:"Credenciales rechazadas o sesión caducada.",
                              403:"Acceso al inventario denegado; revisa los permisos."}.get(err.code,
                              f"Falcon respondió con un error HTTP {err.code}.")
                    result = (False,detail)
                except Exception:
                    result = (False,"No se pudo contactar con Falcon. Revisa la conexión y vuelve a comprobar.")
                self.api_results.put(result)
            threading.Thread(target=probe,daemon=True).start()
        self.root.after(500,self.api_tick)

    def connection_info(self):
        if not self.demo:
            self.api_next = 0.0
        text = self.api_detail + "\n\nÚltima comprobación: " + self.api_checked
        text += "\nSe comprueba el acceso al inventario cada 30 segundos."
        if self.demo:
            text = self.api_detail
        messagebox.showinfo("Estado API",text+"\n\nPara cambiar la cuenta o la región, cierra el gestor y abre Iniciar.cmd.",parent=self.root)

    def toggle_theme(self):
        self.dark=not self.dark
        self.colors=palette(self.root,self.dark)
        try:
            (self.path.parent/"tema.txt").write_text("oscuro" if self.dark else "claro",encoding="utf8")
        except OSError:
            self.footer.set("Tema aplicado para esta sesión.")
        self.theme_btn.configure(text="◑" if self.dark else "◐")
        self.paint_search(self.search_entry==self.root.focus_get())
        self.paint_catalog()
        self.tint_widgets(self.root)
        self.update_nav()

    def tint_widgets(self,parent):
        c=self.colors
        for widget in parent.winfo_children():
            if isinstance(widget,tk.Text):
                widget.configure(bg=c["soft"] if widget.winfo_name()=="editor" else c["bg"],
                                 fg=c["fg"],insertbackground=c["fg"])
            if isinstance(widget,tk.Menu):
                widget.configure(bg=c["bg"],fg=c["fg"],activebackground=c["selected"],activeforeground=c["fg"])
            if isinstance(widget,ttk.Treeview):
                style_rows(widget)
                widget.tag_configure("marked",background=c["selected"])
            self.tint_widgets(widget)

    def history(self, jid=None):
        if jid is None:
            if not self.jobs.selection():
                return
            jid = self.jobs.selection()[0]
        j = self.db.execute("SELECT * FROM job WHERE id=?", (jid,)).fetchone()
        window = tk.Toplevel(self.root)
        window.title("Historial · " + j["hostname"])
        log = tk.Text(window, wrap="word", padx=12, pady=12)
        log.pack(fill="both",expand=True)
        log.insert("end",f"Equipo  {j['hostname']}\nAID  {j['aid']}\nScript  {j['script']}\nSesión  {j['session']}\nSolicitud  {j['request']}\n\n")
        result = job_result(self.db,jid)
        log.insert("end",f"Resultado actual: {result}\nEstado original de ejecución RTR: {j['status']}\n\n")
        if result=="Ya no figura instalado":
            stamp = self.db.execute("SELECT max(stamp) FROM removal WHERE app_id=? AND host_key=?",(j["app_id"],j["aid"])).fetchone()[0]
            log.insert("end",f"El inventario confirmó la ausencia posteriormente: {stamp}\nEl registro original de ejecución se conserva debajo.\n\n")
        for row in self.db.execute("SELECT * FROM event WHERE job_id=? ORDER BY id",(jid,)):
            log.insert("end",f"{row['stamp']}   {row['status']}\n{row['detail']}\n\n")
        log.configure(state="disabled")
        if j["status"] in {"Revisar en Falcon","En cola","En curso","Enviado"}:
            def reconcile():
                if self.busy:
                    messagebox.showinfo("Seguimiento","Espera a que termine la operación en curso.",parent=window)
                    return
                if messagebox.askyesno("Cierre manual",
                        "¿Verificaste en Falcon que la orden ya terminó, caducó o fue cancelada? "
                        "Cerrar el registro permite preparar otro envío. La orden remota se gestiona en Falcon.",
                        parent=window):
                    current = self.db.execute("SELECT status FROM job WHERE id=?", (jid,)).fetchone()[0]
                    if current in {"Revisar en Falcon","En cola","En curso","Enviado"}:
                        set_state(self.db,jid,"Cerrado por operador","Orden revisada en Falcon y cerrada manualmente.")
                    window.destroy()
                    self.refresh()
            ttk.Button(window,text="Cerrar registro tras verificar en Falcon",command=reconcile).pack(pady=5)

    def open_profile(self, aid):
        app=self.db.execute("SELECT * FROM app WHERE id=?",(aid,)).fetchone()
        outer=self.detail
        window=self.root
        title=ttk.Frame(outer)
        title.pack(fill="x")
        name=ttk.Label(title,text="  "+app["name"],image=self.icon(app["name"],42),
                       compound="left",style="Title.TLabel",wraplength=550)
        name.pack(anchor="w")
        title.bind("<Configure>",lambda e:name.configure(wraplength=max(200,e.width-8)))
        if len(self.active_group)>1:
            profiles=[self.db.execute("SELECT vendor,platform FROM app WHERE id=?",(key,)).fetchone() for key in self.active_group]
            choices=ttk.Combobox(title,state="readonly",values=[" · ".join(r) for r in profiles])
            choices.current(self.active_group.index(aid))
            choices.pack(anchor="w")
            choices.bind("<<ComboboxSelected>>",lambda _:self.select_group(self.group_key,self.active_group[choices.current()]))
        else:
            ttk.Label(title,text=f"{app['vendor'] or 'Fabricante desconocido'} · {app['platform']}",style="Muted.TLabel").pack(anchor="w")
        def edit_category():
            if self.busy:
                messagebox.showinfo("Categoría","Espera a que termine la operación actual.",parent=window)
                return
            dialog=tk.Toplevel(window)
            dialog.title("Cambiar categoría")
            dialog.transient(window)
            box=ttk.Frame(dialog,padding=16)
            box.pack()
            ttk.Label(box,text=app["name"],style="Section.TLabel").pack(anchor="w")
            field=ttk.Combobox(box,values=list(self.cats["values"])[2:],width=30)
            field.set(category.get())
            field.pack(pady=8)
            def apply_category():
                value=field.get().strip()
                if not value or value.casefold() in {"todas","juegos y plataformas"}:
                    return
                with self.db:
                    self.db.execute("UPDATE app SET category=? WHERE id=?",(value,aid))
                    self.db.execute("INSERT OR IGNORE INTO manual_category VALUES(?)",(aid,))
                category.set(value)
                chip.configure(text=value+"  ✎")
                dialog.destroy()
                self.refresh()
            ttk.Button(box,text="Guardar categoría",command=apply_category).pack(anchor="e")
            dialog.grab_set()
            field.focus_set()
        category=tk.StringVar(value=app["category"])
        meta=ttk.Frame(title)
        meta.pack(anchor="w",pady=(6,0))
        chip=ttk.Button(meta,text=app["category"]+"  ✎",style="Chip.TButton",command=edit_category)
        chip.pack(side="left")
        ttk.Label(meta,textvariable=self.install_stats,style="Muted.TLabel").pack(side="left",padx=10)
        def verify_now():
            if not self.busy:
                self.start(lambda db,progress:verify_product(db,self.service,app["id"],progress))

        partial = not self.demo and not self.db.execute("SELECT 1 FROM meta WHERE key='applications_scope'").fetchone()
        banner = ttk.Label(outer,text="Inventario parcial · Los envíos se habilitan al terminar la carga.",style="Banner.TLabel")
        if partial:
            banner.pack(fill="x",pady=(6,0))
        tabs = ttk.Notebook(outer)
        tabs.pack(fill="both",expand=True,pady=(10,0))
        devices = ttk.Frame(tabs,padding=10)
        frame = ttk.Frame(tabs,padding=12)
        tabs.add(devices,text="Equipos")
        tabs.add(frame,text="Desinstalador")
        timeline=ttk.Frame(tabs,padding=8)
        tabs.add(timeline,text="Historial")
        recent=table(timeline,[("Fecha UTC",125),("Equipo",110),("Resultado",180)])
        def load_recent():
            recent.delete(*recent.get_children())
            rows=self.db.execute("""SELECT j.updated AS stamp,j.hostname,"""+JOB_RESULT_SQL+""" FROM job j WHERE j.app_id=?
                UNION ALL SELECT stamp,hostname,'Ya no figura instalado' FROM removal WHERE app_id=?
                ORDER BY stamp DESC LIMIT 100""",(aid,aid))
            for stamp,host,result in rows:
                recent.insert("","end",values=(stamp[:19].replace("T"," "),host,result),tags=(self.status_tag(result),))
        def product_history():
            self.hist_filter.set(app["name"])
            self.history_app=aid
            self.show_archive(reset=True)
            self.tabs.select(3)
        ttk.Button(timeline,text="Ver historial completo",command=product_history).pack(anchor="w")
        tabs.bind("<<NotebookTabChanged>>",lambda _:load_recent() if tabs.select()==str(timeline) else None)
        editor_bar=ttk.Frame(frame)
        frame.columnconfigure(0,weight=1)
        frame.rowconfigure(2,weight=1)
        editor_bar.grid(row=0,column=0,sticky="ew")
        language="PowerShell" if app["platform"].casefold()=="windows" else "shell"
        ttk.Label(editor_bar,text=f"Comando o script de {language}",style="Section.TLabel").pack(side="left")
        ttk.Button(editor_bar,text="Abrir archivo…",command=lambda:import_file()).pack(side="right")
        script_hint = ttk.Label(frame,text="Pega el script aquí o abre un archivo.",style="Muted.TLabel")
        script_hint.grid(row=1,column=0,sticky="w",pady=(3,6))
        draft = tk.Text(frame,name="editor",height=3,width=20,wrap="word",padx=12,pady=8,
                        relief="flat",font=("Consolas",11),undo=True)
        draft.insert("1.0",self.pending_edits.get(aid,app["draft"]))
        draft.configure(bg=self.colors["soft"],fg=self.colors["fg"],insertbackground=self.colors["fg"])
        def remember():
            edits=draft.get("1.0","end-1c")
            if edits!=app["draft"]:
                self.pending_edits[aid]=edits
            else:
                self.pending_edits.pop(aid,None)
        self.remember_edits=remember
        draft.grid(row=2,column=0,sticky="nsew")
        published = tk.StringVar(value=app["script"] or "Sin script vinculado")
        published.trace_add("write",lambda *_:script_hint.configure(text="Script vinculado: "+published.get()))
        if app["script"]: script_hint.configure(text="Script vinculado: "+app["script"])
        linked = dict(getattr(self.service,"script_bindings",{}).get(app["script"],{}))
        def save():
            if self.busy:
                messagebox.showinfo("Operación en curso","Espera a que termine la operación actual.",parent=window)
                return False
            source = draft.get("1.0","end-1c")
            try:
                name = save_uninstaller(self.db, self.service, app, source, linked)
            except ValueError as err:
                messagebox.showinfo("Guardar desinstalador", str(err), parent=window)
                return False
            published.set(name or "Sin script vinculado")
            choose_script.configure(text="Editar desinstalador" if name else "Elegir desinstalador")
            self.refresh()
            return True
        def select_cloud_script():
            if self.demo:
                messagebox.showinfo("Scripts de Falcon", "Conecta un perfil Falcon para ver los custom scripts.", parent=window)
                return
            if self.busy:
                messagebox.showinfo("Operación en curso", "Espera a que termine la consulta actual.", parent=window)
                return
            dialog = tk.Toplevel(window)
            dialog.title("Elegir script de Falcon")
            dialog.geometry("900x540")
            dialog.minsize(680, 400)
            dialog.transient(window)
            shell = ttk.Frame(dialog, padding=16)
            shell.pack(fill="both", expand=True)
            shell.columnconfigure(0, weight=1)
            shell.rowconfigure(3, weight=1)
            ttk.Label(shell, text="Custom scripts de Falcon", style="Section.TLabel").grid(row=0, column=0, sticky="w")
            subtitle = ttk.Label(shell, text="Vincula un script existente a esta aplicación. Puedes reutilizarlo en otras versiones.",
                                 wraplength=820, style="Muted.TLabel")
            subtitle.grid(row=1, column=0, sticky="ew", pady=(6, 0))
            search = ttk.Frame(shell)
            search.grid(row=2, column=0, sticky="ew", pady=10)
            ttk.Label(search, text="Buscar script").pack(side="left", padx=(0, 8))
            query = tk.StringVar()
            field = ttk.Entry(search, textvariable=query)
            field.pack(side="left", fill="x", expand=True)
            # Only this row expands: actions retain their space at every window size.
            listing = ttk.Frame(shell)
            listing.grid(row=3, column=0, sticky="nsew")
            tree = table(listing, [("Nombre", 370), ("Plataforma", 100), ("Actualizado", 170)])
            tree.configure(height=5)
            notice = tk.StringVar(value="Consultando biblioteca…")
            notice_label = ttk.Label(shell, textvariable=notice, wraplength=820, style="Muted.TLabel")
            notice_label.grid(row=4, column=0, sticky="ew", pady=6)
            def fit_text(event):
                width = max(200, event.width - 32)
                subtitle.configure(wraplength=width)
                notice_label.configure(wraplength=width)
            shell.bind("<Configure>", fit_text)
            replies = queue.Queue()
            records = []
            loading = [False]
            def render(*_):
                tree.delete(*tree.get_children())
                for index, record in enumerate(records):
                    if query.get().casefold() not in str(record.get("name", "")).casefold():
                        continue
                    platforms = record.get("platform", "")
                    if isinstance(platforms, list): platforms = ", ".join(map(str, platforms))
                    stamp = record.get("modified_timestamp") or record.get("modified_at") or "—"
                    tree.insert("", "end", iid=str(index), values=(record.get("name", ""), platforms, stamp))
                use_button.state(["disabled"])
                if not loading[0]:
                    notice.set(f"{len(tree.get_children())} de {len(records)} scripts. Vincular no ejecuta ni publica el script.")
            query.trace_add("write", render)
            def selected(_=None):
                use_button.state(["!disabled"] if tree.selection() and not loading[0] else ["disabled"])
            tree.bind("<<TreeviewSelect>>", selected)
            def fetch():
                if loading[0]: return
                loading[0] = True
                refresh_button.state(["disabled"])
                use_button.state(["disabled"])
                notice.set("Consultando biblioteca…")
                def work():
                    try: replies.put((self.service.library_scripts(), None))
                    except Exception as err: replies.put((None, str(err)))
                threading.Thread(target=work, daemon=True).start()
                dialog.after(150, received)
            def received():
                if not dialog.winfo_exists(): return
                try: result, error = replies.get_nowait()
                except queue.Empty:
                    dialog.after(150, received)
                    return
                loading[0] = False
                refresh_button.state(["!disabled"])
                if error:
                    records.clear()
                    render()
                    notice.set("No se pudo consultar la biblioteca: " + error)
                    return
                records[:] = sorted(result, key=lambda r: str(r.get("name", "")).casefold())
                render()
            def use():
                if loading[0] or not tree.selection(): return
                record = records[int(tree.selection()[0])]
                try:
                    content, binding = rtr_script_binding(record, app["platform"])
                    if sum(r.get("name") == binding["name"] for r in records) != 1:
                        raise ValueError("Hay varios scripts con el mismo nombre. Usa un nombre único en Falcon.")
                except ValueError as err:
                    messagebox.showerror("Vincular script", str(err), parent=dialog)
                    return
                if not messagebox.askyesno("Vincular script", f"Aplicación: {app['name']}\nScript: {binding['name']}\n\n"
                        "Se reemplazará el contenido del editor de esta ficha. El script no se ejecutará.", parent=dialog):
                    return
                previous = dict(linked)
                previous_source = draft.get("1.0", "end-1c")
                linked.clear()
                linked.update(binding)
                draft.delete("1.0", "end")
                draft.insert("1.0", content)
                if not save():
                    linked.clear()
                    linked.update(previous)
                    draft.delete("1.0", "end")
                    draft.insert("1.0", previous_source)
                    return
                self.pending_edits.pop(aid, None)
                self.footer.set("Script vinculado: " + binding["name"])
                dialog.destroy()
            buttons = ttk.Frame(shell)
            buttons.grid(row=5, column=0, sticky="ew", pady=(8, 0))
            refresh_button = ttk.Button(buttons, text="Actualizar lista", command=fetch)
            refresh_button.pack(side="left")
            use_button = ttk.Button(buttons, text="Vincular seleccionado", style="Accent.TButton", command=use, state="disabled")
            use_button.pack(side="right")
            ttk.Button(buttons, text="Cancelar", command=dialog.destroy).pack(side="right", padx=8)
            tree.bind("<Double-1>", lambda _: use())
            dialog.bind("<Return>", lambda _: use())
            dialog.bind("<Escape>", lambda _: dialog.destroy())
            dialog.grab_set()
            field.focus_set()
            fetch()

        def publish():
            if self.demo:
                messagebox.showinfo("Publicar en Falcon","Conecta un perfil Falcon para publicar scripts.",parent=window)
                return
            source = draft.get("1.0","end-1c")
            if not source.strip():
                messagebox.showinfo("Publicar en Falcon","Pega el script o abre un archivo primero.",parent=window)
                return
            if not save():
                return
            self.busy = True
            publish_button.state(["disabled"])
            publish_button.configure(text="Publicando…")
            replies = queue.Queue()
            def upload():
                try:
                    if linked and published.get()==linked.get("name") and hashlib.sha256(source.encode("utf-8")).hexdigest()==linked.get("sha256"):
                        self.service.verify(linked["name"])
                        result = "Script vinculado y contenido verificado en Falcon."
                    else:
                        result = self.service.publish_script(app,source)
                    replies.put((True,result))
                except FalconError as err:
                    text = "Falcon rechazó la publicación. Revisa Real time response (admin): Write y Read." if err.code==403 else str(err)
                    replies.put((False,text))
                except Exception as err:
                    replies.put((False,str(err)))
            def completed():
                try:
                    ok,text = replies.get_nowait()
                except queue.Empty:
                    self.root.after(150,completed)
                    return
                self.busy = False
                if publish_button.winfo_exists():
                    publish_button.state(["!disabled"])
                    publish_button.configure(text="Publicar en Falcon")
                self.footer.set(text)
                (messagebox.showinfo if ok else messagebox.showerror)("Publicar en Falcon",text,parent=self.root)
            threading.Thread(target=upload,daemon=True).start()
            self.root.after(150,completed)

        actions = ttk.Frame(frame)
        actions.grid(row=3,column=0,sticky="ew",pady=(8,4))
        def import_file():
            ext = "*.ps1" if app["platform"].casefold()=="windows" else "*.sh"
            file = filedialog.askopenfilename(parent=window,filetypes=[("Script del programa",ext)])
            if not file:
                return
            try:
                data = Path(file).read_bytes()
                source = data.decode("utf-16" if data.startswith((b"\xff\xfe",b"\xfe\xff")) else "utf-8-sig")
            except (UnicodeError,OSError) as err:
                messagebox.showerror("Abrir script",str(err),parent=window)
                return
            draft.delete("1.0","end")
            draft.insert("1.0", source.replace("\r\n","\n"))
        def save_and_return():
            if save():
                tabs.select(devices)
        ttk.Button(actions,text="Guardar y volver a equipos",style="Accent.TButton",command=save_and_return).pack(side="left")
        publish_button = ttk.Button(actions,text="Publicar en Falcon",command=publish)
        publish_button.pack(side="left",padx=6)
        ttk.Button(actions,text="Elegir script de Falcon…",command=select_cloud_script).pack(side="left",padx=6)
        hint=ttk.Label(frame,text="Publica un script nuevo o elige uno existente de Falcon. Después selecciona los equipos para enviarlo.",
                       wraplength=440,style="Muted.TLabel")
        hint.grid(row=4,column=0,sticky="w",pady=(2,4))
        frame.bind("<Configure>",lambda event:hint.configure(wraplength=max(240,event.width-30)))
        opts = ttk.Frame(devices)
        opts.pack(side="bottom",fill="x",pady=(8,0))
        offline = tk.BooleanVar(value=False)
        choose_script=ttk.Button(opts,text="Editar desinstalador" if app["script"] else "Elegir desinstalador",
                                 command=lambda:tabs.select(frame))
        choose_script.grid(row=0,column=0,sticky="w",padx=(0,6))
        action_group=ttk.Frame(opts)
        action_group.grid(row=0,column=1,sticky="e")
        opts.columnconfigure(1,weight=1)
        queue_choice=ttk.Checkbutton(action_group,text="Ejecutar al reconectarse",variable=offline)
        queue_choice.pack(side="left",padx=(0,12))

        auto_opts=ttk.Frame(frame)
        def show_auto():
            if auto_opts.winfo_manager():
                auto_opts.grid_remove()
                more.configure(text="▸ Regla automática")
            else:
                auto_opts.grid(row=6,column=0,sticky="w")
                more.configure(text="▾ Regla automática")
        more=ttk.Button(frame,text="▸ Regla automática",command=show_auto)
        more.grid(row=5,column=0,sticky="w",pady=(4,0))
        ttk.Checkbutton(auto_opts,text="Ejecutar al reconectarse",variable=offline).pack(anchor="w",pady=3)
        def automatic():
            if not draft.get("1.0","end-1c").strip() or not save():
                messagebox.showinfo("Script","Guarda primero el script del programa.",parent=window)
                return
            name = published.get()
            if not messagebox.askyesno("Regla automática" if not self.demo else "Regla automática simulada",
                    f"{app['name']} · {app['vendor']} · {app['platform']}\nScript RTR: {name}\n\n"
                    f"Se tramitarán las instalaciones actuales ({sum(bool(r['aid']) for r in hosts.rows)} equipos con sensor) "
                    "y las futuras en todos los equipos de este inventario.\n"
                    f"Cola al reconectarse: {'sí' if offline.get() else 'no'}.\n\n"
                    "¿Activar la regla con esta versión del script?",parent=window):
                return
            with self.db:
                self.db.execute("INSERT OR REPLACE INTO policy VALUES(?,?,?)",(aid,name,offline.get()))
            self.tabs.select(2)
            self.refresh()
            self.sync()
        rule = ttk.Button(auto_opts,text="Desinstalar al detectar este programa…",command=automatic)
        rule.pack(anchor="w",pady=(6,0))
        def launch():
            if self.busy:
                messagebox.showinfo("Operación en curso","Espera a que termine la consulta actual.",parent=window)
                return
            targets = sorted(hosts.marked)
            if not targets or not draft.get("1.0","end-1c").strip():
                tabs.select(frame)
                messagebox.showinfo("Desinstalador","Carga el script de esta aplicación. Tus equipos quedarán marcados.",parent=window)
                return
            if not save():
                return
            cname = published.get()
            mode = "Simulación local" if self.demo else "Desinstalación real por RTR"
            if not messagebox.askyesno(mode,f"{app['name']} · {app['platform']}\n{len(targets)} equipos seleccionados\nScript RTR: {cname}\nCola al reconectarse: {'sí' if offline.get() else 'no'}\n\n¿Confirmas el envío?",parent=window):
                return
            ids = plan(self.db,aid,targets,offline.get(),uuid.uuid4().hex[:10])
            self.tabs.select(1)
            self.refresh()
            if ids:
                self.start(lambda db,progress:dispatch(db,self.service,ids,progress))
            else:
                messagebox.showinfo("Campaña","Los equipos ya tienen una orden pendiente o cambiaron de estado.")
        send = ttk.Button(action_group,text="Revisar desinstalación…",style="Danger.TButton",command=launch)
        send.pack(side="left")
        def fit_actions(event):
            needed=choose_script.winfo_reqwidth()+action_group.winfo_reqwidth()+18
            if event.width<needed:
                action_group.grid_configure(row=1,column=0,columnspan=2,sticky="e",pady=(6,0))
            else:
                action_group.grid_configure(row=0,column=1,columnspan=1,sticky="e",pady=0)
        opts.bind("<Configure>",fit_actions)
        def update_buttons(count):
            complete = self.demo or self.db.execute("SELECT 1 FROM meta WHERE key='applications_scope'").fetchone()
            send.configure(state="normal" if count and complete else "disabled")
            rule.configure(state="normal" if complete else "disabled")
            if complete:
                banner.pack_forget()
        hosts = HostPicker(devices,self,aid,update_buttons,verify_now)
        hosts.pack(fill="both",expand=True)


def choose_connection(root, dark=False, asset_directory=None):
    palette(root,dark)
    dialog = tk.Toplevel(root)
    dialog.title(f"GestorFalcon {__version__} · Falcon App Uninstaller")
    dialog.resizable(False,False)
    box = ttk.Frame(dialog, padding=(36,30))
    box.pack(fill="both", expand=True)
    box.columnconfigure(0, weight=1)
    brand = ttk.Frame(box)
    brand.grid(row=0,column=0,sticky="w",pady=(0,24))
    if asset_directory is None:
        app_path = sys.executable if getattr(sys,"frozen",False) else __file__
        asset_directory = Path(app_path).resolve().parent
    dialog._brand_image = crowdstrike_image(root,asset_directory)
    if dialog._brand_image is not None:
        ttk.Label(brand,image=dialog._brand_image).pack(side="left",padx=(0,10))
    ttk.Label(brand,text="CROWDSTRIKE",style="CrowdStrike.TLabel").pack(side="left")
    heading = ttk.Frame(box)
    heading.grid(row=1,column=0,sticky="ew",pady=(0,22))
    ttk.Label(heading,text="GestorFalcon",style="Muted.TLabel").pack(anchor="w")
    ttk.Label(heading,text="Conecta con Falcon",style="Title.TLabel").pack(anchor="w",pady=(5,6))
    ttk.Label(heading,text="Gestiona aplicaciones y equipos desde un solo lugar.",style="Muted.TLabel",wraplength=400).pack(anchor="w")
    regions = ("us2","us1","eu1","usgov1","usgov2")
    region = ttk.Combobox(box, values=regions, state="readonly")
    default = os.getenv("FALCON_REGION","us2").lower()
    region.set(default if default in regions else "us2")
    client = ttk.Entry(box, width=48)
    secret = ttk.Entry(box, width=48, show="•")
    client.insert(0,os.getenv("FALCON_CLIENT_ID",""))
    secret.insert(0,os.getenv("FALCON_CLIENT_SECRET",""))
    for i,(label,widget) in enumerate([("Región",region),("Client ID",client),("Client Secret",secret)]):
        ttk.Label(box,text=label).grid(row=2+i*2,column=0,sticky="w",pady=(0,6))
        widget.grid(row=3+i*2,column=0,sticky="ew",pady=(0,16),ipady=4)
    visible = tk.BooleanVar(value=False)
    ttk.Checkbutton(box,text="Mostrar secret",variable=visible,
        command=lambda:secret.configure(show="" if visible.get() else "•")).grid(row=8,column=0,sticky="w")
    scopes = ttk.Frame(box,padding=(0,8))
    def toggle_scopes():
        if scopes.winfo_manager():
            scopes.grid_remove()
            scope_button.configure(text="Ver permisos necesarios ▾")
        else:
            scopes.grid(row=10,column=0,sticky="ew")
            scope_button.configure(text="Ocultar permisos ▴")
    scope_button = ttk.Button(box,text="Ver permisos necesarios ▾",style="Side.TButton",command=toggle_scopes)
    scope_button.grid(row=9,column=0,sticky="w",pady=(10,0))
    for label in ("Inventario · Assets → Read", "Equipos · Hosts → Read",
                  "Sesión RTR · Real time response → Read",
                  "Desinstalación · Real time response (admin) → Write"):
        ttk.Label(scopes,text=label,style="Muted.TLabel").pack(anchor="w",pady=2)
    status = tk.StringVar()
    ttk.Label(box,textvariable=status,style="Muted.TLabel",wraplength=420).grid(row=11,column=0,sticky="w",pady=10)
    choice = None
    replies = queue.Queue()

    def finish(service, profile):
        nonlocal choice
        choice = service, profile
        secret.delete(0,"end")
        dialog.destroy()

    def check_reply():
        try:
            service, profile, error = replies.get_nowait()
        except queue.Empty:
            dialog.after(120,check_reply)
            return
        if service is not None:
            finish(service,profile)
        else:
            status.set(error)
            connect_button.state(["!disabled"])
            client.state(["!disabled"])
            secret.state(["!disabled"])
            region.configure(state="readonly")

    def connect():
        if connect_button.instate(["disabled"]):
            return
        cid, key, cloud = client.get().strip(), secret.get().strip(), region.get()
        if not cid or not key:
            status.set("Completa el Client ID y el Client Secret.")
            (client if not cid else secret).focus_set()
            return
        status.set("Comprobando acceso al inventario…")
        for widget in (client,secret,region,connect_button):
            widget.state(["disabled"])
        def verify():
            try:
                service = Falcon(cid,key,cloud)
                service.inventory_sample = service.inspect_inventory()
                profile = hashlib.sha256(f"{cloud}:{cid}".encode()).hexdigest()[:24]
                replies.put((service,profile,""))
                return
            except ModuleNotFoundError:
                message = "Instala la biblioteca con python -m pip install crowdstrike-falconpy y vuelve a conectar."
            except FalconError as err:
                message = {
                    401: "Falcon rechazó las credenciales. Revisa la región, el Client ID y el Client Secret.",
                    403: "Falcon denegó la lectura del inventario. Revisa Assets → Read y el acceso a Discover.",
                }.get(err.code, f"Falcon respondió con el código {err.code}. Revisa la región y la conexión.")
            except Exception:
                message = "No se pudo consultar Falcon. Revisa la región, la conexión y las credenciales."
            replies.put((None,None,message))
        threading.Thread(target=verify,daemon=True).start()
        dialog.after(120,check_reply)

    ttk.Button(box,text="Explorar con datos de ejemplo",style="Side.TButton",command=lambda:finish(Demo(),"demostracion")).grid(row=13,column=0,pady=(12,0))
    connect_button = ttk.Button(box,text="Conectar a Falcon",style="Brand.TButton",command=connect)
    connect_button.grid(row=12,column=0,sticky="ew",ipady=4)
    dialog.update_idletasks()
    x = max(0,(dialog.winfo_screenwidth()-dialog.winfo_reqwidth())//2)
    y = max(0,(dialog.winfo_screenheight()-dialog.winfo_reqheight())//2)
    dialog.geometry(f"+{x}+{y}")
    dialog.bind("<Return>",lambda event:connect())
    client.focus_set()
    root.wait_window(dialog)
    return choice


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    modes = parser.add_mutually_exclusive_group()
    modes.add_argument("--falcon", action="store_true",help="Abrir el menú de conexión")
    modes.add_argument("--demo", action="store_true",help="Abrir directamente la demostración")
    args = parser.parse_args()
    root = create_root()
    root.withdraw()
    app_path = sys.executable if getattr(sys, "frozen", False) else __file__
    data = Path(app_path).resolve().parent / "datos"
    choice = (Demo(),"demostracion") if args.demo else choose_connection(root,read_theme(data),data.parent)
    if choice is None:
        root.destroy()
        return
    service, profile = choice
    data.mkdir(exist_ok=True)
    if isinstance(service,Falcon):
        (data / (profile+"-muestra.json")).write_text(
            json.dumps(service.inventory_sample,ensure_ascii=False,indent=2),encoding="utf-8")
    # Mantener un único escritor/ejecutor por perfil en el escritorio Windows.
    import msvcrt
    with (data / (profile+".lock")).open("a+b") as lock:
        lock.seek(0)
        try:
            msvcrt.locking(lock.fileno(), msvcrt.LK_NBLCK, 1)
        except OSError:
            messagebox.showinfo("Gestor de aplicaciones","Este perfil ya está abierto.",parent=root)
            root.destroy()
            return
        Panel(root,data/(profile+".sqlite3"),service)
        root.deiconify()
        root.mainloop()


if __name__ == "__main__":
    main()
