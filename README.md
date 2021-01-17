Overview
========
This is a simple control interface for the NanoVNA.  An HTML interface is provided 
that allows the user to perform VSWR sweeps of antennas or other devices.  
Calibration is also possible using the interface.

This program was designed by N1FMV and KC1FSZ.

NanoVNA Technial Information
============================
The data command causes the NanoVNA to return a list of reflection coefficients in real/imaginary pairs.  Each line contains one coefficient and the real/imaginary parts are space-delimited.

Gamma is the magnitude of the complex reflect coefficient.

VSWR = (1+Gamma)/(1-Gamma)

One Time Setup
==============
On Windows:

python -m venv dev
dev\Scripts\activate.bat
python -m pip install --upgrade pip
pip install pyserial
pip install pandas
pip install Flask
pip install PyInstaller

NOTE: This is needed to work around a bug in Windows 10 2004.  See https://developercommunity.visualstudio.com/content/problem/1207405/fmod-after-an-update-to-windows-2004-is-causing-a.html

pip install numpy==1.19.3

Running
=======
Windows, command-line, development:

* python main.py .

Building Requirements
=====================
* pyserial - For serial communications to the NanoVNA
* pandas - Needed for data interpolation
* Flask - Needed for web serving

PyInstaller Packaging
=====================
pip install PyInstaller
pyinstaller --onefile main.py --name nanovna-controller
The .exe will end up in /dist
Zip the .exe, config.ini, and the static folder together.

Links
=====
* Prototype UI: https://brucemack.github.io/nanovna 
* NanoVNA command reference: https://4ham.ru/wp-content/uploads/2020/05/NanoVNA_Console_Commands_Dec-9-19-1.pdf

Precise Installation Instructions
=================================
* Download nanovna-controller.zip
* Unzip the file.  This will create a base folder that contains the .exe, the config.ini file, and a static folder.
* Edit the config.ini file:
  - Set the workdir to a location where you'd like to store working files created by the controller.    
  - Set the port you want to listen on for HTTP connections.
* Open a command prompt and run the nanovna-controller.exe 
* Point your browser to http://localhost:8080.  Or use whatever port number you have configured in the config.ini file

Change Notes
============
Version 2:
* Defaults to COM6
* Able to auto-sense the base dir
* Error checks for config.ini and static dir
* Changing numpuy version to address Windows bug
