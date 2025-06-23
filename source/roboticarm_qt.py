import sys
import os
import webbrowser
import cv2
import struct
import time
import serial
from ultralytics import YOLO
from src.utils import available_capture_devices
from src.utils import detection_infos
from src.utils import robotic_arm
from src.utils.voice_recognition import summarize_audio
from src.utils.two_dof_kinematics import set_point
from PyQt6.QtGui import *
from PyQt6.QtWidgets import *
from PyQt6.QtCore import *
from PyQt6 import uic

VERSION = "2.5.0-beta"

# Classe da janela principal
class RoboticArmMenu(QWidget):

    def __init__(self):
        super().__init__()
        uic.loadUi('./ui/main_window.ui', self)
        self.setWindowTitle(f'Robotic Arm Control v{VERSION}')
        self.setWindowIcon(QIcon('./src/images/roboticarm.png'))

        self.additional_info_label.setText(f'ECT - UFRN\n{VERSION}')

        # Botão Exit fecha o programa
        self.exit_button.clicked.connect(self.close)

        # Botão About redireciona para o github
        self.about_button.clicked.connect(self.redirect_to_github)

        # Botão Setup carrega a janela de configurações
        self.setup_window = RoboticArmSetup()
        self.setup_button.clicked.connect(self.show_setup_window)

        # Conexão do sinal para atualizar as informações dinâmicas na janela de configurações
        self.setup_window.settings_update_signal.connect(self.settings_update_slot)

        # Inicia/Para a execução dos processos (Threads)
        self.start_stop_button.clicked.connect(self.start_stop_execution)

        # Configuração da Thread 1
        self.Thread_1 = Thread_1()  
        self.Thread_1.manual_gestures_image_update_signal.connect(self.manual_gestures_image_update_slot)
        self.Thread_1.manual_gestures_info_update_signal.connect(self.manual_gestures_info_update_slot)
        self.Thread_1.t1_exception_stop_signal.connect(self.t1_exception_stop)

        # Configuração da Thread_2
        self.Thread_2 = Thread_2()
        self.Thread_2.audio_info_update_signal.connect(self.audio_info_update_slot)
        self.Thread_2.t2_exception_stop_signal.connect(self.t2_exception_stop)

        # Configuração da Thread_3
        self.Thread_3 = Thread_3()
        self.Thread_3.automatic_gestures_image_update_signal.connect(self.automatic_gestures_image_update_slot)
        self.Thread_3.automatic_gestures_info_update_signal.connect(self.automatic_gestures_info_update_slot)
        self.Thread_3.t3_exception_stop_signal.connect(self.t3_exception_stop)

        # Widget de processamento
        self.processing_widget = self.findChild(QWidget, 'processing_widget')

        # Leitura do arquivo de configurações
        self.setup_window.read_setup_file()

        # Configruação inicial dos textos dos botões e das informações
        if self.setup_window.get_control_method() == "Manual gestures":
            if not self.Thread_1.isRunning():
                self.start_stop_button.setText("Start")
                self.fps_info.setText("-")
                self.capture_device_info.setText(f'{self.setup_window.cap_device}')
                self.com_port_info.setText(f'{self.setup_window.COM}')
                self.in_range_info.setText("-")
                self.position_info.setText("(-, -)")
                self.state_info.setText("-")
                self.direction_info.setText("-")
                self.serial_monitor.clear()
                self.serial_monitor.setPlaceholderText("Monitor...")
            else:
                self.start_stop_button.setText("Stop")
        elif self.setup_window.get_control_method() == "Voice":
            if not self.Thread_2.isRunning():
                self.start_stop_button.setText("Start")
                self.capture_device_info.setText(f'{self.setup_window.cap_device}')
                self.com_port_info.setText(f'{self.setup_window.COM}')
                self.fps_label.hide()
                self.fps_info.hide()
                self.in_range_label.hide()
                self.in_range_info.hide()
                self.position_info.resize(160, 15)
                self.position_info.setText("(-, -, -, -)")
                self.state_label.setText("Class:")
                self.state_label.move(240, 30)
                self.state_info.setText("-")
                self.state_info.move(290, 30)
                self.direction_label.hide()
                self.direction_info.hide()
                self.serial_monitor.clear()
                self.serial_monitor.setPlaceholderText("Monitor...")
            else:
                self.start_stop_button.setText("Stop")
        elif self.setup_window.get_control_method() == "Automatic gestures":
            if not self.Thread_3.isRunning():
                self.start_stop_button.setText("Start")
                self.fps_info.setText("-")
                self.capture_device_info.setText(f'{self.setup_window.cap_device}')
                self.com_port_info.setText(f'{self.setup_window.COM}')
                self.in_range_info.setText("-")
                self.state_info.setText("-")
                self.state_label.setText("Class:")
                self.state_label.move(160, 30)
                self.state_info.move(210, 30)
                self.position_info.hide()
                self.position_label.hide()
                self.direction_label.hide()
                self.direction_info.hide()
                self.fps_info.setText("-")
                self.serial_monitor.clear()
                self.serial_monitor.setPlaceholderText("Monitor...")
            else:
                self.start_stop_button.setText("Stop")

        # Configuração das informações iniciais do widget de processamento
        self.processing_widget.setStyleSheet("background-color: black; color: white; border: 1px solid; border-color: #465863;")
        self.processing_widget.setText("Not running...")

    def redirect_to_github(self):
        '''
            Esta função redireciona o usuário para o repositório do projeto no github.
        '''

        webbrowser.open('https://github.com/heltonmaia/ECT-proj-roboticArm/')
    
    def show_setup_window(self):
        '''
            Esta função mostra a janela de configurações.
        '''

        self.start_stop_button.setEnabled(False)
        self.about_button.setEnabled(False)
        self.exit_button.setEnabled(False)
        self.setup_button.setEnabled(False)
        self.setup_window.show()

    def start_stop_execution(self):
        '''
            Esta função inicia ou para a execução do programa. O tipo de execução varia de acordo com o método de controle
            escolhido pelo usuário.
        '''

        # Leitura do arquivo de configurações para decidir qual Thread rodar
        control_method = self.setup_window.get_control_method()

        if control_method == "Manual gestures":

            if not self.Thread_1.isRunning():
                self.start_stop_button.setText("Stop")
                self.Thread_1.start()
                self.setup_button.setEnabled(False)
            else:
                self.start_stop_button.setText("Start")
                self.Thread_1.stop()

                # Reseta todas as informações dinâmicas
                self.fps_info.setText("-")
                self.in_range_info.setText("-")
                self.position_info.setText("(-, -)")
                self.state_info.setText("-")
                self.direction_info.setText("-")
                self.processing_widget.setStyleSheet("background-color: black; color: white; border: 1px solid; border-color: #465863;")
                self.processing_widget.setText("Not running...")
                self.serial_monitor.clear()
                self.serial_monitor.setPlaceholderText("Monitor...")
                self.setup_button.setEnabled(True)

                # Criação de uma nova instância
                self.Thread_1 = Thread_1()
                self.Thread_1.manual_gestures_image_update_signal.connect(self.manual_gestures_image_update_slot)
                self.Thread_1.manual_gestures_info_update_signal.connect(self.manual_gestures_info_update_slot)
                self.Thread_1.t1_exception_stop_signal.connect(self.t1_exception_stop)

        elif control_method == "Automatic gestures":

            if not self.Thread_3.isRunning():
                self.start_stop_button.setText("Stop")
                self.Thread_3.start()
                self.setup_button.setEnabled(False)
            else:
                self.start_stop_button.setText("Start")
                self.Thread_3.stop()

                # Reseta todas as informações dinâmicas
                self.fps_info.setText("-")
                self.in_range_info.setText("-")
                self.position_info.hide()
                self.position_label.hide()
                self.state_label.setText("Class:")
                self.state_info.setText("-")
                self.direction_label.hide()
                self.direction_info.hide()
                self.processing_widget.setStyleSheet("background-color: black; color: white; border: 1px solid; border-color: #465863;")
                self.processing_widget.setText("Not running...")
                self.serial_monitor.clear()
                self.serial_monitor.setPlaceholderText("Monitor...")
                self.setup_button.setEnabled(True)
                self.Thread_3 = Thread_3()
                self.Thread_3.automatic_gestures_image_update_signal.connect(self.automatic_gestures_image_update_slot)
                self.Thread_3.automatic_gestures_info_update_signal.connect(self.automatic_gestures_info_update_slot)
                self.Thread_3.t3_exception_stop_signal.connect(self.t3_exception_stop)

        elif control_method == "Voice":

            if not self.Thread_2.isRunning():
                self.start_stop_button.setText("Stop")
                self.Thread_2.start()
                self.setup_button.setEnabled(False)
                self.processing_widget.setStyleSheet("background-color: black; color: white; border: 1px solid; border-color: #465863; alignment: center;")
                self.processing_widget.setText("Audio Classification\n🔊\n...")
                self.fps_label.hide()
                self.fps_info.hide()
                self.in_range_label.hide()
                self.in_range_info.hide()
                self.position_info.resize(160, 15)
                self.position_info.setText("(-, -, -, -)")
                self.state_label.setText("Class:")
                self.state_info.resize(70, 15)
                self.state_label.move(240, 30)
                self.state_info.move(290, 30)
                self.direction_label.hide()
                self.direction_info.hide()
            else:
                self.start_stop_button.setText("Start")
                self.Thread_2.stop()

                # Reseta todas as informações dinâmicas
                self.position_info.setText("(-, -, -, -)")
                self.state_info.setText("-")
                self.processing_widget.setStyleSheet("background-color: black; color: white; border: 1px solid; border-color: #465863;")
                self.processing_widget.setText("Not running...")
                self.setup_button.setEnabled(True)
                self.Thread_2 = Thread_2()
                self.Thread_2.audio_info_update_signal.connect(self.audio_info_update_slot)
                self.Thread_2.t2_exception_stop_signal.connect(self.t2_exception_stop)
    
    def settings_update_slot(self):
        '''
            Essa função atualiza as informações das configurações do programa.
        '''
        
        self.capture_device_info.setText(f'{self.setup_window.get_capture_device()}')
        self.com_port_info.setText(f'{self.setup_window.get_com_port()}')
        
        control_method = self.setup_window.get_control_method()

        if control_method == "Manual gestures":
            self.update_manual_gestures_interface()
        elif control_method == "Voice":
            self.update_voice_control_interface()
        elif control_method == "Automatic gestures":
            self.update_automatic_gestures_interface()
    
    def update_manual_gestures_interface(self):
        '''
            Esta função atualiza as informações estáticas do método de controle de gestos manuais.
        '''

        # Quais informações mostrar
        self.fps_label.show()
        self.fps_info.show()
        self.capture_device_label.show()
        self.capture_device_info.show()
        self.com_port_label.show()
        self.com_port_info.show()
        self.in_range_label.show()
        self.in_range_info.show()
        self.position_info.show()
        self.position_label.show()
        self.state_label.show()
        self.state_info.show()
        self.direction_label.show()
        self.direction_info.show()

        # Quais informações esconder
        # Nenhuma - Todas as informações estáticas são mostradas no método de controle de gestos manuais

        # Definição e reposicionamento
        self.fps_info.setText("-")
        self.in_range_info.setText("-")
        self.position_info.resize(80, 15)
        self.position_info.setText("(-, -)")
        self.state_label.setText("State:")
        self.state_info.setText("-")
        self.state_label.move(160, 30)
        self.state_info.move(210, 30)
        self.direction_info.setText("-")
        self.serial_monitor.clear()
        self.serial_monitor.setPlaceholderText("Monitor...")
        
    def update_voice_control_interface(self):
        '''
            Esta função atualiza as informações estáticas do método de controle por voz.
        '''

        # Quais informações mostrar
        self.capture_device_label.show()
        self.capture_device_info.show()
        self.com_port_label.show()
        self.com_port_info.show()
        self.position_info.show()
        self.position_label.show()
        self.state_label.show()
        self.state_info.show()

        # Quais informações esconder
        self.fps_label.hide()
        self.fps_info.hide()
        self.in_range_label.hide()
        self.in_range_info.hide()
        self.direction_label.hide()
        self.direction_info.hide()

        # Definição e reposicionamento
        self.position_info.resize(160, 15)
        self.position_info.setText("(-, -, -, -)")
        self.state_label.setText("Class:")
        self.state_label.move(240, 30)
        self.state_info.move(290, 30)
        self.serial_monitor.clear()
        self.serial_monitor.setPlaceholderText("Monitor...")

        
    def update_automatic_gestures_interface(self):
        '''
            Esta função atualiza as informações estáticas do método de controle de gestos automáticos.
        '''

        # Quais informações mostrar
        self.fps_label.show()
        self.fps_info.show()
        self.capture_device_label.show()
        self.capture_device_info.show()
        self.com_port_label.show()
        self.com_port_info.show()
        self.in_range_label.show()
        self.in_range_info.show()
        self.state_label.show()
        self.state_info.show()

        # Quais informações esconder
        self.position_info.hide()
        self.position_label.hide()
        self.direction_label.hide()
        self.direction_info.hide()

        # Definição e reposicionamento
        self.fps_info.setText("-")
        self.in_range_info.setText("-")
        self.state_label.setText("Class:")
        self.state_label.move(160, 30)
        self.state_info.move(210, 30)
        self.state_info.setText("-")
        self.serial_monitor.clear()
        self.serial_monitor.setPlaceholderText("Monitor...")
    
    def manual_gestures_image_update_slot(self, image):
        '''
            Esta função atualiza o widget de processamento para o método de controle de gestos manuais.
        '''

        if not self.Thread_1.isRunning() or image is None or image.isNull():

            self.processing_widget.setStyleSheet("background-color: black; color: white; border: 1px solid; border-color: #465863;")
            self.processing_widget.setText("Not running...")

        else:

            self.processing_widget.setStyleSheet("border: 1px solid; border-color: #465863;")
            self.processing_widget.setText("")
            self.processing_widget.setPixmap(QPixmap.fromImage(image))
    

    def manual_gestures_info_update_slot(self, capture_device, com_port, in_range, position, state, direction, fps, speed):
        '''
            Esta função atualiza as informações estáticas e dinâmicas para o método de controle de gestos manuais.
        '''

        self.capture_device_info.setText(str(capture_device))
        self.com_port_info.setText(str(com_port))

        if in_range:
            self.in_range_info.setText("Yes")
        else:
            self.in_range_info.setText("No")

        self.position_info.setText(str(position))
        self.state_info.setText(str(state))

        # Imagem base
        arrow_image = QPixmap('./src/images/arrow.png')
        # Ângulo da imagem base
        angle = 0

        if direction != "Still":

            if direction == "Left":
                angle = 180
            elif direction == "Right":
                angle = 0
            elif direction == "Up":
                angle = 270
            elif direction == "Down":
                sangle = 90
            elif direction == "Upper left":
                angle = 225
            elif direction == "Upper right":
                angle = 315
            elif direction == "Lower left":
                angle = 135
            elif direction == "Lower right":
                angle = 45

            rotated_arrow_image = arrow_image.transformed(QTransform().rotate(angle))
            rotated_arrow_image = rotated_arrow_image.scaled(15, 15, Qt.AspectRatioMode.KeepAspectRatio)
            self.direction_info.setPixmap(rotated_arrow_image)
        
        else:
            self.direction_info.setText('-')

        self.fps_info.setText(str(fps))
        self.serial_monitor.appendPlainText(f"Inference speed: {speed} ms")
    
    def audio_info_update_slot(self, cap_device, com_port, predicted_class, position_key, position):
        '''
            Esta função atualiza as informações estáticas e dinâmicas para o método de controle por voz.
        '''

        self.capture_device_info.setText(str(cap_device))
        self.com_port_info.setText(str(com_port))
        self.state_info.setText(str(predicted_class))
        self.position_info.setText(str(position))
        self.serial_monitor.clear()
        self.serial_monitor.appendPlainText(f"Position key: {position_key}")

    def automatic_gestures_image_update_slot(self, image):
        '''
            Esta função atualiza o widget de processamento para o método de controle de gestos automáticos.
        '''

        if not self.Thread_3.isRunning() or image is None or image.isNull():

            self.processing_widget.setStyleSheet("background-color: black; color: white; border: 1px solid; border-color: #465863;")
            self.processing_widget.setText("Not running...")

        else:

            self.processing_widget.setStyleSheet("border: 1px solid; border-color: #465863;")
            self.processing_widget.setText("")
            self.processing_widget.setPixmap(QPixmap.fromImage(image))

    def automatic_gestures_info_update_slot(self, capture_device, com_port, in_range, hand_class, fps, speed):
        '''
            Esta função atualiza as informações estáticas e dinâmicas para o método de controle de gestos automáticos.
        '''
        
        self.capture_device_info.setText(str(capture_device))
        self.com_port_info.setText(str(com_port))

        if in_range:
            self.in_range_info.setText("Yes")
        else:
            self.in_range_info.setText("No")

        self.state_info.setText(str(hand_class))
        self.fps_info.setText(str(fps))
        self.serial_monitor.appendPlainText(f"Inference speed: {speed} ms")
    
    def t1_exception_stop(self, stop_flag):
        '''
            Esta função é uma medida de segurança que garante que a Thread 1 pare a execução
            corretamente caso algum erro ocorra.
        '''

        if self.Thread_1.isRunning() and stop_flag:
            self.start_stop_button.setText("Start")
            self.Thread_1.stop()

            # Reseta todas as informações dinâmicas
            self.fps_info.setText("-")
            self.in_range_info.setText("-")
            self.position_info.setText("(-, -)")
            self.state_info.setText("-")
            self.direction_info.setText("-")
            self.processing_widget.setStyleSheet("background-color: black; color: white; border: 1px solid; border-color: #465863;")
            self.processing_widget.setText("Not running...")
            self.serial_monitor.clear()
            self.serial_monitor.setPlaceholderText("Monitor...")
            self.setup_button.setEnabled(True)
            
            # Criação de uma nova instância
            self.Thread_1 = Thread_1()
            self.Thread_1 = Thread_1()
            self.Thread_1.manual_gestures_image_update_signal.connect(self.manual_gestures_image_update_slot)
            self.Thread_1.manual_gestures_info_update_signal.connect(self.manual_gestures_info_update_slot)
            self.Thread_1.t1_exception_stop_signal.connect(self.t1_exception_stop)
    
    def t2_exception_stop(self, stop_flag):
        '''
            Esta função é uma medida de segurança que garante que a Thread 2 pare a execução
            corretamente caso algum erro ocorra.
        '''

        if self.Thread_2.isRunning() and stop_flag:
            self.start_stop_button.setText("Start")
            self.Thread_2.stop()

            # Reseta todas as informações dinâmicas
            self.position_info.setText("(-, -, -, -)")
            self.state_info.setText("-")
            self.processing_widget.setStyleSheet("background-color: black; color: white; border: 1px solid; border-color: #465863;")
            self.processing_widget.setText("Not running...")
            self.setup_button.setEnabled(True)
            
            # Criação de uma nova instância
            self.Thread_2 = Thread_2()
            self.Thread_2.audio_info_update_signal.connect(self.audio_info_update_slot)
            self.Thread_2.t2_exception_stop_signal.connect(self.t2_exception_stop)
    
    def t3_exception_stop(self, stop_flag):
        '''
            Esta função é uma medida de segurança que garante que a Thread 3 pare a execução
            corretamente caso algum erro ocorra.
        '''

        if self.Thread_3.isRunning() and stop_flag:
            self.start_stop_button.setText("Start")
            self.Thread_3.stop()

            # Reseta todas as informações dinâmicas
            self.fps_info.setText("-")
            self.in_range_info.setText("-")
            self.position_info.hide()
            self.position_label.hide()
            self.state_label.setText("Class:")
            self.state_info.setText("-")
            self.direction_label.hide()
            self.direction_info.hide()
            self.processing_widget.setStyleSheet("background-color: black; color: white; border: 1px solid; border-color: #465863;")
            self.processing_widget.setText("Not running...")
            self.serial_monitor.clear()
            self.serial_monitor.setPlaceholderText("Monitor...")
            self.setup_button.setEnabled(True)

            # Criação de uma nova instância
            self.Thread_3 = Thread_3()
            self.Thread_3.automatic_gestures_image_update_signal.connect(self.automatic_gestures_image_update_slot)
            self.Thread_3.automatic_gestures_info_update_signal.connect(self.automatic_gestures_info_update_slot)
            self.Thread_3.t3_exception_stop_signal.connect(self.t3_exception_stop)

