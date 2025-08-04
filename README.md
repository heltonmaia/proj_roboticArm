# Hybrid Control for Robotic Arms: Combining Gesture Recognition and Voice Commands

This project encompasses computer vision, machine learning, 3D printing, and Arduino integration, with the primary goal of enabling robotic arms to replicate the movements of a human arm. The project consists of a PyQt6 application where the user can choose to control the robotic arm either through manual gestures, automatic gestures or voice commands. If the user prefers gesture controls, the application will use the OpenCV computer vision library to capture real-time images using a webcam or smartphone, and relevant information from the user's hand will then be detected by one of our neural networks trained based on the YOLOv11 architecture. However, if the user prefers voice command control, the application will use Google's Gemini 2.0 Flash model, the speech_recognition library and the pyaudio library to record and process the user's voice commands. Regardless of the control method, the movement of the robotic arm, which was 3D-printed, is executed by the Arduino according to serial port commands sent by the program.

[Project video](https://github.com/heltonmaia/ECT-proj-roboticArm/assets/4681481/2796c126-4182-4c66-be8b-e16110343908)

# How to use
### **Requirements**
  - Windows 10 or 11
  - Webcam or a smartphone
  - An Arduino board
  - Arduino IDE

### **Downloading the Robotic Arm Control program**

Access <a href="https://github.com/heltonmaia/proj_roboticArm/releases/" target="_blank">our releases</a> and download the latest one available.

### **Accessing the camera and the microphone**
If you don't have a webcam, you can use the Droidcam app on a smartphone to use the phone's camera as a webcam

  - Install the Droidcam app (Android or IOS): <a href="https://www.dev47apps.com" target="_blank">Download Page</a>
  - Install the Droidcam client on Windows: <a href="https://www.dev47apps.com/droidcam/windows/" target="_blank">Download Page</a>
  - Then follow the instructions to connect: <a href="https://www.dev47apps.com/droidcam/connect/" target="_blank">Connection Guide</a>


### **Installing and configuring the Arduino IDE**
Follow <a href="https://docs.arduino.cc/software/ide-v2/tutorials/getting-started/ide-v2-downloading-and-installing/" target="_blank">this guide</a> to install the Arduino IDE.

Once you installed the Arduino IDE, you can download the zip file of the VarSpeedServo library available <a href="https://github.com/netlabtoolkit/VarSpeedServo" target="_blank">here</a> and install it by following <a href="https://docs.arduino.cc/software/ide-v1/tutorials/installing-libraries" target="_blank">this guide</a>.
Now use the file "serial-port-command-receiver.cpp" in the Arduino IDE.

### **Assembling the circuit**
The following circuit was simulated using the <a href="https://wokwi.com/" target="_blank">Wokwi</a> online platform, and considering that the four servomotors are already fitted to the robotic arm, the circuit in this image bellow must be physically assembled.

<p align="center"><img src="https://github.com/heltonmaia/ECT-proj-roboticArm/blob/main/images/wokwi.PNG?raw=true" style="width: 600px; height: 420px;"></p>

If you want to save time, use our pin configuration as shown in the circuit:

    Gripper -> Pin 2
    Lower Arm -> Pin 3
    Upper Arm -> Pin 4
    Rotating Base -> Pin 5

If you want to change the pins, just make sure the digital pins on the Arduino board receiving the signal jumpers from the servomotors are constant values specified in the file "serial-port-command-receiver.cpp" as "#define something_pin".

For example, if the servomotor that controls the robotic arm's gripper is connected to digital pin 2 on the Arduino board, the definition in the code should be "#define gripper_pin 2".

Select the right serial port within the IDE, compile and send the code to the board.

### **Using the App**

#### **Choosing a control method**
<h5 align="center"><b>1 - Select "Setup"</b></h5>
<p align="center"><img src="https://github.com/heltonmaia/proj_roboticArm/blob/main/images/app/setup_selection.png" style="width: 600px; height: 420px;"></p>

<h5 align="center"><b>2 - Select, for example, "Automatic gestures"</b></h5>
<p align="center"><img src="https://github.com/heltonmaia/proj_roboticArm/blob/main/images/app/automatic_gestures_selection_0.png" style="width: 600px; height: 420px;"></p>
<p align="center"><img src="https://github.com/heltonmaia/proj_roboticArm/blob/main/images/app/automatic_gestures_selection_1.png" style="width: 600px; height: 420px;"></p>

<h5 align="center"><b>3 - Select "Save"</b></h5>
<p align="center"><img src="https://github.com/heltonmaia/proj_roboticArm/blob/main/images/app/automatic_gestures_selection_2.png" style="width: 600px; height: 420px;"></p>

Note that the Voice control method uses Google's Gemini 2.0 Flash model, and it needs an API key, which you can get <a href="https://aistudio.google.com/app/apikey" target="_blank">here</a>. You will need to login with your google account in order to get the API key.

Now just copy and paste the API key to its place in the configuration window:
<p align="center"><img src="https://github.com/heltonmaia/proj_roboticArm/blob/main/images/app/api_key.png" style="width: 600px; height: 420px;"></p>

#### **Selecting the right COM port**
Check the COM port that your Arduino board is using inside the IDE and put the same value in "COM Port". The default value is 3.
<p align="center"><img src="https://github.com/heltonmaia/proj_roboticArm/blob/main/images/app/com_port_selection.png" style="width: 600px; height: 420px;"></p>

#### **Selecting the right capture device**
The default capture device index is 0, if it does not work, try 1, 2, etc.
<p align="center"><img src="https://github.com/heltonmaia/proj_roboticArm/blob/main/images/app/capture_device_selection.png" style="width: 600px; height: 420px;"></p>

**Don't forget to save before closing the Setup window**

#### **Running the app**
Now with the app configured, just select "Start":
<p align="center"><img src="https://github.com/heltonmaia/proj_roboticArm/blob/main/images/app/start_selection.png" style="width: 600px; height: 420px;"></p>

# Examples

### **Manual Gestures**

The following images are examples that show what approximate positions the hand must be in for detections to be made correctly with this method.

<h3 align="center"><b>Open hand</b></h3>
<p align="center"><img src="https://github.com/heltonmaia/ECT-proj-roboticArm/blob/main/images/open%20hand.png?raw=true" style="width: 600px; height: 420px;"></p>

<h3 align="center"><b>Closed hand</b></h3>
<p align="center"><img src="https://github.com/heltonmaia/ECT-proj-roboticArm/blob/main/images/closed%20hand.png?raw=true" style="width: 600px; height: 420px;"></p>

### **Automatic Gestures**

The following images are examples that show what approximate positions the hand must be in for detections to be made correctly with this method.

<h3 align="center"><b>"Start" command</b></h3>
<p align="center"><img src="https://github.com/heltonmaia/ECT-proj-roboticArm/blob/main/images/start%20example.png?raw=true" style="width: 600px; height: 420px;"></p>

<h3 align="center"><b>"Search" command</b></h3>
<p align="center"><img src="https://github.com/heltonmaia/ECT-proj-roboticArm/blob/main/images/search%20example.png?raw=true" style="width: 600px; height: 420px;"></p>

<h3 align="center"><b>"Grab" command </b></h3>
<p align="center"><img src="https://github.com/heltonmaia/ECT-proj-roboticArm/blob/main/images/grab%20example.png?raw=true" style="width: 600px; height: 420px;"></p>

<h3 align="center"><b>"Stop" command</b></h3>
<p align="center"><img src="https://github.com/heltonmaia/ECT-proj-roboticArm/blob/main/images/stop%20example.png?raw=true" style="width: 600px; height: 420px;"></p>

### **Voice commands**

The following voice commands are used for an ideal detection. 

```
Right, Left, Up, Down, Open or Close
```

But you can also command through short phrases that suggest any of the above commands, such as "go right", "go up" or "open gripper". As long as the sentence does not take more than 2 seconds to be spoken, it should work correctly.

# Authors
- [Kennymar Oliveira](https://github.com/KennymarOliveira)
- [Virna Aguiar](https://github.com/virnaaguiaar)
- [Thiago Lopes](https://github.com/thiagoclopes)

Supervisor: [Helton Maia](https://heltonmaia.github.io/heltonmaia/) 

# Acknowledgements

Project developed for educational purposes at the Automation and Robotics Laboratory (LAR) of the School of Science and Technology (ECT) of the Federal University of Rio Grande do Norte (UFRN).
