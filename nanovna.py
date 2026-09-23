import serial
import logging
import serial
import glob
import sys
import math
import time

# Time for the NanoVNA to complete a fresh sweep after the range is changed
SWEEP_SETTLE_TIME_S = 4
# "scan" answers only once all points are measured, which can take several
# seconds (more with many points or low frequencies)
SCAN_TIMEOUT_S = 30
SCAN_POINTS = 101
# scan outmask bits: 1 = frequency, 2 = channel 0 (S11)
SCAN_OUTMASK_FREQ_S11 = 3


class Nanovna:
    """
    Interface for communicating with a NanoVNA
    """
    ser = None
    port = None
    # Whether the firmware has a usable "scan" command; None = not checked yet
    # on this connection
    scan_supported = None

    def connect_if_necessary(self, port):
        """ Opens a connection to the NanoVNA if necessary. """
        # Look for the case where the port is changing
        if port != self.port:
            self.port = None
            if self.ser is not None:
                self.ser.close()
                self.ser = None
        # Look for the case were we need to open the port
        if self.ser is None or not self.ser.isOpen():
            logging.info("Connection was not open yet: " + port)
            try:
                # Open the serial port to the NanoVNA
                self.ser = serial.Serial(port, timeout=2, write_timeout=2)
                self.port = port
                self.scan_supported = None
                self.flush()
                logging.info("Connection is good")
            except Exception as ex:
                logging.error("Unable to open connection", exc_info=True)
                self.ser = None

            if self.ser is None:
                raise Exception("Unable to connect to NanoVNA")
        else:
            pass

    def flush(self):
        """
        Discards anything left in the serial buffers (half-typed commands, a stale
        prompt, output of an earlier command) so the next response lines up with
        the next command. Same approach as NanoVNA-Saver's flushSerialBuffers().
        """
        self.ser.write(b"\r\n\r\n")
        time.sleep(0.1)
        self.ser.reset_input_buffer()
        self.ser.reset_output_buffer()

    def read_response_as_lines(self):
        """
        :param ser: The serial port that is connected (an open) to the NanoVNA
        :return: An array of strings, one for each line returned
        """
        if self.ser is None:
            raise Exception("Not connected")
        # The ch> prompt is used as the delimiter
        try:
            data = self.ser.read_until(b'ch> ')
        except Exception as ex:
            self.ser = None
            raise ex
        if len(data) == 0:
            raise Exception("No data received from NanoVNA")
        # Pull off the last part (not relevant data)
        data = data[:-4]
        # Break into lines and then decode into strings.
        return [line.decode("utf-8") for line in data.splitlines()]

    def run_command(self, command, timeout=None):
        """
        :param command: The command to send
        :param timeout: Read timeout in seconds for this command only (default:
            the port's timeout)
        :return: An array of strings, one for each line returned by the command
        """
        if self.ser is None:
            raise Exception("Not connected")
        logging.info("NanoVNA command: " + command)
        ser = self.ser
        default_timeout = ser.timeout
        try:
            if timeout is not None:
                ser.timeout = timeout
            # Drop unsolicited leftovers so they aren't taken as this response
            ser.reset_input_buffer()
            ser.write((command + "\r").encode("utf-8"))
            lines = self.read_response_as_lines()
        except Exception as ex:
            self.ser = None
            raise ex
        finally:
            ser.timeout = default_timeout
        # We discard the first line because that is the echo of the command
        return lines[1:]

    def get_complex_data(self):
        lines = self.run_command("data")
        # Parse into real/imaginary tokens
        tokenized_lines = [line.split(" ") for line in lines]
        # Make into imaginary numbers
        return [complex(float(token[0]), float(token[1])) for token in tokenized_lines]

    def supports_scan(self):
        """
        Checks (once per connection) whether "scan" is among the commands listed
        by "help". Firmwares format the list differently (one per line with a
        usage text, or all on one line), so any whitespace separated word counts.
        """
        if self.scan_supported is None:
            words = " ".join(self.run_command("help")).split()
            self.scan_supported = any(w.rstrip(":,") == "scan" for w in words)
            logging.info("Firmware supports scan: " + str(self.scan_supported))
        return self.scan_supported

    @staticmethod
    def parse_scan_lines(lines):
        """
        :param lines: Output of "scan" with the frequency and S11 outmask, one
            "frequency real imaginary" line per point
        :return: A list of frequencies and a list of complex reflection coefficients
        """
        frequency_list = []
        rc_list = []
        for line in lines:
            tokens = line.split()
            if len(tokens) < 3:
                raise Exception("Unexpected scan output: " + line)
            frequency_list.append(float(tokens[0]))
            rc_list.append(complex(float(tokens[1]), float(tokens[2])))
        if len(frequency_list) == 0:
            raise Exception("No data returned by scan")
        return frequency_list, rc_list

    def scan_s11(self, start_frequency, end_frequency, points=SCAN_POINTS):
        """
        Measures S11 with "scan", which returns only after a fresh measurement of
        the requested range (with the active calibration applied).
        """
        lines = self.run_command("scan {} {} {} {}".format(
            int(start_frequency), int(end_frequency), points, SCAN_OUTMASK_FREQ_S11),
            timeout=SCAN_TIMEOUT_S)
        return self.parse_scan_lines(lines)

    def sweep_s11(self, start_frequency, end_frequency):
        """
        Measures S11 by setting the sweep range and reading back the data, for
        firmwares without a usable "scan".
        """
        self.run_command("sweep {} {}".format(int(start_frequency), int(end_frequency)))
        # "sweep" returns immediately while the device keeps sweeping in the
        # background; "data" would return the previous range/calibration until
        # a new sweep has completed
        time.sleep(SWEEP_SETTLE_TIME_S)
        lines = self.run_command("frequencies")
        frequency_list = [float(line) for line in lines]
        rc_list = self.get_complex_data()
        if len(frequency_list) != len(rc_list):
            raise Exception("Data length error")
        return frequency_list, rc_list

    def measure_s11(self, start_frequency, end_frequency):
        """
        :return: A list of frequencies and a list of complex reflection
            coefficients for the range, using "scan" when the firmware supports
            it and the sweep/readout otherwise
        """
        if self.supports_scan():
            try:
                result = self.scan_s11(start_frequency, end_frequency)
                logging.info("Measured with scan")
                return result
            except Exception:
                # A dropped connection isn't a firmware limitation
                if self.ser is None:
                    raise
                # E.g. an older firmware whose scan has no outmask and prints nothing
                logging.warning("scan output unusable, falling back to sweep", exc_info=True)
                self.scan_supported = False
                self.flush()
        result = self.sweep_s11(start_frequency, end_frequency)
        logging.info("Measured with sweep")
        return result

    @staticmethod
    def reflection_coefficient_to_vswr(rc):
        """
        :param rc: A complex reflection coefficient
        :return: The scalar VSWR
        """
        gamma = abs(rc)
        return (1.0 + gamma) / (1.0 - gamma)


    @staticmethod
    def reflection_coefficient_to_z(rc):
        """
        Z = Zo * ((1 + Γ) / (1 - Γ))
        """
        return 50.0 * (1.0 + rc) / (1 - rc)

    @staticmethod
    def reflection_coefficient_to_s11(rc):
        """
        s11 = 20 * log10(mag(Γ))
        """
        gamma = abs(rc)
        return 20.0 * math.log10(gamma)

    @staticmethod
    def reflection_coefficient_to_c(rc, f):
        """
        Z = Zo * ((1 + Γ) / (1 - Γ))
        C = -1 / (w * Zi)
        """
        z = 50.0 * (1.0 + rc) / (1 - rc)
        w = 2 * math.pi * f
        return -1 / (w * z.imag)

    @staticmethod
    def reflection_coefficient_to_l(rc, f):
        """
        Z = Zo * ((1 + Γ) / (1 - Γ))
        L = Zl / w
        """
        z = 50.0 * (1.0 + rc) / (1 - rc)
        w = 2 * math.pi * f
        return z.imag / w



    @staticmethod
    def list_serial_ports():
        """ Lists serial port names

            :raises EnvironmentError:
                On unsupported or unknown platforms
            :returns:
                A list of the serial ports available on the system
        """
        if sys.platform.startswith('win'):
            ports = ['COM%s' % (i + 1) for i in range(256)]
        elif sys.platform.startswith('linux') or sys.platform.startswith('cygwin'):
            # this excludes your current terminal "/dev/tty"
            ports = glob.glob('/dev/tty[A-Za-z]*')
        elif sys.platform.startswith('darwin'):
            ports = glob.glob('/dev/tty.*')
        else:
            raise EnvironmentError('Unsupported platform')

        # This is somewhat crude, but it's the only way I know to check for the 
        # existence of a COMx port on Windows.
        result = []
        for port in ports:
            try:
                s = serial.Serial(port)
                s.close()
                result.append(port)
            except (OSError, serial.SerialException):
                pass

        return result
