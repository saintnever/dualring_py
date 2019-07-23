import serial
import matplotlib
matplotlib.use('TkAgg') # MUST BE CALLED BEFORE IMPORTING plt
from matplotlib import pyplot as plt
import queue
import threading
import animation
import seaborn as sns
import numpy as np
import time

class ArduinoReader(threading.Thread):
    def __init__(self, stop_event, sig, serport):
        threading.Thread.__init__(self)
        self.stopped = stop_event
        self.signal = sig
        self.pixalarray = [[] for _ in range(8)]
        self.pixalarray0 = [[] for _ in range(8)]
        port = serport
        # self.s = serial.Serial(port, 9600, timeout=1, rtscts=True, dsrdtr=True)
        self.s = serial.Serial(port, 115200, timeout=0.1, rtscts=True, dsrdtr=True)
        if not self.s.isOpen():
            self.s.open()
        print("connected: ", self.s)

    def run(self):
        while not self.stopped.is_set():
            # print(self.s.readline().rstrip())
            try:
                dstr = str(self.s.readline())
                # print(dstr.find('Frame'))
                if dstr.find('Frame') > 0:
                    data_d1 = str(self.s.readline()).split(',')
                    self.pixalarray = [float(x) for x in data_d1[1:-1]]  
                    data_d0 = str(self.s.readline()).split(',')
                    self.pixalarray0 = [float(x) for x in data_d0[1:-1]]
                    if len(self.pixalarray) == 64 and len(self.pixalarray0) == 64:
                        self.signal.put([self.pixalarray, self.pixalarray0])
            except:
                continue
        self.clean()
    
    def get_signal(self):
        return self.signal
        
    def clean(self):
        # self.s.cancel_read()
        while self.s.isOpen():
            self.s.close()
            # print('the serial port is open? {}'.format(self.s.isOpen()))

def colorscale(data, minc, maxc):
    data_scale = 256 * (data - minc) / (maxc - minc)
    if data_scale < 0:
        data_scale = 0
    elif data_scale > 255:
        data_scale = 255
    print(data, data_scale)
    return int(data_scale)

if __name__ == '__main__':
    try:
        q = queue.Queue()
        stop_event = threading.Event()
        data_reader = ArduinoReader(stop_event, q, 'COM3')
        data_reader.start()
        fig, (ax1, ax0) = plt.subplots(1, 2)
        im1 = ax1.imshow(np.random.uniform(low=22, high=32, size=(8, 8)), vmin=22, vmax=32, cmap='jet', interpolation='lanczos')
        im0 = ax0.imshow(np.random.uniform(low=22, high=32, size=(8,8)), vmin = 22, vmax = 32, cmap='jet', interpolation='lanczos')
        plt.tight_layout()
        plt.ion()
        while True:
            [frame1, frame0] = q.get()
            im1.set_array(np.reshape(frame1, (8, 8)))
            im0.set_array(np.reshape(frame0, (8, 8)))
            # plt.draw()
            plt.pause(0.001)
        plt.ioff()
        plt.show()
    finally:
        stop_event.set()
        data_reader.clean()
        data_reader.join()
