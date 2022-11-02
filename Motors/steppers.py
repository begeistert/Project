# steppers.py

# this has 2 classes
#   HBRIDGE - for using h-bridges
#   A4899 - for using a4899 stepper drivers (and similar)

# -----------------------------------------------
# imports
# -----------------------------------------------

import time
from machine import Pin


# -----------------------------------------------
# h-bridge stepper driver class
# -----------------------------------------------

class HBRIDGE:    
    # this performs and tracks steps on a single motor with quad-h-bridge
    # this required 4 controller pins per motor

    # for bipolar steppers, the 2 coils are A-->a and B-->b

    # for uni-polar steppers, the 4 coils are A-->G, B-->G, a-->G, and b-->G
    # where G is ground (default condition, but see invert=True)

    # default is to use pin HIGH == h-bridge channel ON
    # if LOW == h-bridge channel ON, set invert=True on init

    # -----
    # modes
    # -----

    # all modes are set up as (A,B,a,b) (easier for viewing)
    # for bipolar motors A-a and B-b are the 2 coils
    # for uni-polar motors A, B, a, and b are the 4 coils

    # full-step, single coil, 4-state
    mode1 = ((1, 0, 0, 0),
             (0, 1, 0, 0),
             (0, 0, 1, 0),
             (0, 0, 0, 1))

    # full-step, dual coil, 4-state
    mode2 = ((1, 1, 0, 0),
             (0, 1, 1, 0),
             (0, 0, 1, 1),
             (1, 0, 0, 1))

    # half-step, single and dual coil, 8-state
    mode3 = ((1, 1, 0, 0),
             (0, 1, 0, 0),
             (0, 1, 1, 0),
             (0, 0, 1, 0),
             (0, 0, 1, 1),
             (0, 0, 0, 1),
             (1, 0, 0, 1),
             (1, 0, 0, 0))

    # -----
    # init
    # -----

    def __init__(self,
                 A,  # pin number for coil A
                 a,  # pin number for coil a
                 B,  # pin number for coil B
                 b,  # pin number for coil b
                 mode=1,  # see modes above
                 reverse=False,  # reverse motor default direction
                 invert=False,  # invert all mode pin states
                 sleep=False,  # start in sleep mode
                 sps=200,  # steps-per-second
                 smax=10240,  # max step count allowed
                 smin=-10240  # min step count allowed
                 ):

        # set mode (delete others)
        if mode == 3:
            self.mode = self.mode3
            self.mode1, self.mode2 = None, None
        elif mode == 2:
            self.mode = self.mode2
            self.mode1, self.mode3 = None, None
        else:
            self.mode = self.mode1
            self.mode2, self.mode3 = None, None
        self.index = 0  # index of current state
        self.imax = len(self.mode) - 1  # when to loop index

        # set reverse (just reverse self.mode)
        if reverse:
            # not for micropython: self.mode = self.mode[::-1]
            mode = list(self.mode)
            mode.reverse()
            self.mode = tuple(mode)

        # set invert mode and xstate (off state)
        self.xstate = (0, 0, 0, 0)
        if invert:
            mode = []
            for state in self.mode:
                pins = []
                for pin in state:
                    if pin:
                        pins.append(0)
                    else:
                        pins.append(1)
                mode.append(tuple(pins))
            self.mode = tuple(mode)
            del mode
            self.xstate = (1, 1, 1, 1)

        # set sleep and init state
        if sleep:
            self.isoff = True
            istate = self.xstate
        else:
            self.isoff = False
            istate = self.mode[self.index]

        # pin init
        self.p1 = Pin(A, Pin.OUT, istate[0])
        self.p2 = Pin(B, Pin.OUT, istate[1])
        self.p3 = Pin(a, Pin.OUT, istate[2])
        self.p4 = Pin(b, Pin.OUT, istate[3])

        # step tracking
        self.steps = 0  # current step count
        self.last = time.ticks_us()  # ticks_us of last pset
        self.sps = int(sps or 200)  # default steps per second
        self.smax = smax
        self.smin = smin

    def zero(self):
        self.steps = 0

    def sleep(self):
        self.pset(self.xstate)
        self.isoff = True

    def wake(self):
        self.pset(self.mode[self.index])
        self.isoff = False

    def pset(self, state, waitfor=None):
        while waitfor and time.ticks_diff(time.ticks_us(), waitfor) < 0:
            time.sleep_us(10)
        self.p1.value(state[0])
        self.p2.value(state[1])
        self.p3.value(state[2])
        self.p4.value(state[3])
        self.last = time.ticks_us()

    def step(self, steps, sps=None, sleep=False):

        # limit steps
        # steps = min(steps,self.smax-self.steps)
        # steps = max(steps,self.smin-self.steps)
        steps = min(max(steps, self.smin - self.steps), self.smax - self.steps)

        # mode localize
        mode = self.mode
        imax = self.imax

        # local tracking
        index = self.index  # most recent index
        sc = 0  # step count

        # accurate timing
        stime = int(round(1000000 / max(1, (sps or self.sps)), 0))
        #                 (   timenow -                  (lastpset + stime)) >= 0:
        if time.ticks_diff(time.ticks_us(), time.ticks_add(self.last, stime)) >= 0:
            waitfor = time.ticks_us()
        else:
            waitfor = time.ticks_add(self.last, stime)

        # wake
        if self.isoff:
            self.wake()

        # backward
        if steps < 0:
            for s in range(abs(steps)):
                if index == 0:
                    index = imax
                else:
                    index -= 1
                self.pset(mode[index], waitfor)
                waitfor = time.ticks_add(waitfor, stime)
                sc -= 1

        # forward
        else:
            for s in range(steps):
                if index == imax:
                    index = 0
                else:
                    index += 1
                self.pset(mode[index], waitfor)
                waitfor = time.ticks_add(waitfor, stime)
                sc += 1

        # sleep
        if sleep:
            self.sleep()

        # done
        self.index = index
        self.steps += sc
        return self.steps

    def beepbeep(self, freq=880, sleep=False):
        self.beep(freq, 100, 100, sleep)
        self.beep(freq, 100, 100, sleep)

    def beep(self, freq=440, time_ms=250, pause=0, sleep=False):

        # determine steps based on freq and period
        stime = int(round(500000 / max(1, freq), 0))  # 500000 is divide-by-2 (each step is a forward and back)
        steps = int(round(time_ms * 500 / stime, 0))  # 500 is divide-by-2 (each step is a forward and back)

        # timing setup (see step() for details)
        if time.ticks_diff(time.ticks_us(), time.ticks_add(self.last, stime)) >= 0:
            waitfor = time.ticks_us()
        else:
            waitfor = time.ticks_add(self.last, stime)

        # get states
        cstate = self.mode[self.index]
        if self.index == self.imax:
            nstate = self.mode[0]
        else:
            nstate = self.mode[self.index + 1]

        # wake
        if self.isoff:
            self.wake()

        # step forward and back
        for s in range(steps):
            # forward
            self.pset(nstate, waitfor)
            waitfor = time.ticks_add(waitfor, stime)

            # back
            self.pset(cstate, waitfor)
            waitfor = time.ticks_add(waitfor, stime)

            # sleep
        if sleep:
            self.sleep()

        # pause
        if pause:
            time.sleep_ms(pause)

        # done
        return self.steps

    # note strings
    jingle = 'e5 g5 b5 d6 p d5'
    jingle2 = 'd7'
    shave = 'c4 p g3 g3 a32 g32 p p b3 p c4'
    axelf = 'd44 f43 d42 d41 g42 d42 c42 d44 a43 d42 d41 a#42 a42 f42 d42 a42 d52 d41 c42 c41 a32 e42 d46'  # smash 3

    def play(self, notestring, root=440, beat=0.125, sleep=False):

        # notestring = any string of a note+optional_sharp+octave+beats sequences
        # only "ABCDEFGP#0123456789" characters matter, others ignored
        # example: "d44" == "D44" == "d 4 4" == "d, 4, 4" == "D4-4"
        # example: "d44 a43 d42 d41 a#42 a42 f42"
        # example: "d44a43d42d41a#42a42f42"

        # middle C for 3 beats = 'C43'
        # a pause for 3 beats = 'P3' or 'P03'

        # upper case
        notestring = notestring.upper()

        # all strings
        note, octave, period = '', '', ''

        for c in notestring:

            # note
            if c in 'ABCDEFGP':
                if note:
                    self.play_note(note, octave or '4', period or '1', root, beat)
                    octave, period = '', ''
                note = c

            # sharp
            elif c == '#' and note:  # smash 3
                note += '#'  # smash 3

            # digit
            elif c.isdigit():

                # period
                if octave or note == 'P':
                    period += c

                # octave
                else:
                    octave = c

            # junk
            else:
                pass

        # last note
        if note:
            self.play_note(note, octave or '4', period or '1', root, beat)

        # sleep
        if sleep:
            self.sleep()

    def play_note(self, note, octave, period, root, beat):

        # catch
        try:

            freq, pixel = {
                'C': (16.35160, 7),
                'C#': (17.32391, 7),  # smash 3
                'D': (18.35405, 6),
                'D#': (19.44544, 6),  # smash 3
                'E': (20.60172, 5),
                'F': (21.82676, 4),
                'F#': (23.12465, 3),  # smash 3
                'G': (24.49971, 2),
                'G#': (25.95654, 2),  # smash 3
                'A': (27.50000, 1),
                'A#': (29.13524, 1),  # smash 3
                'B': (30.86771, 0)
            }.get(note, (None, None))

            period = abs(int(period))
            octave = abs(int(octave))

            if freq:
                freq *= root / 440 * 2 ** octave
                self.beep(freq, 1000 * period * beat * 0.95)
                time.sleep_ms(int(period * beat * 50))

            else:
                time.sleep_ms(int(period * beat * 1000))

        # any error
        except Exception as e:
            import sys
            sys.print_exception(e)