# Classe da janela de configurações
class RoboticArmSetup(QWidget):

    # Checa se tem algum dispositivo de captura disponível
    available_devices = available_capture_devices.capture_devices()

    # Sinal para atualizar as informações dinâmicas na janela de configurações
    settings_update_signal = pyqtSignal()

    def __init__(self):
        super().__init__()
        uic.loadUi('./ui/setup_window.ui', self)
        self.setWindowTitle('Robotic Arm Control Setup')
        self.setWindowIcon(QIcon('./src/images/roboticarm.png'))

        # Valores padrão
        self.COM = 3
        self.cap_device = 0
        self.control_method = "Manual gestures"
        self.api_key = "No-key"
        self.read_setup_file()

        # Foco persistente na janela
        self.setWindowModality(Qt.WindowModality.ApplicationModal)

        # Configura os valores padrão
        self.com_port_text.setText(str(self.COM))
        self.capture_device_text.setText(str(self.cap_device))
        self.control_method_box.addItems(["Manual gestures", "Automatic gestures","Voice"])
        self.control_method_box.setCurrentText(self.control_method)
        self.api_key_text.setText(str(self.api_key))

        # Conecta os sinais para mudar/validar os itens padrão
        self.com_port_text.textChanged.connect(self.validate_com_port)
        self.capture_device_text.textChanged.connect(self.validate_capture_device)
        self.control_method_box.currentTextChanged.connect(self.update_control_method)
        self.api_key_text.textChanged.connect(self.validate_api_key)

        # O botão Save fecha a janela de setup, salva os valores e mostra a janela principal novamente
        self.save_button.clicked.connect(self.show_menu_window)

        # O botão Restore Defaults restaura os valores padrão
        self.restore_defaults_button.clicked.connect(self.restore_default_values)
    
    def read_setup_file(self):
        '''
            Esta função lê o arquivo de configurações.
        '''
        
        if os.path.exists('setup.txt'):
            with open('setup.txt', 'r') as setup_file:
                lines = setup_file.readlines()
                for line in lines:
                    line = line.strip()
                    if line.startswith('com_port='):
                        self.COM = int(line.split('=')[1])
                    elif line.startswith('capture_device='):
                        self.cap_device = int(line.split('=')[1])
                    elif line.startswith('control_method='):
                        self.control_method = str(line.split('=')[1])
                    elif line.startswith('api_key='):
                        self.api_key = str(line.split('=')[1])

    def get_capture_device(self):
        '''
            Esta função adquire a informação do dispositivo de captura.
        '''

        return self.cap_device

    def get_com_port(self):
        '''
            Esta função adquire a informação do dispositivo da porta serial.
        '''

        return self.COM
    
    def get_control_method(self):
        '''
            Esta função adquire a informação do método de controle.
        '''

        return self.control_method
    
    def get_api_key(self):
        '''
            Esta função adquire a informação da chave api do google ai studio
        '''

        return self.api_key
    
    def validate_com_port(self, text):
        '''
            Função de validação da porta serial.
        '''
        
        try:

            if not text:
                self.com_port_label.setStyleSheet("color: red; border: none;")
            elif not text.isdigit():
                self.com_port_label.setStyleSheet("color: white; border: none;")
                self.com_port_text.setText(text[:-1])
            else:
                self.com_port_label.setStyleSheet("color: white; border: none;")
                self.COM = int(text)
                self.update_setup_file()

        except Exception as e:

            print("Error while updating com_port:", e)

    def validate_capture_device(self, text):
        '''
            Função de validação do dispositivo de captura.
        '''

        try:

            if not text:
                self.capture_device_label.setStyleSheet("color: red; border: none;")
            elif not text.isdigit():
                self.capture_device_label.setStyleSheet("color: white; border: none;")
                self.capture_device_text.setText(text[:-1])
            else:
                device_id = int(text)
                if device_id in self.available_devices:
                    self.capture_device_label.setStyleSheet("color: white; border: none;")
                    self.cap_device = int(text)
                    self.update_setup_file()
                else:
                    self.capture_device_label.setStyleSheet("color: red; border: none;")
                    print("Device not available")

        except Exception as e:

            print("Error while updating capture device:", e)
    
    def update_control_method(self, text):
        '''
            Esta função atualiza a informação do método de controle.
        '''

        self.control_method = text
        self.update_setup_file()
    
    def validate_api_key(self, text):
        '''
            Função de validação da chave api do google ai studio.
        '''

        try:

            if not text or " " in text:
                self.api_key_label.setStyleSheet("color: red; border: none;")
            else:
                self.api_key_label.setStyleSheet("color: white; border: none;")
                self.api_key = text.strip()
                self.update_setup_file()

        except Exception as e:

            print("Error while validating API key:", e)

    def update_setup_file(self):
        '''
            Esta função atualiza o arquivo de configurações, executando a criação caso não exista
            ou a sobrescrição caso já exista.
        '''
        
        try:

            with open('setup.txt', 'w') as setup_file:
                setup_file.write(f'com_port={self.COM}\n')
                setup_file.write(f'capture_device={self.cap_device}\n')
                setup_file.write(f'control_method={self.control_method}\n')
                setup_file.write(f'api_key={self.api_key}\n')

        except Exception as e:

            print("Error while updating setup.txt:", e)
    
    def restore_default_values(self):
        '''
            Esta função restaura os valores de configuração padrão.
        '''

        self.COM = 3
        self.cap_device = 0
        self.control_method = "Manual gestures"
        self.api_key = "No-key"
        self.com_port_text.setText(str(self.COM))
        self.capture_device_text.setText(str(self.cap_device))
        self.control_method_box.setCurrentText(self.control_method)
        self.api_key_text.setText(str(self.api_key))
        self.update_setup_file()

    def show_menu_window(self):
        '''
            Esta função fecha a janela de configurações e mostra novamente a janela principal.
        '''

        if self.com_port_text.text() != '' and self.capture_device_text.text() != '':

            if int(self.capture_device_text.text()) in self.available_devices:

                self.settings_update_signal.emit()
                menu_window.start_stop_button.setEnabled(True)
                menu_window.about_button.setEnabled(True)
                menu_window.exit_button.setEnabled(True)
                menu_window.setup_button.setEnabled(True)
                menu_window.show()
                self.close()
    
    def closeEvent(self, event):
        '''
            Esta função garante que o fechamento da janela de configurações reative os botões corretamente
            mesmo se a janela tenha sido fechada abruptamente.
        '''
        
        menu_window.start_stop_button.setEnabled(True)
        menu_window.about_button.setEnabled(True)
        menu_window.exit_button.setEnabled(True)
        menu_window.setup_button.setEnabled(True)
        event.accept()

