# Security-Door-based-on-raspberry-pi
## About this project
这是《智能硬件设计》这门课的自选作业，要求利用树莓派设计一个有一定简单功能的智能硬件原型。我选择用树莓派构造一个智能门禁，并绘制出3D格式的外壳，通过3D打印机打印出，封装好整个树莓派及相关零件。

该智能门禁通过与访客的语音交互可以让访客选择提供的各种功能，具体实现的操作主要有三：

1.访客选择开门，摄像头会自动拍摄一张照片，对比库中已训练好的人像库，如通过，则开门。

2.访客选择留言，麦克风将自动录制一段语音，将留言播放给访客确认，并选择是否重新录制。

3.（彩蛋）访客选择跟门对话，实现实时的语音或文字/图片交流。

___
## 实现具体功能前的基本操作
### 训练访客人像图库

首先需要建立一个针对访客的人像库，以便后期门禁将拍摄到的访客图像与库中已有人像做对比以决定是否开门。

**NOTE:** 这里借用了**微软的认知服务**（[自行申请](https://docs.microsoft.com/en-us/azure/cognitive-services/speech/https://azure.microsoft.com/zh-cn/try/cognitive-services/?apiSlug=face-api&country=China&allowContact=true&unauthorized=1)），具体调用的API是[Face verification](https://azure.microsoft.com/en-us/services/cognitive-services/face/)，实现对已有的图像数据进行人脸识别训练。

在树莓派上安装 人脸识别的库：
```
pip3 install cognitive_face
```

开始对一个人像的训练之前，需要拍摄若干张照片并存入`Security-Door-based-on-raspberry-pi/faceRecognition/img/person`目录下，拍照指令为(宽：640px，高：480px）：
```
raspistill -w 640 -h 480 -o 1.jpg
raspistill -w 640 -h 480 -o 2.jpg
raspistill -w 640 -h 480 -o 3.jpg
```
**具体的训练过程如下**（对代码中KEY做了留白，请自行去[官网申请](https://docs.microsoft.com/en-us/azure/cognitive-services/speech/https://azure.microsoft.com/zh-cn/try/cognitive-services/?apiSlug=face-api&country=China&allowContact=true&unauthorized=1)）（`Security-Door-based-on-raspberry-pi/faceRecognition/trainFace.py`）：

**NOTE:** 代码中留白的personGroupId请自行定义一个值，该值是一个只由数字、小写字母、“-”、“_”组成的不超过64个字符长的字符串。只有在训练的时候定义不同的值，才能保证如果有建立多个人的人像库的需求时可以共用一个key。
```py
import json

def GetFileListFromDir(dir):
    l = []
    for p, d, f in os.walk(dir):
        for fname in f:
            l.append(os.path.join(p,fname))
    return l

def CheckGroupIdExistStatus(groupId):
    for info in CF.person_group.lists():
        if info['personGroupId'] == groupId:
            return True
    return False

# set Key
KEY = ""
CF.Key.set(KEY)

# create group and person

personGroupId = "" 
# Valid format should be a string composed 
#by numbers, English letters in lower case,
# '-', '_', and no longer than 64 characters. 

if not CheckGroupIdExistStatus(personGroupId):
    CF.person_group.create(personGroupId,"Description about your group")
user1 = CF.person.create(personGroupId,"Descrption about the person")


# add face
friendImageDir = "img/person"
for fname in GetFileListFromDir(friendImageDir):
    CF.person.add_face(fname, personGroupId, user1['personId'])

# train
CF.person_group.train(personGroupId)


trainingStatus = "running"
while(True):
    trainingStatus = CF.person_group.get_status(personGroupId)
    if trainingStatus['status'] != "running":
        print(trainingStatus)
        break

```

### 访客敲门到门禁对访客的需要求作出反应之前

访客首先需要唤醒门禁，让门禁开始工作。门禁则需要提醒用户说出自己需要的服务并进行识别。

**具体的逻辑为**：

访客触动门禁——门禁连接的姿态传感器接收到振动——播放welcome.wav(`Security-Door-based-on-raspberry-pi/welcome.wav`)，提醒用户有三种选择——开始闪绿灯，提醒访客正在录音，且灯闪频率会随录音终止时间的接近越来越快——访客给出反馈——对访客的命令做出识别（语音转文字）

**NOTE:** 这里依然用到了**微软的认知服务**（[自行申请](https://docs.microsoft.com/en-us/azure/cognitive-services/speech/https://azure.microsoft.com/zh-cn/try/cognitive-services/?apiSlug=face-api&country=China&allowContact=true&unauthorized=1)），通过调用微软的[speech-to-text API](https://docs.microsoft.com/en-us/azure/cognitive-services/speech/home), 实现对用户发出需求的音频做出识别。

在树莓派上安装录音的必要工具包：
```
sudo apt-get update 
sudo apt-get upgrade 
sudo apt-get -y install alsa-utils alsa-tools alsa-tools-gui alsamixergui
```

在树莓派上安装语音识别的库：
```
pip3 install SpeechRecogniton
```

发光二极管（绿灯）接线：长的引脚接作为信号线的BOARD_11，短的引脚接作为地线的BOARD_39。

在树莓派上安装管教操作库：
```
sudo apt-get update
sudo apt-get -y install python-rpi.gpio
```

**具体的执行代码如下**(对代码中speech_key做了留白，请自行去[官网申请](https://docs.microsoft.com/en-us/azure/cognitive-services/speech/https://azure.microsoft.com/zh-cn/try/cognitive-services/?apiSlug=face-api&country=China&allowContact=true&unauthorized=1)）：

**NOTE:** 代码中留白的personGroupId请自行定义一个值，该值是一个只由数字、小写字母、“-”、“_”组成的不超过64个字符长的字符串。只有在训练的时候定义不同的值，才能保证如果有建立多个人的人像库的需求时可以共用一个key。
```py
import RPi.GPIO as GPIO
import os
import speech_recognition as sr
import wave

def light(pin, times, delay1, delay2):
	GPIO.setmode(GPIO.BOARD)
	GPIO.setup(pin,GPIO.OUT)
	onoff = GPIO.LOW
	delay = delay2
	
	i = 0
	while i < times:
		if onoff == GPIO.LOW:
			onoff = GPIO.HIGH
			if delay > 0.12:
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
```

## 开门指令

如果访客选择了“Open the door”指令，摄像头将自动获取一张访客的照片，并判断是否给开门。

**具体的逻辑为**：

分析判断由前面访客的需求音频转换而成的文本中是否含有“Open”这一关键词——如有，则继续；如无，则程序结束——播放photo.wav（`Security-Door-based-on-raspberry-pi/photo.wav`），提醒访客将要拍照——红灯频闪，提醒访客正在拍照倒计时，且灯闪频率会随正式开始拍照时间的接近越来越快——发出“咔擦”一声（`Security-Door-based-on-raspberry-pi/yinxiao.wav`），正式开始拍照——与已经训练好的库中的人像做对比，如果置信度达到70%，则开门（这里抽象为舵机转动一定角度并停下）

**NOTE: **这里继续使用**微软的认知服务**（[自行申请](https://docs.microsoft.com/en-us/azure/cognitive-services/speech/https://azure.microsoft.com/zh-cn/try/cognitive-services/?apiSlug=face-api&country=China&allowContact=true&unauthorized=1)），具体调用的API作为前面训练图像的延续依然是[Face verification](https://azure.microsoft.com/en-us/services/cognitive-services/face/)，对应前面的图像训练过程进行分析检测并得出置信度。

**具体的执行代码如下**(对代码中face_key做了留白，请自行去[官网申请](https://docs.microsoft.com/en-us/azure/cognitive-services/speech/https://azure.microsoft.com/zh-cn/try/cognitive-services/?apiSlug=face-api&country=China&allowContact=true&unauthorized=1)）：

**NOTE:** 代码中留白的personGroupId与前面训练时定义的值需保持相同。
```py
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
```

## 留言指令
如果访客选择了“leave a message”指令，门禁将提醒访客开始留言，稍后播放后将确认访客是否需要重新录制。

**具体的逻辑为**：([]部分为循环)

分析判断由前面访客的需求音频转换而成的文本中是否含有“message”这一关键词——如有，则继续；如无，则程序结束——[*播放leave.wav（`Security-Door-based-on-raspberry-pi/leave.wav`），提醒访客将要拍照——绿灯频闪，提醒访客正在录音——录音结束，提醒访客确认留言（`Security-Door-based-on-raspberry-pi/confirm.wav`）——播放留言音频（`Security-Door-based-on-raspberry-pi/message.wav`）——提醒访客做出选择（`Security-Door-based-on-raspberry-pi/save_or_delete.wav`）——分析判断由访客的选择音频转换而成的文本中是否含有“no”这一关键词——如有，则继续；如无，则告知访客留言已保存（`Security-Door-based-on-raspberry-pi/remindsaved.wav`*]
