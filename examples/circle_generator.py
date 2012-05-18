"""
Measure communication statistics of the machine

Requires these modules:
* pySerial: http://pypi.python.org/pypi/pyserial
"""

# To use this example without installing s3g, we need this hack:
import os, sys
lib_path = os.path.abspath('../')
sys.path.append(lib_path)
lib_path = os.path.abspath('./')
sys.path.append(lib_path)

import s3g
import serial
import time
import optparse
import threading
import signal
import random
import math
import MemsicAccelerometer

parser = optparse.OptionParser()
parser.add_option("-p", "--serialport", dest="serialportname",
                  help="serial port (ex: /dev/ttyUSB0)", default="/dev/ttyACM0")
parser.add_option("-b", "--baud", dest="serialbaud",
                  help="serial port baud rate", default="115200")
parser.add_option("-a", "--accelerometerport", dest="accelerometerportname",
                  help="port that the accelerometer is attached to (ex: /dev/ttyUSB0)", default="/dev/ttyACM0")
(options, args) = parser.parse_args()


class ZagGenerator:
    def __init__(self, radius, divisions, velocity):
        self.radius = radius
        self.divisions = divisions
        self.velocity= velocity

        self.last_target = [0,0,0,0,0]
        self.distance = 0
        self.duration = 0

    def GetNextPoint(self):
        if self.last_target[0] == 0:
            target = [
                -self.radius,
                -self.radius,
                0,
                0,
                0
            ]
        else:
            target = [
                0,
                0,
                0,
                0,
                0
            ]
 
        velocity = self.velocity
        self.last_target = target

        self.distance = self.radius
        self.duration = self.distance*velocity*.000001
   
	return target, velocity

class LineGenerator:
    def __init__(self, radius, divisions, velocity):
        self.radius = radius
        self.divisions = divisions
        self.velocity= velocity

        self.last_target = [0,0,0,0,0]
        self.distance = 0
        self.duration = 0

    def GetNextPoint(self):
        target = [
            self.last_target[0] - self.radius,
            self.last_target[1] - self.radius,
            0,
            0,
            0
        ]
 
        velocity = self.velocity
        self.last_target = target

        self.distance = self.radius
        self.duration = self.distance*velocity*.000001
   
	return target, velocity

class CircleGenerator:
    def __init__(self, radius, divisions, velocity):
        self.angle = 0
        self.radius = radius
        self.divisions = divisions
        self.velocity= velocity

        self.last_target = None

    def GetNextPoint(self):
        target = [
            math.cos(self.angle)*self.radius,
            math.sin(self.angle)*self.radius,
            0,
            0,
            0
        ]
 
        velocity = self.velocity

        if self.last_target != None:
            # distance in steps, velocity in us/step
            distance_x = abs(target[0] - self.last_target[0])
            distance_y = abs(target[1] - self.last_target[1])

            self.distance = math.pow(math.pow(distance_x,2) + math.pow(distance_y,2),.5)

            longest_axis_distance = max(distance_x, distance_y)
            velocity = velocity*self.distance/longest_axis_distance

            self.duration = self.distance*velocity*.000001
            self.duration = longest_axis_distance*velocity*.000001

#            print '%4.4f %4.4f %4.4f %4.4f %4.4f %4.4f'%(
#                self.distance, distance_x, distance_y, longest_axis_distance, velocity,
#                self.duration,
#            )

        self.last_target = target
        self.angle = (self.angle + 2*math.pi/self.divisions)%(math.pi*2)
   
	return target, velocity

r = s3g.s3g()

r.file = serial.Serial(options.serialportname, options.serialbaud, timeout=0)

acc = MemsicAccelerometer.Memsic2125(options.accelerometerportname)
acc.start()

# Test patterns to run
target_position = 13000

test_states = [
#    [rad, div, vel],
#    [1000, 2, 1000],
    [1000, 2, 500],
    [1000, 2, 200],
    [1000, 2, 150],
    [1000, 2, 100],
    [1000, 2, 80],
    [1000, 2, 60],
]

# How long to test each motion, in seconds
test_length = 3

print "commands/sec, velocity, distance, command_length," + \
      " command_count, max_queue_time, min_queue_time, average_queue_time," + \
      " total_distance, total_retries, total_overflows," + \
      " total_time, expected_time" + \
      " min_x_acc, max_x_acc, average_x_acc"


for test_state in test_states:

    r.FindAxesMaximums(['x','y'],500,60)
    r.SetExtendedPosition([3000,3000,0,0,0])
    while not r.IsFinished():
        pass

    generator = ZagGenerator(test_state[0], test_state[1], test_state[2])

    filename = 'divisions_%05i.csv'%test_state[0]
    acc.StartCaptureToFile(filename)

    command_count = 0
    queue_times = []
    r.total_retries = 0
    r.total_overflows = 0
    target = [0,0,0,0,0]

    start_time = time.time()
    for i in range(0, test_state[1]*3):

        target,velocity = generator.GetNextPoint()
 
        try:
            queue_start_time = time.time()
            r.QueueExtendedPoint(target, int(velocity))
            queue_times.append(time.time() - queue_start_time)
 
            command_count += 1
 
        except s3g.TransmissionError as e:
            print 'error moving:', e
 
        except KeyboardInterrupt, SystemExit:
            print 'shutting down'
            r.ToggleAxes(['x','y','z','a','b'],False)
            exit(1)

    while not r.IsFinished():
        pass
    total_time = time.time() - start_time

    acc.StopCaptureToFile()

    max_x_acc = 0
    min_x_acc = 100000
    total_x_acc = 0
    x_acc_count = 0

    max_y_acc = 0
    min_y_acc = 100000
    total_y_acc = 0
    y_acc_count = 0
    with open(filename) as file:
      for line in file:
        x_acc = float(line.split(',')[2])
        y_acc = float(line.split(',')[3])
        
        min_x_acc = min(min_x_acc, x_acc)
        max_x_acc = max(max_x_acc, x_acc)
        total_x_acc += x_acc
        x_acc_count += 1

        min_y_acc = min(min_y_acc, y_acc)
        max_y_acc = max(max_y_acc, y_acc)
        total_y_acc += y_acc
        y_acc_count += 1

    min_time = 1000
    max_time = 0
    queue_total_time = 0
    for queue_time in queue_times:
        min_time = min(min_time, queue_time)
        max_time = max(max_time, queue_time)
        queue_total_time += queue_time

    print "%.2f, %.2f, %.4f, %.4f, %i, %.4f, %.4f, %.4f, %.4f, %i, %i, %.2f, %.2f, %.5f, %.5f, %.5f, %.5f, %.5f, %.5f"%(
        1.0/generator.duration, generator.velocity, generator.distance, generator.duration,
        command_count, max_time, min_time, queue_total_time/command_count,
        generator.distance*command_count, r.total_retries, r.total_overflows,
        total_time, generator.duration*command_count,
        min_x_acc, max_x_acc, total_x_acc/x_acc_count,
        min_y_acc, max_y_acc, total_y_acc/y_acc_count
    )


r.ToggleAxes(['x','y','z','a','b'],False)
exit(1)