# Thread para lidar com os gestos manuais
class Thread_1(QThread):

    # Configuração dos sinais de informações para o método de controle de gestos manuais
    manual_gestures_image_update_signal = pyqtSignal(QImage)
    manual_gestures_info_update_signal = pyqtSignal(int, int, bool, tuple, str, str, int, str)
    t1_exception_stop_signal = pyqtSignal(bool)

    def __init__(self):
        super().__init__()
        self.ThreadActive = True
        self.mutex = QMutex()

        if os.path.exists('setup.txt'):

            with open('setup.txt', 'r') as setup_file:
                lines = setup_file.readlines()
                for line in lines:
                    line = line.strip()
                    if line.startswith('com_port='):
                        self.COM = int(line.split('=')[1])
                    elif line.startswith('capture_device='):
                        self.cap_device = int(line.split('=')[1])
                    elif line.startswith('control_method='):
                        self.control_method = str(line.split('=')[1])
                    elif line.startswith('api_key='):
                        self.api_key = str(line.split('=')[1])
        else:

            # Valores padrão
            self.COM = 3
            self.cap_device = 0
            self.control_method = "gestures"
            self.api_key = "No-key"
    
    def run(self):

        # Configuração da porta serial
        try:

            self.arm = serial.Serial(f'COM{self.COM}', 9600, timeout=0.2)
            if not self.arm.isOpen():
                self.arm.open()

        except Exception as e:

            print(f"Error: {e}")

        model = YOLO('./src/misc/yolo-v11-weight-manual-gestures.pt')
        cap = cv2.VideoCapture(self.cap_device)
        prev_m_coord_x = 0
        prev_m_coord_y = 0
        prev_frame_time = 0
        new_frame_time = 0
        pixel_threshold = 5
        rtlx = detection_infos.rect_top_left_x
        rtly = detection_infos.rect_top_left_y
        rbrx = detection_infos.rect_bottom_right_x
        rbry = detection_infos.rect_bottom_right_y

        while self.ThreadActive:

            read, frame = cap.read()

            if read:

                # Usa nosso modelo no frame
                results = model(source=frame, conf=0.85)
                boxes = results[0].boxes.cpu().numpy()

                best_detection = None
                best_score = 0

                # Contador de frames por segundo (FPS)
                new_frame_time = time.time()
                fps = 1 / (new_frame_time - prev_frame_time)
                prev_frame_time = new_frame_time
                fps = int(fps)

                # Processa informações individuais para cada mão no frame
                for box in boxes:

                    if box.cls in [0, 1]:

                        # Cálculo de informações chave para o processo
                        rect_coord = box.data[0][:4]
                        conf = box.data[0][4]
                        area = detection_infos.calculate_area(rect_coord)
                        m_coord_x = int((box.xyxy[0][2] + box.xyxy[0][0]) / 2)
                        m_coord_y = int((box.xyxy[0][1] + box.xyxy[0][3]) / 2)
                        hand_position = (m_coord_x, m_coord_y)
                        in_range = detection_infos.is_in_range(m_coord_x, m_coord_y)
                        score = detection_infos.calculate_score(area, conf)
                        direction = detection_infos.calculate_direction(pixel_threshold, m_coord_x, m_coord_y, prev_m_coord_x, prev_m_coord_y)

                        if robotic_arm.is_moving_axis_x(pixel_threshold, prev_m_coord_x, m_coord_x):

                            rotating_base_angle = robotic_arm.calculate_rotating_base_angle(m_coord_x)
                            prev_m_coord_x = m_coord_x

                        if robotic_arm.is_moving_axis_y(pixel_threshold, prev_m_coord_y, m_coord_y):

                            arm1_angle, arm2_angle = robotic_arm.calculate_angle_hastes(m_coord_y)
                            prev_m_coord_y = m_coord_y

                        if score > best_score:

                            best_score = score
                            best_detection = box

                        if best_detection is not None:

                            gripper_angle, state = robotic_arm.calculate_gripper_angle(best_detection.cls)

                            if best_detection.cls == 0:

                                hand_class = 'Closed Hand'
                                state = "Closed"

                            elif best_detection.cls == 1:

                                hand_class = 'Open Hand'
                                state = "Open"
                        else:

                            in_range = False
                            hand_class = 'None'
                            state = hand_class
                        
                        if in_range:
                            
                            try:
                                self.arm.write(struct.pack('BBBB', rotating_base_angle, gripper_angle, arm1_angle, arm2_angle))
                            except Exception as e:
                                print(f"Error: {e}")
                                self.t1_exception_stop_signal.emit(True)

                if best_detection is None:
                    in_range = False

                # Processamento de imagem
                annotated_frame = results[0].plot(boxes=False)
                flipped_annotated_frame = cv2.flip(annotated_frame, 1)
                image = cv2.cvtColor(flipped_annotated_frame, cv2.COLOR_BGR2RGB)
                flipped_image = cv2.flip(image, 1)

                try:

                    if in_range:
                        cv2.rectangle(flipped_image, (rtlx, rtly), (rbrx, rbry), (25, 255, 25), 3)
                    else:
                        cv2.rectangle(flipped_image, (rtlx, rtly), (rbrx, rbry), (255, 0, 0), 3)

                    if direction != "Still":
                        cv2.circle(flipped_image, (m_coord_x, m_coord_y), 3, (0, 255, 0), 2)
                    else:
                        cv2.circle(flipped_image, (m_coord_x, m_coord_y), 3, (255, 255, 255), 2)

                except Exception as e:

                    print(f"Error: {e}")

                converted_image = QImage(flipped_image.data,
                                         flipped_image.shape[1],
                                         flipped_image.shape[0],
                                         QImage.Format.Format_RGB888)
                final_image = converted_image.scaled(790, 500, Qt.AspectRatioMode.IgnoreAspectRatio)

                self.manual_gestures_image_update_signal.emit(final_image)

                speed = str(results[0].speed['inference'])

                try:
                    self.manual_gestures_info_update_signal.emit(self.cap_device, self.COM, in_range, hand_position, state, direction, fps, speed)
                except Exception as e:
                    print(f"Error: {e}")
        
        # Libera o acesso à câmera
        cap.release()

    def stop(self):
        with QMutexLocker(self.mutex):
            self.ThreadActive = False

        # Desaloca recursos corretamente antes de parar a Thread
        if hasattr(self, 'arm') and self.arm.isOpen():
            self.arm.close()
        
        self.quit()
        self.wait()

