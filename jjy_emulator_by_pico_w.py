###############################################################################
#   JJY emulator by Raspberry Pico W
#   Version date: 20 Dec 2022
#
#   print() and RuntimeError() are commented for actual firmware
#   led.*() is commented in broadcasting() for the actual firmware
#
#   Received successfully by SEIKO SQ699W and SQ443S(2.71ppm)
#
###############################################################################
#   import modules
#   https://docs.micropython.org/en/latest/library/<...>.html
###############################################################################
from machine import Pin
from machine import PWM
from machine import RTC
from machine import freq
from machine import deepsleep
import time
import network
import socket
import struct
###############################################################################
#   function, wlan_connect
# Return value of cyw43_wifi_link_status
# define CYW43_LINK_DOWN (0)
# define CYW43_LINK_JOIN (1)
# define CYW43_LINK_NOIP (2)
# define CYW43_LINK_UP (3)
# define CYW43_LINK_FAIL (-1)
# define CYW43_LINK_NONET (-2)
# define CYW43_LINK_BADAUTH (-3)
###############################################################################
def wlan_connect(ssid, password):
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    wlan.connect(ssid, password)

    # Wait for connect or fail
    max_wait = 20
    while max_wait > 0:
        if wlan.status() < 0 or wlan.status() >= 3:
            break
        max_wait -= 1
        #print('waiting for connection...')
        time.sleep(1)

    # Handle connection error
    if wlan.status() != 3:
        #raise RuntimeError('network connection failed')
        return 1
    else:
        #print('wifi connected')
        status = wlan.ifconfig()
        #print( 'ip = ' + status[0] )
        return 0
###############################################################################
#   function, wlan_disconnect
###############################################################################
def wlan_disconnect():
    wlan = network.WLAN(network.STA_IF)
    wlan.active(False)
    # turn off WiFi module,led is also off since led is connected to WL_GPIO0
    # the following command must be executed before deepsleep()
    machine.Pin(23, machine.Pin.OUT).low()
    #print('wifi disconnected')
    return 0
###############################################################################
#   function, set_time()
#   aallan/picow_ntp_client.py
#   https://gist.github.com/aallan/581ecf4dc92cd53e3a415b7c33a1147c
###############################################################################
def set_time():
    NTP_DELTA = 2208988800 - 8*3600 # subtract 8 hour to get GMT + 8 for Singapore
    host = "sg.pool.ntp.org"        # using host from Singapore

    NTP_QUERY = bytearray(48)
    NTP_QUERY[0] = 0x1B
    
    try:
        addr = socket.getaddrinfo(host, 123)[0][-1]
 
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.settimeout(1)    # in seconds
        res = s.sendto(NTP_QUERY, addr)
        msg = s.recv(48)
        s.close()
        
        msg_received = 1
    except OSError:
        msg_received = 0
    finally:
        if msg_received == 1:
            val = struct.unpack("!I", msg[40:44])[0]
            t = val - NTP_DELTA    
            tm = time.gmtime(t)
            machine.RTC().datetime((tm[0], tm[1], tm[2], tm[6] + 1, tm[3], tm[4], tm[5], 0))
            #print('time set')
            return 0
        else:
            #print('time setting unsuccessful')        
            return 1
