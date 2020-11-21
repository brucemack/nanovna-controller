Overview
========
This is a simple control panel for the NanoVNA.  An HTML interface is provided.

This program was designed by N1FMV and KC1FSZ.

Runnning Instructions
=====================
There are two parameters:
* The serial (comm) port to use
* The TCP port to listen on for HTTP requests.  Defaults to 8080.

NanoVNA Technial Information
============================
The data command returns a list of reflection coefficients in real/imaginary pairs.  Each line contains one coefficient and the real/imaginary parts are space-delimited.

Gamma is the magnitude of the complex reflect coefficient.

VSWR = (1+Gamma)/(1-Gamma)

Requirements
============
* pyserial - For serial communications to the NanoVNA
* jinja2 - For HTML templates
* pandas - Needed for data interpolation
* Flask - Needed for web serving

Links
=====
* Prototype UI: https://brucemack.github.io/nanovna 
* NanoVNA command reference: https://4ham.ru/wp-content/uploads/2020/05/NanoVNA_Console_Commands_Dec-9-19-1.pdf