# Thread para lidar com a classificação de áudio
class Thread_2(QThread):

    # Configuração do sinal de informações do método de comando por voz
    audio_info_update_signal = pyqtSignal(int, int, str, str, str)
    t2_exception_stop_signal = pyqtSignal(bool)

    def __init__(self):
        super().__init__()
        self.ThreadActive = True
        self.mutex = QMutex()

        if os.path.exists('setup.txt'):

            with open('setup.txt', 'r') as setup_file:
                lines = setup_file.readlines()
                for line in lines:
                    line = line.strip()
                    if line.startswith('com_port='):
                        self.COM = int(line.split('=')[1])
                    elif line.startswith('capture_device='):
                        self.cap_device = int(line.split('=')[1])
                    elif line.startswith('control_method='):
                        self.control_method = str(line.split('=')[1])
                    elif line.startswith('api_key='):
                        self.api_key = str(line.split('=')[1])
                    
        else:

            # Valores padrão
            self.COM = 3
            self.cap_device = 0
            self.control_method = "voice"
            self.api_key = "No-key"
        
        self.positions = {
            "initial": (90, 10, 120, 110),
            "right": (175, 10, 120, 110),
            "left": (5, 10, 120, 110),
            "up": (90, 10, 175, 100),
            "down": (90, 10, 105, 160),
            "upper_right": (175, 10, 170, 100),
            "lower_right": (175, 10, 100, 170),
            "upper_left": (0, 10, 170, 100), 
            "lower_left": (0, 10, 100, 170)
        }

        self.current_position = "initial"
        self.position = self.positions[self.current_position]
        self.gripper_angle = 10
    
    def move_arm(self):
        '''
            Esta função empacota em formato de byte as informações dos ângulos e envia pela porta serial.
        '''

        data = struct.pack('BBBB', *self.positions[self.current_position])
        self.arm.write(data)
    
    def set_gripper_angle(self, predicted_class):
        '''
            Esta função decide qual ângulo será utilizado pela garra do braço robótico de acordo com
            a classe prevista pelo modelo.
        '''

        if predicted_class == "open":
            self.gripper_angle = 120
        elif predicted_class == "close":
            self.gripper_angle = 10

    def run(self):

        # Configuração da porta serial
        try:

            self.arm = serial.Serial(f'COM{self.COM}', 9600, timeout=0.2)
            if not self.arm.isOpen():
                self.arm.open()

        except Exception as e:

            print(f"Error: {e}")

        while self.ThreadActive:

            # Configuração do arquivo de flag, utilizado para parar imediatamente o processamento de áudio, caso necessário.
            if not os.path.exists("flag.txt"):

                with open("flag.txt", "w") as f:
                    f.write("1")

            else:

                with open("flag.txt", "w") as f:
                    f.write("1")

            # Usa o modelo gemini do google para resumir o comando de voz
            predicted_class = summarize_audio().strip()

            if predicted_class == "alternative_stop_flag":
                self.t2_exception_stop_signal.emit(True)

            # Escolha da próxima posição, de acordo com a class prevista e a posição atual
            with QMutexLocker(self.mutex):

                if predicted_class == "up":
                    self.current_position = {
                        "initial": "up",
                        "up": "up",
                        "down": "initial",
                        "left": "upper_left",
                        "right": "upper_right",
                        "upper_left": "upper_left",
                        "upper_right": "upper_right",
                        "lower_left": "left",
                        "lower_right": "right"
                    }.get(self.current_position, self.current_position)
                elif predicted_class == "down":
                    self.current_position = {
                        "initial": "down",
                        "down": "down",
                        "up": "initial",
                        "left": "lower_left",
                        "right": "lower_right",
                        "upper_left": "left",
                        "upper_right": "right",
                        "lower_left": "lower_left",
                        "lower_right": "lower_right"
                    }.get(self.current_position, self.current_position)
                elif predicted_class == "left":
                    self.current_position = {
                        "initial": "left",
                        "left": "left",
                        "right": "initial",
                        "up": "upper_left",
                        "down": "lower_left",
                        "upper_left": "upper_left",
                        "lower_left": "lower_left",
                        "upper_right": "up",
                        "lower_right": "down"
                    }.get(self.current_position, self.current_position)
                elif predicted_class == "right":
                    self.current_position = {
                        "initial": "right",
                        "right": "right",
                        "left": "initial",
                        "up": "upper_right",
                        "down": "lower_right",
                        "upper_left": "up",
                        "lower_left": "down",
                        "upper_right": "upper_right",
                        "lower_right": "lower_right"
                    }.get(self.current_position, self.current_position)

            self.position = self.positions[self.current_position]
            self.set_gripper_angle(predicted_class)
            self.position = (self.position[0], self.gripper_angle, self.position[2], self.position[3])
            
            try:
                self.move_arm()
            except Exception as e:
                print(f"Error: {e}")
                self.t2_exception_stop_signal.emit(True)

            try:
                self.audio_info_update_signal.emit(self.cap_device, self.COM, predicted_class, self.current_position, str(self.position))
            except Exception as e:
                print(f"Error: {e}")
    
    def stop(self):

        # Escrevendo flag no arquivo
        with open("flag.txt", "w") as f:
            f.write("0")

        with QMutexLocker(self.mutex):
            self.ThreadActive = False

        # Desaloca recursos corretamente antes de parar a Thread
        if hasattr(self, 'arm') and self.arm.isOpen():
            self.arm.close()

        self.quit()
        self.wait()

