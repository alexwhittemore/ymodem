import os
import logging
import math
import os
import serial
import sys
import time

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
    # logging.basicConfig(level=logging.INFO, format='%(message)s')

    serial_io = serial.Serial()
    serial_io.port = "COM6"
    serial_io.baudrate = "2000000"
    serial_io.parity = "N"
    serial_io.bytesize = 8
    serial_io.stopbits = 1
    serial_io.timeout = 2

    try:
        serial_io.open()
        serial_io.flush()
    except Exception as e:
        raise Exception("Failed to open serial port!")
    
    def read(size, timeout = 10):
        serial_io.timeout = timeout
        return serial_io.read(size)

    txcount = 0
    def write(data, timeout = 10):
        global txcount
        serial_io.write_timeout = timeout
        # txcount += 1
        if txcount == 300:
            data = bytearray(data)
            data[0] = 0
            data = bytes(data)
        serial_io.write(data)
        serial_io.flush()
        return

    sender = ModemSocket(read, write, ProtocolType.YMODEM)
    # sender = ModemSocket(read, write, ProtocolType.YMODEM, ['g'])

    os.chdir(sys.path[0])
    file_path1 = os.path.abspath('local/sample.stl')
    file_path2 = os.path.abspath('local/sample2.stl')
    file_path3 = os.path.abspath('local/sample3.stl')
    progress_bar = TaskProgressBar()
    sender.send([file_path1, file_path2, file_path3], progress_bar.show)
    # sender.send([file_path1], progress_bar.show)

    serial_io.close()