# -----------------------------------------------
# a4899 stepper driver class
# -----------------------------------------------

class A4899(HBRIDGE):
    # re-use as much of HBRIDGE as possible
    # keep all the function names the same

    # disable value (sleep = disable)
    sleepis = 1

    def __init__(self,
                 step,  # pin number for step
                 direction,  # pin number for direction
                 enable=None,  # pin number for enable
                 reverse=False,  # reverse motor default direction
                 sleep=False,  # start in sleep mode
                 sps=200,  # steps-per-second
                 smax=0,  # max step count allowed
                 smin=0  # min step count allowed
                 ):

        # no modes (set by dip switch)
        self.mode1, self.mode2, self.mode3 = None, None, None

        # direction
        if reverse:
            self.forward = 1
            self.reverse = 0
        else:
            self.forward = 0
            self.reverse = 1

        # pin init
        self.ps = Pin(step, Pin.OUT, 0)
        self.pd = Pin(direction, Pin.OUT, self.forward)
        if type(enable) == int:
            self.pe = Pin(enable, Pin.OUT, 0)
        else:
            self.pe = None

        # set sleep and init state
        if sleep:
            self.sleep()
        else:
            self.wake()

        # step tracking
        self.steps = 0  # current step count
        self.last = time.ticks_us()  # ticks_us of last pset
        self.sps = int(sps or 200)  # default steps per second
        self.smax = smax
        self.smin = smin
        self.stop = False  # stop flag
        self.running = False  # running flag

    def sleep(self):
        self.pe.value(self.sleepis)
        self.isoff = True

    def wake(self):
        if self.sleepis:
            self.pe.value(0)
        else:
            self.pe.value(1)
        self.isoff = False

    def step(self, steps, sps=None, sleep=False):

        self.running = True
        # limit steps
        # steps = min(steps,self.smax-self.steps)
        # steps = max(steps,self.smin-self.steps)
        if self.smax > 0 and self.smin:
            steps = min(max(steps, self.smin - self.steps), self.smax - self.steps)

        # local tracking
        sc = 0  # step count

        # accurate timing
        stime = int(round(1000000 / max(1, (sps or self.sps)), 0))
        #                 (   timenow -                  (lastpset + stime)) >= 0:
        if time.ticks_diff(time.ticks_us(), time.ticks_add(self.last, stime)) >= 0:
            waitfor = time.ticks_us()
        else:
            waitfor = time.ticks_add(self.last, stime)

        # wake
        if self.isoff:
            self.wake()

        # set direction
        if steps < 0:
            self.pd.value(self.reverse)
            sv = -1
        else:
            self.pd.value(self.forward)
            sv = 1

        # step
        for s in range(abs(steps)):
            if self.stop:
                break
            while waitfor and time.ticks_diff(time.ticks_us(), waitfor) < 0:
                time.sleep_us(10)
            self.last = time.ticks_us()
            waitfor = time.ticks_add(waitfor, stime)
            self.ps.value(1)
            time.sleep_us(10)  # a4988 requires 1 us
            self.ps.value(0)
            sc += sv

        # sleep
        if sleep:
            self.sleep()

        # done
        self.steps += sc
        self.stop = False
        self.running = False
        return self.steps

    def beep(self, freq=440, time_ms=250, pause=0, sleep=False):

        # determine steps based on freq and period
        stime = int(round(500000 / max(1, freq), 0))  # 500000 is divide-by-2 (each step is a forward and back)
        steps = int(round(time_ms * 500 / stime, 0))  # 500 is divide-by-2 (each step is a forward and back)

        # timing setup (see step() for details)
        if time.ticks_diff(time.ticks_us(), time.ticks_add(self.last, stime)) >= 0:
            waitfor = time.ticks_us()
        else:
            waitfor = time.ticks_add(self.last, stime)

        # wake
        if self.isoff:
            self.wake()

        # step forward and back
        for s in range(steps):

            # forward
            self.pd.value(self.forward)
            while waitfor and time.ticks_diff(time.ticks_us(), waitfor) < 0:
                time.sleep_us(10)
            self.last = time.ticks_us()
            waitfor = time.ticks_add(waitfor, stime)
            self.ps.value(1)
            time.sleep_us(10)  # a4988 requires 1 us
            self.ps.value(0)

            # back
            self.pd.value(self.reverse)
            while waitfor and time.ticks_diff(time.ticks_us(), waitfor) < 0:
                time.sleep_us(10)
            self.last = time.ticks_us()
            waitfor = time.ticks_add(waitfor, stime)
            self.ps.value(1)
            time.sleep_us(10)  # a4988 requires 1 us
            self.ps.value(0)

        # sleep
        if sleep:
            self.sleep()

        # pause
        if pause:
            time.sleep_ms(pause)

        # done
        return self.steps

# -----------------------------------------------
# end
# -----------------------------------------------