###############################################################################
#   function, time_to_signals
#   JJY Format
#   標準電波（電波時計）の運用状況
#   https://jjy.nict.go.jp/jjy/trans/index.html
#   snt/rpi_jjy_server
#   https://github.com/snt/rpi_jjy_server/blob/master/src/main/python/jjy.py
###############################################################################
def time_to_signals(timetuple):
    JJY_FORMAT="M{0:03b}0{1:04b}M00{2:02b}0{3:04b}M00{4:02b}0{5:04b}M{6:04b}00{7:01b}{8:01b}0M0{9:04b}{10:04b}M{11:03b}000000M"

    # (year, month, mday, hour, minute, second, weekday, yearday)
    # weekdays = {0:"Monday", 1:"Tuesday", 2:"Wednesday", 3:"Thursday", 4:"Friday", 5:"Saturday", 6:"Sunday"}
    sYear   = "{:>02}".format(timetuple[0] - 2000)    # > : right aligned
    sHour   = "{:>02}".format(timetuple[3])
    sMinute = "{:>02}".format(timetuple[4])
    sSecond = "{:>02}".format(timetuple[5])
    sWeek   = "{:>01}".format((timetuple[6]+1) % 7)
    sDay    = "{:>03}".format(timetuple[7])

    PA1 = str("".join(["{:b}".format(int(x)) for x in sHour]).count('1') % 2)
    PA2 = str("".join(["{:b}".format(int(x)) for x in sMinute]).count('1') % 2)

    data = sMinute + sHour + sDay + PA1 + PA2 + sYear + sWeek
    signals = JJY_FORMAT.format(*[int(x) for x in data])    # * : unpacking argument sequence
    return signals
###############################################################################
#   function, send_signals\
#   snt/rpi_jjy_server
#   https://github.com/snt/rpi_jjy_server/blob/master/src/main/python/jjy.py
###############################################################################
def send_signals(signals):
    # M 200 [ms]
    # 1 500 [ms]
    # 0 800 [ms]
    SIGNAL_LENGTHS = {'M': 200, '1': 500, '0': 800}

    for i, signal in enumerate(signals):
        pwm8.duty_u16(32768)                          # set duty to 50%
        pwm9.duty_u16(32768)                          # set duty to 50%
        time.sleep_ms(SIGNAL_LENGTHS[signal])         # wait for signal length
        pwm8.duty_u16(0)                              # no output
        pwm9.duty_u16(0)                              # no output
        if i == 59:
            timetuple = next_minute()                 # time for next minute
        time.sleep_ms(1000-SIGNAL_LENGTHS[signal])    # wait for remain of the signal length

    return timetuple
###############################################################################
#   function, next_minute
###############################################################################
def next_minute():
    timenow = time.localtime()
    timenext = time.localtime(time.mktime(timenow)+60)    # time for next minute
    timelist = list(timenext)
    timelist[5] = 0                                       # set second = 0
    timetuple = tuple(timelist)
    return timetuple
###############################################################################
#   function, sleep_time
#   目ざまし時計電波クロック,取扱説明書
#   https://www.seiko-clock.co.jp/product-personal/up_files/FSQ-155Q.pdf
###############################################################################
def sleep_time(timetuple):
    send_hours = [2,5,8,11,14,17,20,23]    # SEIKO clocks sync at these hours

    Minute_start  = 58
    Minute_stop   =  8
    Second_margin = 10

    Hour   = timetuple[3]
    Minute = timetuple[4]

    if (Hour+1) in send_hours:
        if Minute > Minute_start:
            sleep_second = 0
        else:
            timenow  = timetuple
            # set target time
            timelist = list(timetuple)
            timelist[4] = Minute_start     # set minute
            timelist[5] = Second_margin    # set second margin
            sleep_second = time.mktime(tuple(timelist)) - time.mktime(timenow)
    elif Hour in send_hours:
        if Minute < Minute_stop:
            sleep_second = 0
        else:
            timenow  = timetuple
            # set target time
            timelist = list(timetuple)
            timelist[3] = Hour + 2      # set hour
            timelist[4] = Minute_start  # set minute
            timelist[5] = Second_margin    # set second margin
            sleep_second = time.mktime(tuple(timelist))- time.mktime(timenow)
    else:
            timenow  = timetuple
            # set target time
            timelist = list(timetuple)
            timelist[3] = Hour + 1      # set hour
            timelist[4] = Minute_start  # set minute
            timelist[5] = Second_margin    # set second margin
            sleep_second = time.mktime(tuple(timelist))- time.mktime(timenow)

    return sleep_second
