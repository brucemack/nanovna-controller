Overview
========
This is a simple control interface for the NanoVNA.  An HTML interface is provided 
that allows the user to perform VSWR sweeps of antennas or other devices.  Calibration is also possible using the interface.

This program was designed by N1FMV and KC1FSZ.

Precise Installation Instructions
=================================
* Download nanovna-controller.zip from the release area: https://github.com/brucemack/nanovna-controller/releases
* Unzip the file.  This will create a base folder that contains the .exe, the config.ini file, and a static folder.
* Edit the config.ini file:
  - Set the workdir to a location where you'd like to store working files created by the controller.    
  - Set the port you want to listen on for HTTP connections.
* Open a command prompt 
* Change directories (cd) into the base folder where the files were unzipped.
* Run the nanovna-controller.exe 
* Point your browser to http://localhost:8080.  Or use whatever port number you have configured in the config.ini file.
* Use the Administration tab to configure the serial port where the NanoVNA is connected.

NanoVNA Technical Information
============================
The data command causes the NanoVNA to return a list of reflection coefficients in real/imaginary pairs.  Each line contains one coefficient and the real/imaginary parts are space-delimited.

Gamma is the magnitude of the complex reflect coefficient.

VSWR = (1+Gamma)/(1-Gamma)

One Time Setup For Development
==============================
On Windows:

* python -m venv dev
* dev\Scripts\activate.bat
* python -m pip install --upgrade pip
* pip install pyserial
* pip install Flask
* pip install PyInstaller

Resolvoing Numpy Problen on Windows 10 2004
--------------------------------------------
This is needed to work around a bug in Windows 10 2004.  See https://developercommunity.visualstudio.com/content/problem/1207405/fmod-after-an-update-to-windows-2004-is-causing-a.html

Microsoft is supposed to have this problem fixed in the next update 
of Windows 10.

pip install numpy==1.19.3

Running (Development Mode)
==========================
Windows, command-line, development:

* python main.py

Building Requirements
=====================
* pyserial - For serial communications to the NanoVNA
* Flask - Needed for web serving

PyInstaller Packaging
=====================

* pip install PyInstaller
* pyinstaller --onefile main.py --name nanovna-controller

The .exe will end up in /dist
Zip the .exe, config.ini, and the static folder together.

Resolving Issues with PyInstaller Virus Detection
-------------------------------------------------
Many anti-malware tools have a problem with the pre-built bootloader
shipped in the standard PyInstaller distribution.  The work-around 
is to pull the source distribution of PyInstaller and build the 
bootloader locally.

* git clone https://github.com/pyinstaller/pyinstaller.git
* cd pyinstaller
* cd bootloader
* python ./waf all
* Switch to the nanovna-controller virtual environment
* pip install c:/Users/bruce/git/pyinstaller

Links
=====
* Prototype UI: https://brucemack.github.io/nanovna 
* NanoVNA command reference: https://4ham.ru/wp-content/uploads/2020/05/NanoVNA_Console_Commands_Dec-9-19-1.pdf

Change Notes
============

Version 3
---------
* Major rework of calibration process.
* Cleaned up some of the noise on the console window at startup.
* Automatically stripping spaces from serial port entry on administration tab.
* If a single number is entered into the serial port box, automatically add the "com" prefix.
* Fixed problem with complex impedance.  Now showing real and imaginary components.
* Using locally-compiled PyInstaller bootloader to avoid issues with Windows Threat Detection.

Version 2
---------
* Defaults to COM6
* Able to auto-sense the base dir
* Error checks for config.ini and static dir
* Changing numpuy version to address Windows bug

Version 1
---------
* Initial version

Screenshots
===========

Here are some pictures of what the HTML screens look like.  You might be thinking 
that the UI is not very impressive, but please keep in mind that 
one of the design objectives was to create an application that is easy to use
for visually-impaired operators.  The HTML has been structured 
using semantic mark-up and ARIA tags so that it can be integrated smoothly with 
the Microsoft Narrator screen reader.  I am new to this technology but I find it
quite interesting.  I would welcome comments from people with more experience in 
this area.

The sweep panel:

![Sweep Panel Picture](docs/s1.png)

The complex sweep panel:

![Complex Sweep Panel Picture](docs/cs1.png)

The administration panel:

![Administration Panel Picture](docs/ap1.png)

The status panel:

![Status Panel Picture](docs/sp.png)
