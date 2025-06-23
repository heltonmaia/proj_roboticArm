# Hybrid Control for Robotic Arms: Combining Gesture Recognition and Voice Commands

This project encompasses computer vision, machine learning, 3D printing, and Arduino integration, with the primary goal of enabling robotic arms to replicate the movements of a human arm. The project consists of a PyQt6 application where the user can choose to control the robotic arm either through gestures or voice commands. If the user prefers gesture control, the application will use the OpenCV computer vision library to capture real-time images using a webcam or smartphone, and relevant information from the user's hand will then be detected by one of our neural networks trained based on the YOLOv8 architecture. However, if the user prefers voice command control, the application will use the Librosa library for recording and processing, and then our custom audio classification neural network will be used to recognize the command. Regardless of the control method, the movement of the robotic arm, which was 3D-printed, is executed by the Arduino according to serial port commands sent by a Python script using the Pyserial module.

[Project video](https://github.com/heltonmaia/ECT-proj-roboticArm/assets/4681481/2796c126-4182-4c66-be8b-e16110343908)

# How to use
### **Requirements**
  - Webcam or a smartphone
  - Arduino IDE

### **Downloading the Robotic Arm Control program**

Downloading the Robotic Arm Control program


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

Using the App

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

<h3 align="center"><b>"Search" command</b></h3>

<h3 align="center"><b>"Grab" command </b></h3>

<h3 align="center"><b>"Stop" command</b></h3>

### **Voice commands**

The following voice commands are used for an ideal detection. 

```
Right, Left, Up, Down, Open or Close
```

But you can also command through short phrases that suggest any of the above commands, such as "go right", "go up" or "open gripper". As long as the sentence does not take more than 2 seconds to be spoken, it should work correctly.

# Authors
- [Kennymar Oliveira](https://github.com/KennymarOliveira)
- [Thiago Lopes](https://github.com/thiagoclopes)
- [Virna Aguiar](https://github.com/virnaaguiaar)

Supervisor: [Helton Maia](https://heltonmaia.github.io/heltonmaia/) 

# Acknowledgements

Project developed for educational purposes at the Automation and Robotics Laboratory (LAR) of the School of Science and Technology (ECT) of the Federal University of Rio Grande do Norte (UFRN).
