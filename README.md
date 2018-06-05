# Security-Door-based-on-raspberry-pi
## About this project
这是《智能硬件设计》这门课的自选作业，要求利用树莓派设计一个有一定简单功能的智能硬件原型。我选择用树莓派构造一个智能门禁，并绘制出3D格式的外壳，通过3D打印机打印出，封装好整个树莓派及相关零件。

该智能门禁通过与访客的语音交互可以让访客选择提供的各种功能，具体实现的操作主要有三：

1.访客选择开门，摄像头会自动拍摄一张照片，对比库中已训练好的人像库，如通过，则开门。

2.访客选择留言，麦克风将自动录制一段语音，将留言播放给访客确认，并选择是否重新录制。

3.（彩蛋）访客选择跟门对话，实现实时的语音或文字/图片交流。

___
## 实现具体功能前的基本操作

访客首先需要唤醒门禁，让门禁开始工作。门禁则需要提醒用户说出自己需要的服务并进行识别。

**具体的逻辑为**：

访客触动门禁——门禁连接的姿态传感器接收到振动——播放welcome.wav(`Security-Door-based-on-raspberry-pi/welcome.wav`)，提醒用户有三种选择——用户给出反馈——对用户的命令做出识别（语音转文字）

**NOTE:**这里会用到**微软的认知服务**，通过调用微软的（[speech-to-text API](https://docs.microsoft.com/en-us/azure/cognitive-services/speech/home)）, 实现对用户发出需求的音频做出识别。

在树莓派上安装录音的必要工具包：
```linux
sudo apt-get update 
sudo apt-get upgrade 
sudo apt-get -y install alsa-utils alsa-tools alsa-tools-gui alsamixergui
```

在树莓派上安装语音识别的库：
```py
pip3 install SpeechRecogniton
```

具体的代码如下：
```py

```
