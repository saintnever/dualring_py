import serial
import matplotlib
matplotlib.use('TkAgg') # MUST BE CALLED BEFORE IMPORTING plt
from matplotlib import pyplot as plt
import queue
from collections import deque
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
        # calibration
        cal_time = 20
        i = cal_time
        bg1 = [0] * 64
        bg0 = [0] * 64
        while i > 0:
            [frame1, frame0] = q.get()
            bg1 = [frame1[i] + bg1[i] for i in range(64)]
            bg0 = [frame0[i] + bg0[i] for i in range(64)]
            i -= 1
        bg1 = [x / cal_time for x in bg1]
        bg0 = [x / cal_time for x in bg0]

        # start image streaming
        fig, (ax1, ax0) = plt.subplots(1, 2)
        im1 = ax1.imshow(np.random.uniform(low=22, high=32, size=(8, 8)),cmap='jet', vmin = 0, vmax = 8, interpolation='lanczos')
        im0 = ax0.imshow(np.random.uniform(low=22, high=32, size=(8, 8)), cmap='jet', vmin = 0, vmax = 8,interpolation='lanczos')
        plt.tight_layout()
        plt.ion()

        # frame stitching-max
        q_stitch = list()
        while True:
            # for i in range(64):q.get()
            q_stitch.append(q.get())
            if len(q_stitch) == 3:
                frame1_list = [x[0] for x in q_stitch]
                frame0_list = [x[1] for x in q_stitch]
                frame1_max = np.max(np.array(frame1_list),axis=0)
                frame0_max = np.max(np.array(frame0_list),axis=0)
                frame1_cal = frame1_max - np.array(bg1)
                ind1 = frame1_cal < 0
                frame1_cal[ind1] = 0
                frame0_cal = frame0_max - np.array(bg0)
                ind0 = frame0_cal < 0
                frame0_cal[ind0] = 0
                im1.set_array(np.reshape(frame1_cal, (8, 8)))
                im0.set_array(np.reshape(frame0_cal, (8, 8)))
                # plt.draw()
                plt.pause(0.001)
                q_stitch.pop(0)
            # for i in range(64):
            #     frame1[i] -= bg1[i]
            #     if frame1[i] < 0:
            #         frame1[i] = 0
            #     frame0[i] -= bg0[i]
            #     if frame0[i] < 0:
            #         frame0[i] = 0
            # # print(frame1_cal)
            # im1.set_array(np.reshape(frame1, (8, 8)))
            # im0.set_array(np.reshape(frame0, (8, 8)))
            # # plt.draw()
            # plt.pause(0.001)
        plt.ioff()
        plt.show()
    finally:
        stop_event.set()
        data_reader.clean()
        data_reader.join()
