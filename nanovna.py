import serial
import logging


class Nanovna:

    ser = None
    port = None

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
                logging.info("Connection is good")
            except Exception as ex:
                logging.error("Unable to open connection", exc_info=True)
                self.ser = None

            if self.ser is None:
                raise Exception("Unable to connect to NanoVNA")
        else:
            pass

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

    def run_command(self, command):
        """
        :param ser: The serial port that is connected (an open) to the NanoVNA
        :param command: The command to send
        :return: An array of strings, one for each line returned by the command
        """
        if self.ser is None:
            raise Exception("Not connected")
        logging.info("NanoVNA command: " + command)
        try:
            self.ser.write((command + "\r").encode("utf-8"))
            lines = self.read_response_as_lines()
        except Exception as ex:
            self.ser = None
            raise ex
        # We discard the first line because that is the echo of the command
        return lines[1:]

    def get_complex_data(self):
        lines = self.run_command("data")
        # Parse into real/imaginary tokens
        tokenized_lines = [line.split(" ") for line in lines]
        # Make into imaginary numbers
        return [complex(float(token[0]), float(token[1])) for token in tokenized_lines]

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