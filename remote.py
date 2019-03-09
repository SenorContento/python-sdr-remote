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
sdr.sample_rate = 2.048e6   # Hz - Sample Rate is the number of samples of audio carried per second. (https://manual.audacityteam.org/man/sample_rates.html)
sdr.center_freq = 314873000 # Hz - 314,873.000 kHz
sdr.freq_correction = 60    # PPM
# Figure Out How To Squelch (-40.0)
#sdr.gain = 'auto'

squelch = -40.0

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
            if(sample.real == 1):
                if((sample.imag*100) > 90): # Squelchish Value? It it out of 100...
                    print(sample.imag*100)

    # to stop streaming:
    await sdr.stop()

    # done
    sdr.close()

def listen(sdr):
    loop = asyncio.get_event_loop()
    loop.run_until_complete(streaming(sdr))

listen(sdr);
#printMe(sdr);
#plotMe(sdr);