# Thread para lidar com os gestos automáticos
class Thread_3(QThread):

    # Configuração dos sinais para o método de controle de gestos automáticos
    automatic_gestures_image_update_signal = pyqtSignal(QImage)
    automatic_gestures_info_update_signal = pyqtSignal(int, int, bool, str, int, str)
    t3_exception_stop_signal = pyqtSignal(bool)

    def __init__(self):
        super().__init__()
        self.ThreadActive = True
        self.mutex = QMutex()
        self.last_hand_class = None
        self.last_position = [90, 10, 90, 90]

        if os.path.exists('setup.txt'):

            with open('setup.txt', 'r') as setup_file:
                lines = setup_file.readlines()
                for line in lines:
                    line = line.strip()
                    if line.startswith('com_port='):
                        self.COM = int(line.split('=')[1])
                    elif line.startswith('capture_device='):
                        self.cap_device = int(line.split('=')[1])
                    elif line.startswith('control_method='):
                        self.control_method = str(line.split('=')[1])
                    elif line.startswith('api_key='):
                        self.api_key = str(line.split('=')[1])

        else:

            # Valores padrão
            self.COM = 3
            self.cap_device = 0
            self.control_method = "Automatic gestures"
            self.api_key = "No-key"

    def set_command(self, hand_class: str):
        '''
            Esta função escolhe e executa um comando automático para o braço robótico de acordo com o gesto do usuário.
            A posição anterior do braço é mantida em self.last_position para comandos como "grab".
        '''

        if hand_class == "start":

            # Ângulos
            rotating_base = 90
            gripper = 10
            arm1 = 70
            arm2 = 110

            self.rotating_base_angle = max(0, min(180, rotating_base))
            self.gripper_angle = max(0, min(180, gripper))
            self.arm1_angle = max(0, min(180, arm1))
            self.arm2_angle = max(0, min(180, arm2))

            self.last_position = [rotating_base, gripper, arm1, arm2]

        elif hand_class == "search":

            # Ponto de destino em centímetros
            x = 10
            y = 15

            # Ângulos
            rotating_base = 90
            gripper = 170
            arm1, arm2 = set_point(x, y)

            self.rotating_base_angle = max(0, min(180, rotating_base))
            self.gripper_angle = max(0, min(180, gripper))
            self.arm1_angle = max(0, min(180, arm1))
            self.arm2_angle = max(0, min(180, arm2))

            self.last_position = [rotating_base, gripper, arm1, arm2]

        elif hand_class == "grab":

            rotating_base = self.last_position[0]
            gripper = 10
            arm1 = self.last_position[2]
            arm2 = self.last_position[3]

            # Apenas o gripper se move
            self.gripper_angle = max(0, min(180, gripper))

            self.last_position = [rotating_base, gripper, arm1, arm2]

        elif hand_class == "stop":

            # Ângulos
            rotating_base = 90
            gripper = 10
            arm1 = 90
            arm2 = 90

            self.rotating_base_angle = max(0, min(180, rotating_base))
            self.gripper_angle = max(0, min(180, gripper))
            self.arm1_angle = max(0, min(180, arm1))
            self.arm2_angle = max(0, min(180, arm2))

            self.last_position = [rotating_base, gripper, arm1, arm2]
        
        self.arm.write(struct.pack('BBBB', self.last_position[0], self.last_position[1], self.last_position[2], self.last_position[3]))    

    def run(self):

        # Configuração da porta serial
        try:

            self.arm = serial.Serial(f'COM{self.COM}', 9600, timeout=0.2)
            if not self.arm.isOpen():
                self.arm.open()

        except Exception as e:

            print(f"Error: {e}")

        model = YOLO('./src/misc/yolo-v11-weight-auto-gestures.pt')
        cap = cv2.VideoCapture(self.cap_device)
        prev_frame_time = 0
        new_frame_time = 0
        rtlx = detection_infos.rect_top_left_x
        rtly = detection_infos.rect_top_left_y
        rbrx = detection_infos.rect_bottom_right_x
        rbry = detection_infos.rect_bottom_right_y

        while self.ThreadActive:

            read, frame = cap.read()

            if read:

                # Usa nosso modelo no frame
                results = model(source=frame, conf=0.85)
                boxes = results[0].boxes.cpu().numpy()

                best_detection = None
                best_score = 0
                in_range = False
                hand_class = None

                # Contador de frames por segundo (FPS)
                new_frame_time = time.time()
                fps = 1 / (new_frame_time - prev_frame_time)
                prev_frame_time = new_frame_time
                fps = int(fps)

                # Processa informações individuais para cada mão no frame
                for box in boxes:

                    if box.cls in [0, 1, 2, 3]:

                        # Cálculo de informações chave para o processo
                        rect_coord = box.data[0][:4]
                        conf = box.data[0][4]
                        area = detection_infos.calculate_area(rect_coord)
                        m_coord_x = int((box.xyxy[0][2] + box.xyxy[0][0]) / 2)
                        m_coord_y = int((box.xyxy[0][1] + box.xyxy[0][3]) / 2)
                        in_range = detection_infos.is_in_range(m_coord_x, m_coord_y)
                        score = detection_infos.calculate_score(area, conf)

                        if score > best_score:

                            best_score = score
                            best_detection = box
                        
                        if in_range:

                            if best_detection is not None:
                                
                                if best_detection.cls == 0:
                                    hand_class = "start"
                                elif best_detection.cls == 1:
                                    hand_class = "search"
                                elif best_detection.cls == 2:
                                    hand_class = "grab"
                                elif best_detection.cls == 3:
                                    hand_class = "stop"
                                else:
                                    hand_class = None

                            else:

                                hand_class = None

                            self.last_hand_class = hand_class

                            try:
                                self.set_command(self.last_hand_class)
                            except Exception as e:
                                print(f"Error {e}")
                                self.t3_exception_stop_signal.emit(True)

                # Processamento de imagem
                annotated_frame = results[0].plot(boxes=True)
                flipped_annotated_frame = cv2.flip(annotated_frame, 1)
                image = cv2.cvtColor(flipped_annotated_frame, cv2.COLOR_BGR2RGB)
                flipped_image = cv2.flip(image, 1)

                try:

                    if in_range:
                        cv2.rectangle(flipped_image, (rtlx, rtly), (rbrx, rbry), (25, 255, 25), 3)
                    else:
                        cv2.rectangle(flipped_image, (rtlx, rtly), (rbrx, rbry), (255, 0, 0), 3)

                except Exception as e:

                    print(f"Error: {e}")

                converted_image = QImage(flipped_image.data,
                                         flipped_image.shape[1],
                                         flipped_image.shape[0],
                                         QImage.Format.Format_RGB888)
                final_image = converted_image.scaled(790, 500, Qt.AspectRatioMode.IgnoreAspectRatio)

                self.automatic_gestures_image_update_signal.emit(final_image)

                speed = str(results[0].speed['inference'])

                try:
                    self.automatic_gestures_info_update_signal.emit(self.cap_device, self.COM, in_range, hand_class, fps, speed)
                except Exception as e:
                    print(f"Error: {e}")
        
        # Libera o acesso à câmera
        cap.release()

    def stop(self):

        with QMutexLocker(self.mutex):
            self.ThreadActive = False

        # Desaloca recursos corretamente antes de parar a Thread
        if hasattr(self, 'arm') and self.arm.isOpen():
            self.arm.close()

        self.quit()
        self.wait()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    menu_window = RoboticArmMenu()
    menu_window.show()
    try:
        sys.exit(app.exec())
    except SystemExit:
        print("Closing Window...")
