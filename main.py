"""
NanoVNA Controller
Designed by N1FMV and KC1FSZ
"""
import numpy as np
import nanovna as nv
from calcs import *
from flask import Flask, request, make_response, send_from_directory, send_file, jsonify, cli
import json
import logging
import configparser
import sys
import os
import util
import math, cmath 

def load_user_config():
    try:
        with open(static_config["workdir"] + "/userconfig.json") as f:
            return json.load(f)
    except Exception as ex:
        logging.warning("No user configuration setup yet")
        return {}


def save_user_config():
    with open(static_config["workdir"] + "/userconfig.json", "w") as f:
        json.dump(user_config, f)

VERSION = "5"

# Determine where the script is actually running from 
run_base_dir = os.path.dirname(os.path.realpath(__file__))

# Check to see if the user specified an explicit base directory
if len(sys.argv) >= 2:
    base_dir = sys.argv[1]
else:
    base_dir = run_base_dir

# Configure logging
logging.basicConfig(filename=base_dir + "/log.txt", 
    format='%(asctime)s %(message)s', level=logging.INFO)
logging.getLogger().addHandler(logging.StreamHandler(sys.stdout))

logging.info("KC1FSZ NanoVNA Controller")
logging.info("Version is " + VERSION)
logging.info("Running from " + run_base_dir)
logging.info("Base directory is " + base_dir)

# Make sure the config file and static directories exist
if not os.path.exists(base_dir + "/config.ini"):
    logging.error("config.ini is not found")
    quit()
if not os.path.exists(base_dir + "/static"):
    logging.error("static directory is not found")
    quit()

# Load .ini file
config = configparser.ConfigParser()
config.read(base_dir + "/config.ini")
static_config = config["DEFAULT"]

logging.info("Working directory is " + static_config["workdir"])
logging.info("Listen port is " + static_config["listenport"])

calibration_config = { }
visible_ports = nv.Nanovna.list_serial_ports()

for p in visible_ports:
    logging.info("Found a serial port " + p)

# Initial load of configuration properties
user_config = load_user_config()

# Default the USB port if none has been explicitly defined in the config
if not ("port" in user_config):
    if len(visible_ports):
        if len(visible_ports) == 1:
            user_config["port"] = visible_ports[0]
        else:
            # Try to avoid COM1 on Windows (generally not the NanoVNA)
            for p in visible_ports: 
                if p != "COM1":
                    user_config["port"] = p
                    break
    else:    
        user_config["port"] = "COM6"

    logging.info("Defaulted serial port to " + user_config["port"])

    # Force a save to get the default
    save_user_config()
else:
    logging.info("Using configured serial port " + user_config["port"])

nanovna = nv.Nanovna()

# Flask routes
cli.show_server_banner = lambda *_: None
app = Flask(__name__)


@app.route("/static/<filename>")
def root2(filename):
    return send_file(base_dir + "/static/" + filename)


@app.route("/")
def root():
    """ Sends static home page. """
    return send_file(base_dir + "/static/index.html")


@app.route("/api/config", methods=["GET", "POST"])
def config():
    """ Allows the client to read and write the user configuration parameters. """
    if request.method == "POST":
        for item in request.form.items():
            user_config[item[0]] = item[1]
            logging.info("Changed config value " + item[0] + "=" + item[1])
        save_user_config()
    return jsonify(user_config)


