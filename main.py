#encoding: utf-8
#!/usr/bin/env python
#This is a demo for security door. For more details, you can consult readme.docx

import os
import speech_recognition as sr
import wave
import time
import cognitive_face as CF
import itchat
import sys
from itchat.content import *
from PIL import Image
import threading
import RPi.GPIO as GPIO
import struct
import sys
import pigpio


def send_message(message, userId):
	itchat.send(message, toUserName = userId)

def send_picture(userId):
	print("I will take a photo and send it to ice:")
	os.system("sudo raspistill -o try.jpg")
	file = "try.jpg"
	itchat.send_image(file, toUserName = userId)

def xiaoice(iceId):
	#make dirs for downloading pictures and recordings
	if not os.path.exists('./picture'): 
		os.mkdir('./picture')

	if not os.path.exists('./recording'):
		os.mkdir('./recording')

	@itchat.msg_register([TEXT,PICTURE,RECORDING], isMpChat=True)
	def xiaobing(msg):
		#if xiao ice send two message at once, deal it with queue
		if msg['Type'] == 'Text': #if xiaoice send a short message, put it into the queue
			print("小冰：" + msg['Text']) 

		if msg['Type'] == 'Picture':
			fileName = './picture/' + msg['FileName']
			with open(fileName, 'wb') as f: #download file
				f.write(msg['Text']())
			print("小冰发了一张图：")
			image = Image.open(fileName) #show this picture
			image.show()

		if msg['Type'] == 'Recording':
			fileName = './recording/' + msg['FileName']
			with open(fileName, 'wb') as f: # download file
				f.write(msg['Text']())
			print("小冰说了一句话")
			os.system('mplayer '+ fileName) # play this audio
			
		del msg 
	itchat.run()

#pin: the GPIO pin you choose
#times: times to blink
#delay: duration between blinking
def light(pin, times, delay1, delay2):
	GPIO.setmode(GPIO.BOARD)
	GPIO.setup(pin,GPIO.OUT)
	onoff = GPIO.LOW
	delay = delay2
	
	i = 0
	while i < times:
		if onoff == GPIO.LOW:
			onoff = GPIO.HIGH
			if delay1 > 0.12:
                                delay1 -= 0.11
			delay = delay1
			i += 1
		else:
			onoff = GPIO.LOW
			delay = delay2
		GPIO.output(pin, onoff)
		time.sleep(delay)
		
		
	GPIO.output(pin, GPIO.LOW)

#if x^2 + y^2 + z^2 > threshold
#somebody knock the door
def knock(threshold):
	global buffer
	if sys.version > '3':
		buffer = memoryview
	BUS = 1
	ADXL345_I2C_ADDR = 0x53
	pi = pigpio.pi() # open local Pi
	h = pi.i2c_open(BUS, ADXL345_I2C_ADDR)
	if h >= 0: # Connected OK?
		# Initialise ADXL345.
		pi.i2c_write_byte_data(h, 0x2d, 0)  # POWER_CTL reset.
		pi.i2c_write_byte_data(h, 0x2d, 8)  # POWER_CTL measure.
		pi.i2c_write_byte_data(h, 0x31, 0)  # DATA_FORMAT reset.
		pi.i2c_write_byte_data(h, 0x31, 11) # DATA_FORMAT full res +/- 16g.
		read = 0
	#get initial pos
	(s, b) = pi.i2c_read_i2c_block_data(h, 0x32, 6)
	if s >= 0:
		(init_x,init_y,init_z) = struct.unpack('<3h', buffer(b))
	#loop until someone move the sensor
	while 1:
		(s, b) = pi.i2c_read_i2c_block_data(h, 0x32, 6)
		if s >= 0:
			(x,y,z) = struct.unpack('<3h', buffer(b))
		if (init_x - x)**2 + (init_y - y) ** 2 + (init_z - z) ** 2 >= threshold:
			break
		time.sleep(0.01)

#control the steering gear
def open_door():
            GPIO.setup(12,GPIO.OUT)
            p = GPIO.PWM(12,50)
            p.start(0)
            global onoff,dc, dir
            onoff = GPIO.LOW
            dc = 10
            dir = 5
            for i in range(23):
                    dc += 5
                    p.ChangeDutyCycle( dc/10 )
                    time.sleep(0.1)
                    
                   
        


# Start from here.......
knock(1000)

print("Welcome to our security door!")
os.system('aplay welcome.wav')
print("You have three choose:")
print("		1. Open the door")
print("		2. Talk with the door")
print("		3. Leave a message")
os.system('aplay choice.wav')

os.system('arecord --device=plughw:1,0 --format S16_LE --rate 16000 -d 5 -c1 oneOrTwo.wav&')#record one or two
#Countdown
light(11, 15, 1.11, 0.1)
audioFile = "oneOrTwo.wav"

