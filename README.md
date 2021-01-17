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

Building Requirements
=====================
* pyserial - For serial communications to the NanoVNA
* pandas - Needed for data interpolation
* Flask - Needed for web serving

PyInstaller
==========
pip install PyInstaller
pyinstaller --onefile main.py

Links
=====
* Prototype UI: https://brucemack.github.io/nanovna 
* NanoVNA command reference: https://4ham.ru/wp-content/uploads/2020/05/NanoVNA_Console_Commands_Dec-9-19-1.pdf

Precise Installation Instructions
=================================
* Download nanovna-controller.zip
* Unzip the file.  This will create a base folder that contains the .exe, the config.ini file, and a static folder.
* Edit the config.ini and set the workdir to a location where you'd like to store working files created by the controller.  
* Open a command prompt and run the nanovna-controller.exe file with one command-line argument: the location of the base folder created in the second step above.  This is needed to allow the controller to locate the .ini file and static folder.
* Point your browser to http://localhost:8080.  Or use whatever port number you have configured.
