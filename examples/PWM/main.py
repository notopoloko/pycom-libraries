from machine import PWM
import time

pwm = PWM(0, frequency=5000)  # use PWM timer 0, with a frequency of 5KHz
# create pwm channel on pin P11 with a duty cycle of 50%
pwm_c = pwm.channel(0, pin='P11', duty_cycle=0.5)
incVal = 0.5
valToSum = 0.05
# Faz o led alterar o brilho
i = 10000000000
while i > 0:
    pwm_c.duty_cycle( incVal ) # change the duty cycle to 50%
    time.sleep(.05)

    if incVal >= 1 :
        valToSum = -valToSum
    elif incVal <= 0 :
        valToSum = -valToSum

    incVal += valToSum
    i -= 1
