# JJY Signal Emulator by Raspberry Pico W

## 1 Introduction
This emulator can emit JJY signal at 40kHz or 60kHz <sup>[1]</sup>. It can be used to provide the synchronization signal to the clocks or the watches in case that there is no JJY signal or the JJY signal is too weak to be picked up <sup>[2]</sup>, such as in the basement of the buildings/houses or in other countries other than Japan. This emulator emits the JJY signal, which is received successfully by SEIKO SQ699W from 8 meters away.

## 2 Hardware
This emulator consists of one Raspberry Pico W, one loop antenna and one USB A to USB micro-B cable. The 2.4GHz 802.11n WiFi signal and one 5V USB power supply should be available so that the emulator can function properly. This emulator can operate around the clock automatically. The current consumption is 1.58mA most of the time because it is in the deep sleep mode <sup>[3]</sup>.  
  
If you just want to play with JJY signal and don't want to construction the hardware, you may find this web JJY is useful <sup>[4]</sup>.

### 2.1 Loop Antenna
For the low frequency signal emission, the loop antenna is a better choice than the dipole antenna because the previous has small size <sup>[5]</sup>. It is also easy to tune the impedance and radiation resistance by adding more loops or removing some loops. This emulator has an AM loop receive antenna available in market as the transmission antenna.  
  
The feed wires of the AM loop antenna is more than 3 loops long which can be transfer to the antenna loops easily by re-connecting. One wire of the twisted pair is cut off near the loops, the end connected with the loop antenna is taken as one of the new input terminals of the loop antenna, the other end then is soldered to the uncut wire so that the original twisted pair act as one whole wire now. The two original input terminals are soldered together as the other new input terminal. Winding the wire converted from the original twisted pair to the original loop to finish the loop adding. Just for reference, the number of the loops is 8+3=11. the loop antenna size is 12.5cm X 10.5cm with rounded corners.  

If the clock/watch is placed in the direction vertical to the loop antenna plane, the radiation power could be weak. Moving the clock/watch to the loop antenna plane to get more power.

### 2.2 AC Coupling
The DC resistance of the loops is 0.8 Ohm. If the loop antenna is connected to the Pico W pin directly, the output stage of Pico W could be damaged or it operates in the saturation status. To avoid this, AC coupling could be implemented between the loop antenna and Pico W. The easiest way to do so is to insert one capacitor in between. The capacitor in this emulator is 680uF/16V of electrolytic type. The anode is connected with both Pin8 and Pin9 to get more power from Pico W.  
  
One good idea is to let the loop antenna and the capacitor operates in the resonance frequency. However, since the loop antenna is fixed, the required capacitance is very small, it occupies a lot of the voltage drop, this leads to a small radiation power. The experiment shows that the JJY signal is too weak to be picked up. So, the idea of resonance is not feasible here.

### 2.3 Assembly
Pico W is small enough to be place inside the base of the loop antenna nicely. All wires can be wrapped tightly and neatly with only the USB cable sticking out.

## 3 Firmware
The firmware is written in microPython <sup>[6]</sup>. It connects the Pico W to the internet through WiFi access point, synchronizes the local time with the time server through NTP, composes and emits the JJY signal. The computer or the notebook with either windows or IOS and the software Thonny are needed to program the Pico W <sup>[7]</sup>.

### 3.1 WiFi Connection
Connecting to the WiFi access point is straight-forwarded as the example code from Raspberry website is quite useful. The only modification is to increase the waiting time to 20 seconds to get more robust coding.  
  
To save power, the WiFi module is turn off by set PIN23 to low once the local time is synchronized or in deep sleep mode.

### 3.2 Time Synchronization
The local time is synchronized through NTP <sup>[8]</sup>. The GMT time difference should be taken into account when the actual local time is extracted from the message received.

### 3.3 Time to Signal
It is a smart way to slip in the timing information to a string in the dedicated JJY format by using the string formatting feature in microPython <sup>[9]</sup>. 

### 3.4 Timing Accuracy
The JJY signal is sent from 0 second, so some timing procedures are implemented to ensure this after the Pico W wakes up from the deep sleep mode. One important thing needs to be considered is that the accuracy of the RC timer used in the deep sleep is around 3% which is not enough accurate for timing the start of the signal sending. So, setting the 10th second as the end point of the deep sleep and the 55th second as the start point of the signal sending kicks in the accurate timing function just after Pico W wakes up.  

The maximum allowed deep sleep time in Thonny is 4294 seconds. One hour (3600 seconds) is set as the deep sleep interval.  

The accuracy of the function time.localtime() is in the order of seconds, the millisecond displayed in the output of the function is always 0. The while loop is used to find the accurate timing beacon of x second 000 millisecond.

### 3.5 Carrier Frequency
In theory, the PWM pins can output either 40kHz or 60kHz carrier. However, the present hardware construction, especially the loop antenna, only emits 40kHz JJY signal which is received and recognized by SEIKO clocks successfully. One of the possible reasons could be the 40kHz carrier can be generated by dividing 125MHz by a integer ratio of 3125 and but the 60kHz carrier cannot be generated from the system frequency of 125MHz by a integer ratio.  

If the clock/watch is very near to the loop antenna, the clock/watch may recognize the 3rd harmonic of 40kHz as the 2nd harmonic of 60kHz, synchronize its time and display the west signal (60kHz) was received.
  
### 3.6 Double the Output Power
One PWM slice can drive two output pins. In this emulator, PIN8 and PIN9 are connected together to provide more power to the loop antenna. The outputs of PIN8 and PIN8 shouldn't conflict each other because they are from the same PWM slice core.  
  
### 3.7 Led Indicator
The led is connected to the WiFi module, once WiFi module is turned off by setting PIN23 to low, the led is turned off also.  
  
There are 4 led modes indicating 4 operation modes of the emulator.  
  - Always-On: Trying to connect to WiFi  
  - Slow flashing: Connected to WiFi successfully  
  - Fast flashing: Set time successfully  
  - Always-Off: Sending signal or being in deep sleep mode  

## 4 License
MIT License

## 5 Reference
[1] 標準電波（電波時計）の運用状況. https://jjy.nict.go.jp/jjy/trans/index.html  
[2] 目ざまし時計電波クロック,取扱説明書. https://www.seiko-clock.co.jp/product-personal/up_files/FSQ-155Q.pdf  
[3] Measuring the Raspberry Pi Pico W's Power Consumption - Workbench Wednesdays. https://www.youtube.com/watch?v=GqmnV_T4yAU  
[4] JJYシミュレータWeb版.https://shogo82148.github.io/web-jjy  
[5] Loop antenna. https://www.amazon.com/Bingfu-Compatible-Bluetooth-Receiver-Amplifier/dp/B07MCHJMCK/ref=sr_1_13?keywords=loop%2Bantenna&qid=1672033050&sr=8-13&th=1  
[6] MicroPython. https://www.raspberrypi.com/documentation/microcontrollers/micropython.html  
[7] Thonny https://thonny.org  
[8] aallan/picow_ntp_client.py. https://gist.github.com/aallan/581ecf4dc92cd53e3a415b7c33a1147c  
[9] snt/rpi_jjy_server. https://github.com/snt/rpi_jjy_server/blob/master/src/main/python/jjy.py  