###############################################################################
#   function, wait_until_next_minute
###############################################################################
def wait_until_next_minute():
    # find x second 000 millisecond
    timenow = time.localtime()
    second_next = timenow[5] + 1
    found_ms = 0
    while found_ms < 3:                # calibrate by 3 seconds
        timenow = time.localtime()
        if timenow[5] == second_next:
            found_ms    += 1
            second_next += 1
    
    timethis = time.mktime(timenow)                       # time for now
    
    timenext = time.localtime(time.mktime(timenow)+60)    # time for next minute
    timelist = list(timenext)
    timelist[5] = 0                                       # set second = 0
    time_boundary = time.mktime(tuple(timelist))          # time at next minute boundary
    time_in_ms = 1000*(time_boundary - timethis)          # in ms
    
    time.sleep_ms(time_in_ms)
    return 0
#################################################################################
#   function, broadcasting
#################################################################################
def broadcasting( nowait = False ):
    Minute_start = 58
    Minute_stop  =  8

    if nowait == True:
        sleep_time_second = 0
    else:
        timenow = time.localtime()
        sleep_time_second = sleep_time(timenow)

    # send signals
    if sleep_time_second <= 0:
        # find the middle of the minute
        #print('finding 55th second')
        middle_minute = False
        while middle_minute == False:
            timenow = time.localtime()
            if timenow[5] == 55:
                middle_minute = True
        #print('55th second found')

        # waiting for the 1st sending
        signals = time_to_signals(next_minute())
        wait_until_next_minute()

        # Continouse sending
        #print('sending signal')
        #led.on()    # for debug
        send_enable = True
        while send_enable:
            timetuple = send_signals(signals)
            if (timetuple[4] < Minute_stop) or (timetuple[4] > Minute_start):
                signals = time_to_signals(timetuple)
                #led.toggle()    # for debug
            else:
                timenow = time.localtime()
                sleep_time_second = sleep_time(timenow)
                #led.off()       # for debug
                send_enable = False
                
    return sleep_time_second
###############################################################################
#   function, led_toggle
###############################################################################
def led_toggle(interval, number):
    i = 0
    while i < number:
        led.on()
        time.sleep_ms(interval)
        led.off()
        time.sleep_ms(interval)
        i += 1

    return 0
###############################################################################
# Setup
#################################################################################
# Set led
led = machine.Pin("LED", machine.Pin.OUT)

# Set output pin
pwm8 = machine.PWM(Pin(8))    # create a PWM object on Pin 8
pwm9 = machine.PWM(Pin(9))    # create a PWM object on Pin 9
pwm8.freq(40_000)             # set frequency to 40kHz (West:60kHz, East:40kHz)
pwm9.freq(40_000)             # set frequency to 40kHz (West:60kHz, East:40kHz)

# Set WiFi parameters
ssid = 'your_ssid'
password = 'your_password'

# Check frequency
machine.freq()*1E-6        # system frequency = 125MHz, period = 800ns

# Set deep sleep
deepsleep_max_period = 3600    # Thonny deepsleep allowed max = 4294 seconds
#################################################################################
# Operations
#################################################################################
sleep_time_second = deepsleep_max_period

# Connect to WiFi
led.on()    # led on during wifi operation period
wlan_status = wlan_connect(ssid, password)
led.off()   # led on during wifi operation period

if wlan_status == 0:
    led_toggle(100,10)    # toggle quickly if wifi connected successful
    # Sync time with ntp server
    set_time_status = set_time()
    led_toggle(500,3)    # toggle slowly if time set successful
    wlan_disconnect()

    if set_time_status == 0:
        sleep_time_second = broadcasting()
        if sleep_time_second > deepsleep_max_period:
            sleep_time_second = deepsleep_max_period

# deep sleep
#print('sleep time = ' + str(sleep_time_second) +'s')
# Current = 1.58mA in deep sleep mode
# Measuring the Raspberry Pi Pico W's Power Consumption - Workbench Wednesdays
# https://www.youtube.com/watch?v=GqmnV_T4yAU
machine.Pin(23, machine.Pin.OUT).low()        # must be executed before deepsleep()
machine.deepsleep(sleep_time_second *1000)    # in millisecond
#################################################################################
