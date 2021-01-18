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

VERSION = "3"
base_dir_2 = os.path.dirname(os.path.realpath(__file__))

if len(sys.argv) >= 2:
    # Get static location
    base_dir = sys.argv[1]
else:
    base_dir = base_dir_2

# Configure logging
logging.basicConfig(filename=base_dir + "/log.txt", format='%(asctime)s %(message)s', level=logging.INFO)
logging.getLogger().addHandler(logging.StreamHandler(sys.stdout))

logging.info("NanoVNA Controller")
logging.info("Version " + VERSION)
logging.info("Running from " + base_dir_2)
logging.info("Base Directory " + base_dir)

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

user_config = { }
calibration_config = { }


def load_user_config():
    global user_config
    try:
        with open(static_config["workdir"] + "/userconfig.json") as f:
            user_config = json.load(f)
    except Exception as ex:
        logging.warning("Unable to read user configuration")
        user_config = {}

    # Program some defaults
    if not ("port" in user_config):
        user_config["port"] = "COM6"


def save_user_config():
    with open(static_config["workdir"] + "/userconfig.json", "w") as f:
        json.dump(user_config, f)
        logging.info("Saved user configuration")
        logging.info(user_config)


# Initial load of configuration properties
load_user_config()

logging.info("Configured USB port is " + user_config["port"])

nanovna = nv.Nanovna()

for p in nanovna.list_serial_ports():
    logging.info("Found USB port " + p)

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
        # Make the VSWR data
        rc_list = nanovna.get_complex_data()
        # Convert to VSWR
        vswr_list = [nanovna.reflection_coefficient_to_vswr(rc) for rc in rc_list]
        z_list = [nanovna.reflection_coefficient_to_z(rc) for rc in rc_list]
        # Re-sample using the start/end/step provided by the user.  Linear
        # interpolation is automatically used
        frequency_space = np.linspace(start_frequency, end_frequency - step_frequency, step_count)
        result_frequencies = []
        result_vswrs = []
        result_real = []
        result_imaginary = []
        for frequency in frequency_space:
            result_frequencies.append(frequency)
            vswr = interp(frequency_list, vswr_list, frequency)
            result_vswrs.append(vswr)
            z = interp(frequency_list, z_list, frequency)
            result_real.append(z.real)
            result_imaginary.append(z.imag)
        # Find the lowest value
        min_vswr = min(result_vswrs)
        for i in range(len(result_frequencies)):
            if result_vswrs[i] == min_vswr:
                min_index = i
        # Format the result
        result = {
            "error": False,
            "headers": ["{:.03f}".format(f / 1000000.0) for f in result_frequencies],
            "rows": [
                {
                    "header": "VSWR",
                    "cells": ["{:.02f}".format(v) for v in result_vswrs]
                },
            ]
        }
        if one_row == "false":
            result["rows"].append(
                {
                    "header": "Real(Z)",
                    "cells": ["{:.02f}".format(v) for v in result_real]
                })
            result["rows"].append(
                {
                    "header": "Imag(Z)",
                    "cells": ["{:.02f}".format(v) for v in result_imaginary]
                })

        # Tweak the minimum VSWR with the best match annotation
        result.get("headers")[min_index] = result.get("headers")[min_index] + " best match"
        result.get("rows")[0].get("cells")[min_index] = result.get("rows")[0].get("cells")[min_index] + " best match"

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
