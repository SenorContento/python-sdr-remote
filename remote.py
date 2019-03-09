#!/usr/bin/env python3

# https://pypi.org/project/pyrtlsdr/

try:
    import sys
except ImportError:
    print("ImportError! Cannot import sys!")

try:
    assert sys.version_info >= (3, 0)
except AssertionError:
    print("AssertionError! You need to use Python 3.x+!")
    sys.exit()

try:
    from math import trunc
except ImportError:
    print("ImportError! Cannot import trunc from math!")
    sys.exit()

try:
    import asyncio
except ImportError:
    print("ImportError! Cannot import asyncio!")
    sys.exit()

try:
    from rtlsdr import RtlSdr
except ImportError:
    print("ImportError! Cannot import RtlSdr from rtlsdr!")
    print("Did you install librtlsdr?")
    # pip3 install pyrtlsdr
    # brew install librtlsdr
    sys.exit()

try:
    from pylab import *
except ImportError:
    print("ImportError! Cannot import pylab!")
    # pip3 install matplotlib
    sys.exit()

# Start SDR
try:
    sdr = RtlSdr()
except OSError:
    print("Could Not Find RTLSDR!!! Is It Locked???");
    sys.exit()

# configure device
measured = 314873e3 # Hz - 314,873.000 kHz
freq = 315e6 # Hz - 315,000.000 kHz
squelch = 60 # Potentional Squelch Level is -40.0
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
    async for samples in sdr.stream():
        for sample in samples:
            #print("Real: " + str(sample.real*100))
            
            # This works, but it also can produce inteference that I cannot silence if I pick up
            # the antenna with my hand. I can disable the inteference in Gqrx by using Squelch
            if(sample.real == 1):
                if((sample.imag*100) > squelch): # Squelchish Value? It it out of 100...
                    print("Imaginary: " + str(sample.imag*100))

    # to stop streaming:
    await sdr.stop()

    # done
    sdr.close()

def listen(sdr):
    loop = asyncio.get_event_loop()
    loop.run_until_complete(streaming(sdr))

listen(sdr);
#printMe(sdr);
#plotMe(sdr); # Great for Debugging