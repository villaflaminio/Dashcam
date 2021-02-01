import picamera
import os
import psutil
import serial
import pynmea2
import time
from picamera import Color
import httplib
import urllib
import time
from datetime import datetime
import logging

key = 'XXXXXXXThingspeakKEYXXXXXXXX'  # Thingspeak channel to update

MAX_FILES = 50
DURATION = 20
SPACE_LIMIT = 100
TIME_STATUS_OK = 0.5

file_root = "/home/pi/Videos/"
port = "/dev/serial0"

logging.basicConfig(filename='all.log',level=logging.DEBUG)

def thingSpeak(speed):
    while True:
        #Calculate CPU temperature of Raspberry Pi in Degrees C
        params = urllib.urlencode({'field1': speed,'field2': speed, 'key':key }) 
        headers = {"Content-typZZe": "application/x-www-form-urlencoded","Accept": "text/plain"}
        conn = httplib.HTTPConnection("api.thingspeak.com:80")
        try:
            conn.request("POST", "/update", params, headers)
            response = conn.getresponse()            
            data = response.read()
            conn.close()
        except:
            logging.warning(str(datetime.now())+'connection failed')

            print ("connection failed")
        break
    
def measure_temp():
        temp = os.popen("vcgencmd measure_temp").readline()
        return str(temp.replace("temp=",""))

def writeLog(entry, filename):        
    csv = open(filename, 'a')
    try:
        csv.write(entry)
    finally:
        csv.close()
        
def parseGPS(data, file_name_log):
#    print "raw:", data #prints raw data
    if data[0:6] == "$GPRMC":
        sdata = data.split(",")
        if sdata[2] == 'V':
            print "no satellite data available"
            logging.debug(str(datetime.now())+'no satellite data available')

            return
        ora=( int(sdata[1][0:2]) +2)
        time = str(ora) + ":" + sdata[1][2:4] + ":" + sdata[1][4:6]
        
        lat_float = decode(float(sdata[3])) #latitude
        lat = str(lat_float)
        dirLat = sdata[4]      #latitude direction N/S
        lon_float = decode( float(sdata[5])) #longitute
        lon= str(lon_float)
        dirLon = sdata[6]      #longitude direction E/W
        speed_int = (float(sdata[7])* 1.852 )      #Speed in km/h
        speed = str(speed_int)
        trCourse = sdata[8]    #True course
        date = sdata[9][0:2] + "/" + sdata[9][2:4] + "/" + sdata[9][4:6]#date
            
        entry = date + " , "+ time+" , "+ lat +" , "+  lon +" , "+ speed+" , "+ str(psutil.cpu_percent()) +" , "+ measure_temp()+ "\n" 
        thingSpeak(speed)
        writeLog(entry, file_name_log)
        camera.annotate_background = Color('black')
        camera.annotate_text = "Date : %s, time : %s, latitude : %s(%s), longitude : %s(%s),speed : %s, CPU : %s, Temp : %s  " %  (date,time,lat,dirLat,lon,dirLon,speed, str(psutil.cpu_percent()),str(measure_temp()))
			 
def decode(raw_value):
    decimal_value = raw_value/100.00
    degrees = int(decimal_value)
    mm_mmmm = (decimal_value - int(decimal_value))/0.6
    position = degrees + mm_mmmm
    position = "%.4f" %(position)
    return position
    
if(psutil.disk_usage(".").percent > SPACE_LIMIT):
	print('WARNING: Low space!')
	logging.warning(str(datetime.now())+'WARNING: Low space!')
	exit()
	
with picamera.PiCamera() as camera:
	camera.resolution = (1920,1080)
	camera.framerate = 30
        camera.exposure_mode = 'auto'
        camera.sharpness = 0
        camera.contrast = 0
        camera.brightness = 60
        camera.saturation = 0
        camera.ISO = 10
        camera.video_stabilization = True
        camera.exposure_compensation = 0
        camera.exposure_mode = 'auto'
        camera.meter_mode = 'average'
        camera.awb_mode = 'auto'
        camera.image_effect = 'none'
        camera.color_effects = None
        camera.rotation = 90
        camera.hflip = False
        camera.vflip = False
        camera.crop = (0.0, 0.0, 1.0, 1.0)

	print('Searching files...')
	logging.info('Searching files...')

	while(1):
                        
            for i in range(1, MAX_FILES):
                    file_number = i
                    
                    
                    file_name = file_root  + " video" + str(i).zfill(3) + ".h264"
                    
                    exists = os.path.isfile(file_name)
                    if not exists:
                            print "Search complete"
                            logging.info(str(datetime.now())+'Search complete')

                            break
                        
            if i == MAX_FILES-1:
                i = 1
                file_number=1
                
                for file_name in camera.record_sequence(file_root +" video%03d.h264" % i for i in range(file_number, MAX_FILES)):
                    
                        timeout = time.time() + DURATION
                        logging.info(str(datetime.now())+'Recording to %s' % file_name)

                        print('Recording to %s' % file_name)
                        file_name_log = file_name + ".csv"

                        csv = open(file_name_log, 'w')
                        try:
                            csv.write("date,time,lat,lon ,speed,cpu , temp \n")
                        finally:
                            csv.close()
                        while(time.time() < timeout):
                                ser = serial.Serial(port, baudrate = 9600, timeout = 0.5)
                                data = ser.readline()
                                parseGPS(data, file_name_log)
                                        
                                time.sleep(TIME_STATUS_OK)
                                if(psutil.disk_usage(".").percent > SPACE_LIMIT):
                                        print('WARNING: Low space!')
                                       	logging.warning('WARNING: Low space!')
 
                                        break;
                                    
        
            if( i < MAX_FILES):
                for file_name in camera.record_sequence(file_root +" video%03d.h264" % i for i in range(file_number, MAX_FILES)):
                    logging.info(str(datetime.now())+'Recording to %s' % file_name)

                    print('Recording to %s' % file_name)
                    file_name_log = file_name + ".csv"
                    
                    timeout = time.time() + DURATION
                    csv = open(file_name_log, 'w')
                    try:
                        csv.write("date,time,lat,lon ,speed,cpu , temp \n")
                    finally:
                        csv.close()
                        
                    while(time.time() < timeout):
                            ser = serial.Serial(port, baudrate = 9600, timeout = 0.5)
                            data = ser.readline()
                            parseGPS(data, file_name_log)
                                    
                            time.sleep(TIME_STATUS_OK)
                            if(psutil.disk_usage(".").percent > SPACE_LIMIT):
                                    print('WARNING: Low space!')
                                    logging.warning('WARNING: Low space!')

                                    break;
        
                    
                
                                    
            
            
            
              
