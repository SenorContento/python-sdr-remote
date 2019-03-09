#!/usr/bin/env python3

# https://pypi.org/project/pyrtlsdr/

try:
    import sys
except ImportError:
    print("ImportError! Cannot import sys!")
    exit(1) # Obviously I cannot use sys.exit() if I cannot import sys...

try:
    assert sys.version_info >= (3, 0)
except AssertionError:
    print("AssertionError! You need to use Python 3.x+!")
    sys.exit(1)

try:
    import os
except ImportError:
    print("ImportError! Cannot import os!")
    sys.exit(1)

try:
    from math import trunc
except ImportError:
    print("ImportError! Cannot import trunc from math!")
    sys.exit(1)

try:
    import asyncio
except ImportError:
    print("ImportError! Cannot import asyncio!")
    sys.exit(1)

try:
    from rtlsdr import RtlSdr
except ImportError:
    print("ImportError! Cannot import RtlSdr from rtlsdr!")
    print("Did you install librtlsdr?")
    # pip3 install pyrtlsdr
    # brew install librtlsdr
    sys.exit(1)

try:
    from pylab import *
except ImportError:
    print("ImportError! Cannot import pylab!")
    # pip3 install matplotlib
    sys.exit()

# Start SDR
try:
    device = 0;

    # Get a list of detected device serial numbers (str)
    devices = RtlSdr.get_device_serial_addresses()
    print("Devices: " + str(devices));
    if len(devices) is 0: raise Exception("No Detected RTLSDR Devices!!!");
    # Find the device index for a given serial number
    device_index = RtlSdr.get_device_index_by_serial(devices[device]) # You can insert your Serial Address (as a string) directly here
    sdr = RtlSdr(device_index)
    #sdr = RtlSdr() # If you don't have more than 1 device, this will work fine.
except OSError:
    print("Could Not Find RTLSDR!!! Is It Locked???");
    sys.exit(2)
except IndexError:
    print("Choose a Valid Device ID!!!");
    sys.exit(2)
except Exception as error:
    print("I Cannot Find A RTLSDR!!!");
    sys.exit(2)

# configure device
measured = 314873e3 # Hz - 314,873.000 kHz
freq = 315e6 # Hz - 315,000.000 kHz
squelch_fake = 60 # Potentional Squelch Level is -40.0
squelch = -5.0 # This is different than the Gqrx squelch level of -40
offset = measured - freq
print("Wanted Frequency: " + (str) (trunc(freq)) + " Hz! Actual Frequency: " + (str) (trunc(measured)) + " Hz!");
print("Offset: {:0.0f}".format(offset)); # Trunc does not want to cooperate with offset for some reason...

#sys.exit()

sdr.sample_rate = 2.048e6 # Hz - Sample Rate is the number of samples of audio carried per second. (https://manual.audacityteam.org/man/sample_rates.html)
sdr.center_freq = measured # Hz
sdr.freq_correction = 60 # PPM - I Don't Know How This is Set - Something to Do With rtl_test -p 10
sdr.gain = 'auto'

def printMe(sdr):
    samples = sdr.read_samples(512)
    sdr.close()

    print(samples)

def plotMe(sdr):
    samples = sdr.read_samples(256*1024)
    sdr.close()

    # use matplotlib to estimate and plot the PSD
    psd(samples, NFFT=1024, Fs=sdr.sample_rate/1e6, Fc=sdr.center_freq/1e6)
    xlabel('Frequency (MHz)')
    ylabel('Relative power (dB)')

    show()

async def streaming(sdr):
    try:
        async for samples in sdr.stream():
            db = (10*log10(var(samples))) # https://docs.scipy.org/doc/numpy/reference/generated/numpy.var.html - np.var(samples) also works. "np.var() -> Compute the variance along the specified axis."
            #print("Decibel: " + str(db) + " Squelch: " + str(squelch))
            if(db > squelch):
                print("Signal!!! Decibel: " + str(db))

            # The three single quotes act as a multiline comment.
            # Just comparing the decibel is so much easier than the below code
            # and I don't have the problem of inteference from picking up the antenna
            '''
            for sample in samples:
                #print("Real: " + str(sample.real*100))

                # This works, but it also can produce inteference that I cannot silence if I pick up
                # the antenna with my hand. I can disable the inteference in Gqrx by using Squelch
                if(sample.real == 1 && False):
                    # https://www.reddit.com/r/RTLSDR/comments/5e4gj0/how_can_i_monitor_a_single_fm_frequency_on/ - db = (10*log10(var(samples)))
                    # https://www.khanacademy.org/math/ap-statistics/random-variables-ap/discrete-random-variables/v/variance-and-standard-deviation-of-a-discrete-random-variable - To Learn About Variance
                    #db = (10*log10(var(samples))) # https://docs.scipy.org/doc/numpy/reference/generated/numpy.var.html - np.var(samples) also works. "np.var() -> Compute the variance along the specified axis."
                    #print("Decibel: " + str(db))
                    if((sample.imag*100) > squelch_fake):# and db > -10): # Squelchish Value? It it out of 100...
                        print("Imaginary: " + str(sample.imag*100))
            '''
    except KeyboardInterrupt:
        print("Stopped Listening for the Remote Signal!")

    # to stop streaming:
    await sdr.stop()

    # done
    sdr.close()

def listen(sdr):
    try:
        loop = asyncio.get_event_loop()
        loop.run_until_complete(streaming(sdr))
    except KeyboardInterrupt:
        # This should only be called if something happened to the
        # RTLSDR's Signal, like the RTLSDR was unplugged during runtime.

        #print("Received Exit!")
        #return
        raise SystemExit("Signal Stopped and KeyboardInterrupt Occurred!!!");

try:
    listen(sdr);
    #printMe(sdr);
    #plotMe(sdr); # Great for Debugging
except SystemExit as error:
    print("Shutting Down! Reason: \"" + str(error) + "\"") #repr(error)
    os._exit(2); # I want a cleaner way of exiting than this.
    #sys.exit(2);
    # Current Problems
    # Error in atexit._run_exitfuncs: (Related to "python3.7/concurrent/futures/thread.py", line 40, in _python_exit)