#analysis your recording
r = sr.Recognizer()
with sr.AudioFile(audioFile) as source:
	audio = r.record(source) 

speech_key = ""  

try:
    speech_result = r.recognize_bing(audio, key=speech_key)
    print(speech_result.encode("utf-8"))
except sr.UnknownValueError:
    print("Microsoft Bing Voice Recognition could not understand audio")
except sr.RequestError as e:
	print("Could not request results from Microsoft Bing Voice Recognition service; {0}".format(e))

if "open" in speech_result or "Open" in speech_result:
	#Verify your face
	face_key = ""
	CF.Key.set(face_key)
	personGroupId = ""
	#Try to take a photo for you
	print("I will take a photo for you, please look at the camera:")
	os.system('aplay photo.wav')
	light(13, 6, 0.56, 0.1)
	os.system('sudo raspistill -o face_recognition.jpg -w 640 -h 480')
	os.system('aplay yinxiao.wav')
	testImageFile = "face_recognition.jpg"
	faces = CF.face.detect(testImageFile)

	if len(faces) != 1:
		print("There is no face or more than one face in your photo!")

	else:
		faceIds = [faces[0]['faceId']]
		res = CF.face.identify(faceIds, personGroupId)

		candidate = res[0]['candidates']
		if candidate == []:
			print("No candidates!")
		else:
			confidence = candidate[0]['confidence']
			print("Confidence： " + str(confidence))
			if confidence >= 0.7:
				print("Accept!")
				open_door()
			else:
				print("Permission Denied!")

if "talk" in speech_result or "Talk" in speech_result:
	itchat.auto_login(enableCmdQR = 2, hotReload = True) #Login
	
	iceId = itchat.search_mps(name = "小冰")[0]['UserName']# get xiaoice's ID
	t = threading.Thread(target=xiaoice, args=(iceId,))
	t.start()
	while 1:
		line = sys.stdin.readline().strip()
		if line != "":
			if line == "send picture":
				send_picture(iceId)
			else:
				send_message(line, iceId)
		else:
			break
		    
if "message" in speech_result or "Message" in speech_result:
    print("I will take a record for you, please leave a message right now")
    os.system('aplay leave.wav')
    os.system('arecord --device=plughw:1,0 --format S16_LE --rate 16000 -d 5 -c1 message.wav&')#record one or two
    light(11, 15, 1.11, 0.1)
    print("please confirm your message")
    os.system('aplay confirm.wav')
    os.system('aplay message.wav')
    print("say yes to save the message or no to record again")
    os.system('aplay save_or_delete.wav')
    os.system('arecord --device=plughw:1,0 --format S16_LE --rate 16000 -d 5 -c1 decide.wav&')#record one or two
    light(11, 15, 1.11, 0.1)
    audioFile = "decide.wav"

    #analysis your recording
    r = sr.Recognizer()
    with sr.AudioFile(audioFile) as source:
            audio = r.record(source) 

    speech_key = ""  

    try:
        confirm_result = r.recognize_bing(audio, key=speech_key)
        print(confirm_result.encode("utf-8"))
    except sr.UnknownValueError:
        print("Microsoft Bing Voice Recognition could not understand audio")
    except sr.RequestError as e:
            print("Could not request results from Microsoft Bing Voice Recognition service; {0}".format(e))
    while "no" in confirm_result or "No" in confirm_result:
        print("I will take a record for you, please leave a message right now")
        os.system('aplay leave.wav')
        os.system('arecord --device=plughw:1,0 --format S16_LE --rate 16000 -d 5 -c1 message.wav&')#record one or two
        light(11, 15, 1.11, 0.1)
        print("please confirm your message")
        os.system('aplay confirm.wav')
        os.system('aplay message.wav')
        print("say yes to save your message or no to record again")
        os.system('aplay save_or_delete.wav')
        os.system('arecord --device=plughw:1,0 --format S16_LE --rate 16000 -d 5 -c1 decide.wav&')#record one or two
        light(11, 15, 1.11, 0.1)
        audioFile = "decide.wav"

        #analysis your recording
        r = sr.Recognizer()
        with sr.AudioFile(audioFile) as source:
                audio = r.record(source) 

        speech_key = ""  

        try:
            confirm_result = r.recognize_bing(audio, key=speech_key)
            print(confirm_result.encode("utf-8"))
        except sr.UnknownValueError:
            print("Microsoft Bing Voice Recognition could not understand audio")
        except sr.RequestError as e:
                print("Could not request results from Microsoft Bing Voice Recognition service; {0}".format(e))
    print("record has been successfully saved!")
    os.system('aplay remindsaved.wav')
       
        


    
        
    