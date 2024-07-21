import socket
import sys
import struct
import numpy as np
import threading
import select
import queue
import matplotlib.pyplot as plt
from PyQt5.QtCore import QCoreApplication, QObject, pyqtSignal
from PyQt5.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas

desired_op_format = input('Enter the desired output format:')
buffer = int(input('Enter the buffer:'))

class PlotThread(threading.Thread):
    def __init__(self, data_queue, signal_exit):
        super(PlotThread, self).__init__()
        self.data_queue = data_queue
        self.signal_exit = signal_exit
        self.figure, ((self.ax1, self.ax2), (self.ax3, self.ax4)) = plt.subplots(2, 2, sharex=True)
        self.canvas = FigureCanvas(self.figure)
        self.partial_data = b''  # It is Buffer to hold partial data from previous iterations
        self.scaling_factors = [0.00549, 0.00549, 0.043945312, 0.001904762]

    def run(self):
        command1_data = np.array([], dtype=np.int16)
        incremental1_data = np.array([], dtype=np.int16)
        absolute1_data = np.array([], dtype=np.int16)
        current1_data = np.array([], dtype=np.int16)
        
        command2_data = np.array([], dtype=np.int16)
        incremental2_data = np.array([], dtype=np.int16)
        absolute2_data = np.array([], dtype=np.int16)
        current2_data = np.array([], dtype=np.int16)
        
        command3_data = np.array([], dtype=np.int16)
        incremental3_data = np.array([], dtype=np.int16)
        absolute3_data = np.array([], dtype=np.int16)
        current3_data = np.array([], dtype=np.int16)
        
        command4_data = np.array([], dtype=np.int16)
        incremental4_data = np.array([], dtype=np.int16)
        absolute4_data = np.array([], dtype=np.int16)
        current4_data = np.array([], dtype=np.int16)
        
        while True:
            data = self.data_queue.get()
            if data is None:
                break

            # Combine partial data from the previous iteration, if any
            full_data = self.partial_data + data
            values = struct.unpack(desired_op_format, full_data)

            # Append the extracted values to the corresponding arrays
            command1_data = np.append(command1_data, (values[10]*self.scaling_factors[0]))
            incremental1_data = np.append(incremental1_data, (values[14]*self.scaling_factors[1]))
            absolute1_data = np.append(absolute1_data, (values[18]*self.scaling_factors[2]))
            current1_data = np.append(current1_data, (values[30]*self.scaling_factors[3]))
            
            command2_data = np.append(command2_data, (values[11]*self.scaling_factors[0]))
            incremental2_data = np.append(incremental2_data, (values[15]*self.scaling_factors[1]))
            absolute2_data = np.append(absolute2_data, (values[19]*self.scaling_factors[2]))
            current2_data = np.append(current2_data, (values[31]*self.scaling_factors[3]))
            
            command3_data = np.append(command3_data, (values[12]*self.scaling_factors[0]))
            incremental3_data = np.append(incremental3_data, (values[16]*self.scaling_factors[1]))
            absolute3_data = np.append(absolute3_data, (values[20]*self.scaling_factors[2]))
            current3_data = np.append(current3_data, (values[32]*self.scaling_factors[3]))
            
            command4_data = np.append(command4_data, (values[13]*self.scaling_factors[0]))
            incremental4_data = np.append(incremental4_data, (values[17]*self.scaling_factors[1]))
            absolute4_data = np.append(absolute4_data, (values[21]*self.scaling_factors[2]))
            current4_data = np.append(current4_data, (values[33]*self.scaling_factors[3]))

            # Remove the processed part from the data
            full_data = full_data[buffer:]

            # Store any remaining partial data for the next iteration
            self.partial_data = full_data

            # Update the plots with the corresponding data for each actuator
            self.ax1.clear()
            self.ax1.plot(command1_data, label='command')
            self.ax1.plot(incremental1_data, label='incremental')
            self.ax1.plot(absolute1_data, label='absolute')
            self.ax1.plot(current1_data, label='current')
            self.ax1.set_xlabel("Time")
            self.ax1.set_ylabel("Actuator 1 in degrees")
            self.ax1.legend()

            self.ax2.clear()
            self.ax2.plot(command2_data, label='command')
            self.ax2.plot(incremental2_data, label='incremental')
            self.ax2.plot(absolute2_data, label='absolute')
            self.ax2.plot(current2_data, label='current')
            self.ax2.set_xlabel("Time")
            self.ax2.set_ylabel("Actuator 2 in degrees")
            self.ax2.legend()

            self.ax3.clear()
            self.ax3.plot(command3_data, label='command')
            self.ax3.plot(incremental3_data, label='incremental')
            self.ax3.plot(absolute3_data, label='absolute')
            self.ax3.plot(current3_data, label='current')
            self.ax3.set_xlabel("Time")
            self.ax3.set_ylabel("Actuator 3 in degrees")
            self.ax3.legend()

            self.ax4.clear()
            self.ax4.plot(command4_data, label='command')
            self.ax4.plot(incremental4_data, label='incremental')
            self.ax4.plot(absolute4_data, label='absolute')
            self.ax4.plot(current4_data, label='current')
            self.ax4.set_xlabel("Time")
            self.ax4.set_ylabel("Actuator 4 in degrees")
            self.ax4.legend()

            self.canvas.draw()

    def stop(self):
        self.signal_exit.emit()  # Emit the signal to exit the application

class Client(QMainWindow):
    def __init__(self):
        super(Client, self).__init__()

        self.data_queue = queue.Queue()
        self.signal_exit = pyqtSignal()  # Define the signal here
        self.plot_thread = PlotThread(self.data_queue, self.signal_exit)
        self.plot_thread.start()

        self.initUI()
        self.connect_to_server()

    def initUI(self):
        central_widget = QWidget()
        layout = QVBoxLayout(central_widget)
        layout.addWidget(self.plot_thread.canvas)
        self.setCentralWidget(central_widget)

        self.setGeometry(100, 100, 800, 600)
        self.setWindowTitle('Binary File Plotter')
        self.show()

    def connect_to_server(self):
        host = '127.0.0.1'
        port = 12345

        client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        try:
            client_socket.connect((host, port))

            while True:
                # Use select to check if there is data available to read
                rlist, _, _ = select.select([client_socket], [], [], 1.0)
                if client_socket in rlist:
                    data = client_socket.recv(buffer)
                    if not data:
                        break
                    self.data_queue.put(data)
                else:
                    # Timeout, no data available to read, continue waiting
                    continue

            self.data_queue.put(None)  # Signal the plot thread to stop
            client_socket.close()

        except Exception as e:
            print("Error:", e)
            sys.exit()

if __name__ == '__main__':
   
    app = QApplication(sys.argv)
    client = Client()
    sys.exit(app.exec_())