@app.route("/api/calibrate", methods=["GET"])
def calibrate():

    try:
        # Get connected to the NanoVNA
        nanovna.connect_if_necessary(user_config["port"])

        if request.args["step"] == "0":
            nanovna.run_command("cal reset")
        elif request.args["step"] == "1":
            if request.args.get("cal_preset").strip() == "":
                raise Exception("Calibration preset is missing")
            calibration_config["cal_preset"] = int(request.args.get("cal_preset"))
        elif request.args["step"] == "2":
            if request.args.get("start_frequency_mhz").strip() == "":
                raise Exception("Start frequency is missing")
            try:
                start_frequency = int(float(request.args.get("start_frequency_mhz")) * 1000000)
            except Exception as ex:
                raise Exception("Invalid start frequency: " + str(ex))
            if request.args.get("end_frequency_mhz").strip() == "":
                raise Exception("End frequency is missing")
            try:
                end_frequency = int(float(request.args.get("end_frequency_mhz")) * 1000000)
            except Exception as ex:
                raise Exception("Invalid end frequency: " + str(ex))
            if start_frequency >= end_frequency:
                raise Exception("Frequency range was not valid")

            # Set the sweep range
            nanovna.run_command("sweep " + str(start_frequency) + " " + str(end_frequency))
            # Cal short
        elif request.args["step"] == "3":
            nanovna.run_command("cal short")
        elif request.args["step"] == "4":
            nanovna.run_command("cal open")
        elif request.args["step"] == "5":
            nanovna.run_command("cal load")
            nanovna.run_command("cal done")
            # Save the designated present
            nanovna.run_command("save " + str(calibration_config["cal_preset"]))

        return "OK"

    except Exception as ex:
        logging.error("Error in calibration", exc_info=True)
        result = {
            "error": True,
            "message": ex.args[0]
        }
        return jsonify(result)


@app.route("/api/status", methods=["GET"])
def status():

    try:
        # Get connected to the NanoVNA
        nanovna.connect_if_necessary(user_config["port"])
        # Execute various status commands
        vbat_lines = nanovna.run_command("vbat")
        vbat = float(vbat_lines[0][:-2]) / 1000
        version_lines = nanovna.run_command("version")

        result = {
            "version": version_lines[0],
            "voltage": vbat
        }
        return result

    except Exception as ex:
        logging.error("Error in status", exc_info=True)
        result = {
            "error": True,
            "message": ex.args[0]
        }
        return jsonify(result)


