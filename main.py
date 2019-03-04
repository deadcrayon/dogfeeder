import machine, time, sys, network
from machine import Pin

# ADC pin - (0 on ESP8266)
adc = machine.ADC(0)

# Stepper driver Dir pin
dir = Pin(14, Pin.OUT)

# Stepper driver Pulse pin
pulse = Pin(12, Pin.OUT)

# Stepper driver Ena Pin
enable = Pin(13, Pin.OUT)

# Turn stepper off
enable.value(1)

# Set current attempt
attempts = [1]

# Step iteration array for laser sensor
steps = [0]

# delay for stepper motor
delay = 0.00035

# adjust these values based on your own adc readings..
# ----------------------------------------------------

# number of steps to check for food
watch_interval = 50

# how long to run the feed screw for
feed_length = 15500

# max amount of time between laser trips
max_empty_time = 2000

# set this to 10 below average (ADC value / 2) when nothing is blocking the sensor
adc_sensitivity = 50

# max number of times to retry if laser continues to not trip
max_retries = 5


# perform check to make sure laser is picking up correctly
def start():
    if round(adc.read() / 2) <= adc_sensitivity:
        print('ADC value is low during startup!\nPlease adjust sensitivity or check sensor for blockage.')
        sys.exit(1)
    return True


# just a test method
def adc_test():
    for i in range(500):
        print(adc.read() / 2)
        time.sleep(0.5)


# check adc value and append steps to array if "food is detected"
def check_adc(x):
    val = adc.read() / 2
    if val <= adc_sensitivity:
        steps.append(x)
    return True


# generic pin value wrapper
def set_pin(pin, val):
    pin.value(int(val))
    return True


# check attempt count and then reverse feed screw, run manual method for remaining steps
def unjam(i):
    if len(attempts) >= max_retries:
        sys.exit(1)
    attempts.append(1)
    prime()
    manual(feed_length - i)
    return True


# run feed screw in reverse to clear and unjam any resting food
def prime():
    start()
    set_pin(enable, 0)
    for i in range(4000):
        set_pin(dir, 0)
        set_pin(pulse, 1)
        time.sleep(delay)
        set_pin(pulse, 0)
        time.sleep(delay)
    return True


# run the feed screw, monitoring the adc value for "food moving"
def feed():
    attempts[:] = [1]
    steps[:] = [0]
    for i in range(feed_length):
        set_pin(dir, 1)
        set_pin(pulse, 1)
        time.sleep(delay)
        set_pin(pulse, 0)
        time.sleep(delay)
        if i % watch_interval == 0:
            check_adc(i)
            if i-steps[-1] >= max_empty_time:
                clear_stepper()
                unjam(i)
                break

    time.sleep(0.05)
    clear_stepper()
    return True


# clear the stepper motor
def clear_stepper():
    set_pin(enable, 1)
    return True


# manual method to enable stepper
def power_on():
    set_pin(enable, 0)
    return True


# manual method called after unjam attempt
def manual(s):
    print("Running manual for remaining " + str(s))
    for i in range(s):
        set_pin(dir, 1)
        set_pin(pulse, 1)
        time.sleep(delay)
        set_pin(pulse, 0)
        time.sleep(delay)
        if i % watch_interval == 0:
            check_adc(i)
            if i-steps[-1] >= max_empty_time:
                clear_stepper()
                unjam(i)
                break
    time.sleep(0.05)
    clear_stepper()
    return True
