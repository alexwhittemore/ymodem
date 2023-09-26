import logging
import math
import os
import serial
import sys
import time
import subprocess
import random
random.seed()

from ymodem.Protocol import ProtocolType
from ymodem.Socket import ModemSocket

class TaskProgressBar:
    def __init__(self):
        self.bar_width = 50
        self.last_task_name = ""
        self.current_task_start_time = -1

    def show(self, task_index, task_name, total, success):
        if task_name != self.last_task_name:
            self.current_task_start_time = time.perf_counter()
            if self.last_task_name != "":
                print('\n', end="")
            self.last_task_name = task_name

        success_width = math.ceil(success * self.bar_width / total)

        a = "#" * success_width
        b = "." * (self.bar_width - success_width)
        progress = (success_width / self.bar_width) * 100
        cost = time.perf_counter() - self.current_task_start_time

        print(f"\r{task_index} - {task_name} {progress:.2f}% [{a}->{b}]{cost:.2f}s", end="")

if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG, format='%(asctime)s %(message)s')
    log = logging.getLogger('__main__')
    # logging.basicConfig(level=logging.INFO, format='%(message)s')
    
    serial_io = serial.Serial()
    serial_io.port = "/dev/ttyAMA0"
    serial_io.baudrate = "2000000"
    serial_io.parity = "N"
    serial_io.bytesize = 8
    serial_io.stopbits = 1
    serial_io.timeout = 2

    try:
        subprocess.run(["sudo", "systemctl", "stop", "serial-getty@ttyAMA0"])
        subprocess.run(["sudo", "chmod", "666", "/dev/ttyAMA0"])
        serial_io.open()
        serial_io.flush()
    except Exception as e:
        raise Exception("Failed to open serial port!")

    # Create up to 5 failures with a 1-in-100 chance on any read.
    failcount = 0
    def read(size, timeout = 10):
        global failcount
        serial_io.timeout = timeout
        if failcount<0 and random.randint(0,100) == 5:
            failcount +=1
            data_in = serial_io.read(size)
            data = bytearray(data_in)
            data[0] = ord('0')
            log.debug(f"Munched data on {size} byte read, failcount {failcount}, {data_in} to {bytes(data)}")
            return bytes(data)
        else:
            return serial_io.read(size)

    def write(data, timeout = 10):
        serial_io.write_timeout = timeout
        serial_io.write(data)
        serial_io.flush()
        return
    
    receiver = ModemSocket(read, write, ProtocolType.YMODEM, )
    # receiver = ModemSocket(read, write, ProtocolType.YMODEM, ['g'])

    os.chdir(sys.path[0])
    folder_path = os.path.abspath("remote")
    progress_bar = TaskProgressBar()
    received = receiver.recv(folder_path, progress_bar.show)

    print(f"Failcount: {failcount}")
    serial_io.close()
    subprocess.run(["sudo", "systemctl", "start", "serial-getty@ttyAMA0"])