@app.route("/api/sweep", methods=["GET", "POST"])
def sweep():
    try:
        # Get connected to the NanoVNA
        nanovna.connect_if_necessary(user_config["port"])

        # Process request parameters
        one_row = request.args.get("one_row")
        
        if request.args.get("cal_preset").strip() == "":
            raise Exception("Calibration preset is missing")
        cal_preset = int(request.args.get("cal_preset"))
        if request.args.get("start_frequency_mhz").strip() == "":
            raise Exception("Start frequency is missing")
        try:
            start_frequency = int(float(request.args.get("start_frequency_mhz")) * 1000000)
        except Exception as ex:
            raise Exception("Invalid start frequency: " + str(ex))
        if request.args.get("end_frequency_mhz").strip() == "":
            raise Exception("End frequency is missing")
        try:
            end_frequency = int(float(request.args.get("end_frequency_mhz")) * 1000000)
        except Exception as ex:
            raise Exception("Invalid end frequency: " + str(ex))
        if start_frequency >= end_frequency:
            raise Exception("Frequency range was not valid")
        if request.args.get("step_frequency_mhz").strip() == "":
            step_count = 10
            step_frequency = (end_frequency - start_frequency) / step_count
        else:
            try:
                step_frequency = int(float(request.args.get("step_frequency_mhz")) * 1000000)
                if step_frequency < 0:
                    raise Exception("Step must be positive")
            except Exception as ex:
                raise Exception("Invalid step: " + str(ex))
            step_count = int((end_frequency - start_frequency) / step_frequency)
        if step_count > 50:
            raise Exception("There are too many steps")
        if step_count == 0:
            raise Exception("There are not enough steps")

        nanovna.run_command("info")
        nanovna.run_command("recall " + str(cal_preset))
        # Set the sweep range
        nanovna.run_command("sweep " + str(start_frequency) + " " + str(end_frequency))
        # Get the battery voltage in volts
        #vbat_lines = nv.run_command(ser, "vbat")
        #vbat = float(vbat_lines[0][:-2]) / 1000
        
        # Collect the frequencies of the sweep
        lines = nanovna.run_command("frequencies")
        frequency_list = [float(line) for line in lines]
        # Collect the reflection coefficients of the sweep
        rc_list = nanovna.get_complex_data()
        if len(frequency_list) != len(rc_list):
            raise Exception("Data length error")

        # Convert to VSWR
        vswr_list = [nanovna.reflection_coefficient_to_vswr(rc) for rc in rc_list]
        z_list = [nanovna.reflection_coefficient_to_z(rc) for rc in rc_list]
        s11_list = [nanovna.reflection_coefficient_to_s11(rc) for rc in rc_list]
        # Make up the C and L data
        c_list = []
        l_list = []
        for i in range(0, len(frequency_list)):
            c_list.append(nanovna.reflection_coefficient_to_c(rc_list[i], frequency_list[i]))
            l_list.append(nanovna.reflection_coefficient_to_l(rc_list[i], frequency_list[i]))

        # Re-sample using the start/end/step provided by the user.  Linear
        # interpolation is automatically used
        frequency_space = np.linspace(start_frequency, end_frequency - step_frequency, step_count)
        result_frequencies = []

        result_vswr = []
        result_zr = []
        result_zi = []
        result_zmag = []
        result_zphase = []
        result_s11 = []
        result_c = []
        result_l = []

        for frequency in frequency_space:
            result_frequencies.append(frequency)
            
            vswr = interp(frequency_list, vswr_list, frequency)
            result_vswr.append(vswr)
            
            z = interp(frequency_list, z_list, frequency)
            result_zr.append(z.real)
            result_zi.append(z.imag)
            result_zmag.append(abs(z))

            rc = interp(frequency_list, rc_list, frequency)
            result_zphase.append(np.angle(rc, True))

            s11 = interp(frequency_list, s11_list, frequency)
            result_s11.append(s11)

            c = interp(frequency_list, c_list, frequency)
            result_c.append(c)

            l = interp(frequency_list, l_list, frequency)
            result_l.append(l)

        # Find the lowest value
        min_vswr = min(result_vswr)
        for i in range(len(result_frequencies)):
            if result_vswr[i] == min_vswr:
                min_index = i
        # Format the result
        result = {
            "error": False,
            "headers": ["{:.03f}".format(f / 1000000.0) for f in result_frequencies],
            "rows": [
                {
                    "header": "VSWR",
                    "cells": ["{:.02f}".format(v) for v in result_vswr]
                },
            ]
        }
        if one_row == "false":
            result["rows"].append(
                {
                    "header": "Real Z",
                    "cells": ["{:.02f}".format(v) for v in result_zr]
                })
            result["rows"].append(
                {
                    "header": "Imag Z",
                    "cells": ["{:.02f}".format(v) for v in result_zi]
                })
            result["rows"].append(
                {
                    "header": "Magnitude Z",
                    "cells": ["{:.02f}".format(v) for v in result_zmag]
                })
            result["rows"].append(
                {
                    "header": "Series C",
                    "cells": [ util.fmt_si(v, "F") for v in result_c]
                })
            result["rows"].append(
                {
                    "header": "Series L",
                    "cells": [ util.fmt_si(v, "H") for v in result_l]
                })
            result["rows"].append(
                {
                    "header": "S11 Return Loss",
                    "cells": [ "{:.00f}".format(v) for v in result_s11]
                })
            result["rows"].append(
                {
                    "header": "S11 Phase",
                    "cells": ["{:.00f}".format(v) for v in result_zphase]
                })

        # Tweak the minimum VSWR with the best match annotation
        result.get("headers")[min_index] = result.get("headers")[min_index] + " best match"
        #result.get("rows")[0].get("cells")[min_index] = result.get("rows")[0].get("cells")[min_index] + " best match"

        return jsonify(result)

    except Exception as ex:
        logging.error("Error in sweep", exc_info=True)
        result = {
            "error": True,
            "message": ex.args[0]
        }
        return jsonify(result)


if __name__ == "__main__":
    app.run(host=static_config["listenhost"], port=static_config["listenport"])
