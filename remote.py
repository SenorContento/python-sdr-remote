#!/usr/bin/env python3

# https://pypi.org/project/pyrtlsdr/
# https://electronics.stackexchange.com/questions/115192/how-electrical-signals-converted-into-digital-binary-1-0

# Used pipreqs to generate requirements.txt.
# pip3 install pipreqs
# pipreqs .

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
    # On MacOSX: brew install librtlsdr
    # On RPi 3: sudo apt-get install librtlsdr0
    sys.exit(1)

try:
    from pylab import *
except ImportError:
    print("ImportError! Cannot import pylab!")
    # pip3 install matplotlib
    # sys.exit(1) # I disabled this because matplotlib is 36.6MB and not everyone uses a GUI.

try:
    import brewtils
except ImportError:
    None
    # print("ImportError! Cannot import brewtils!")
    # pip3 install brewtils
    # sys.exit(1) # I disabled this because I don't even use brewtils. I am still debating on if I should.

#from brewtils.decorators import system, parameter, command
#from brewtils.plugin import RemotePlugin
#import requests

#@system
class SDRKeyFob(object):
    #@parameter(key="message", description="The message to echo", type="String")
    #def say_hello(self, message="World!"):
    #    print("Hello, %s!" % message)
    #    return "Hello, %s!" % message

    def printMe(self, sdr):
        samples = sdr.read_samples(512)
        sdr.close()

        print(samples)

    def plotMe(self, sdr):
        samples = sdr.read_samples(256*1024)
        sdr.close()

        # use matplotlib to estimate and plot the PSD
        psd(samples, NFFT=1024, Fs=sdr.sample_rate/1e6, Fc=sdr.center_freq/1e6)
        xlabel('Frequency (MHz)')
        ylabel('Relative power (dB)')

        show()

    # This function isn't used
    def analogToBinary(self, array):
        return array.append(12)

    def detectButton(self, signal):
        # This doesn't work the way I want yet.
        # I have to figure out how to make this work.
        try:
            count = 0;
            for element in signal:
                #print("Element: " + str(element));
                if element == 1:
                    count = count + 1;

                if(count >= 6):
                    os.system('say "Hello"')
                    break;
        except KeyboardInterrupt:
            raise KeyboardInterrupt("Interrupted detectButton()!");

    async def streaming(self, sdr):
        try:
            global signal
            signal = [];
            async for samples in sdr.stream():
                # https://www.reddit.com/r/RTLSDR/comments/5e4gj0/how_can_i_monitor_a_single_fm_frequency_on/ - db = (10*log10(var(samples)))
                # https://www.khanacademy.org/math/ap-statistics/random-variables-ap/discrete-random-variables/v/variance-and-standard-deviation-of-a-discrete-random-variable - To Learn About Variance
                db = (10*log10(var(samples))) # https://docs.scipy.org/doc/numpy/reference/generated/numpy.var.html - np.var(samples) also works. "np.var() -> Compute the variance along the specified axis."
                #print("Decibel: " + str(db) + " Squelch: " + str(squelch))
                if(db > squelch):
                    signal.append(1);
                    print("Signal!!! Decibel: " + str(db))
                    print("Signal: " + str(signal));

                    #client.detectButton(signal);
                else:
                    signal.append(0);

                    count = 0;
                    for element in signal[-maxEmptyBinary:]:
                        if element == 0:
                            count = count + 1;
                        if count >= maxEmptyBinary:
                            signal = [];
        except KeyboardInterrupt:
            raise KeyboardInterrupt("Interrupted streaming() loop!");

                #for sample in samples:
                #    print("Real: " + str(sample.real*100)) # Check if equals 1
                #    print("Imaginary: " + str(sample.imag*100))

        # I am not sure this code ever runs...
        await sdr.stop() # to stop streaming
        sdr.close() # done

    def listen(self, sdr):
        try:
            loop = asyncio.get_event_loop()
            loop.run_until_complete(client.streaming(sdr))
        except KeyboardInterrupt:
            raise SystemExit("Stopped Listening for the Remote Signal!");

# Added a Proper Entry Point I Guess
if __name__ == "__main__":
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
    squelch = -10.0 # This is different than the Gqrx squelch level of -40
    offset = measured - freq

    maxEmptyBinary = 10 # For deciding when to reset the signal tracker

    print();
    print("Wanted Frequency: " + (str) (trunc(freq)) + " Hz! Actual Frequency: " + (str) (trunc(measured)) + " Hz!");
    print("Offset: {0:0.0f} and Squelch: {1}".format(offset, squelch)); # Trunc does not want to cooperate with offset for some reason...
    print();

    #sys.exit()

    sdr.sample_rate = 2.048e6 # Hz - Sample Rate is the number of samples of audio carried per second. (https://manual.audacityteam.org/man/sample_rates.html)
    sdr.center_freq = measured # Hz
    sdr.freq_correction = 60 # PPM - I Don't Know How This is Set - Something to Do With rtl_test -p 10
    sdr.gain = 'auto'

    try:
        client = SDRKeyFob()
        #plugin = RemotePlugin(client,
        #                  name="hello",
        #                  version="0.0.1",
        #                  bg_host='127.0.0.1',
        #                  bg_port=2337)
        #plugin.run()
        client.listen(sdr);
        #client.printMe(sdr);
        #client.plotMe(sdr); # Great for Debugging
    except SystemExit as error:
        print('\n' + str(error)); #repr(error)
        os._exit(2); # I want a cleaner way of exiting than this. - Error in atexit._run_exitfuncs: (Related to "python3.7/concurrent/futures/thread.py", line 40, in _python_exit)
    #except requests.exceptions.ConnectionError as error:
    #    print("Cannot Connect to Brewtils Server: " + str(error));