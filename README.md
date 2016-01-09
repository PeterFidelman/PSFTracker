## Synopsis

PSFTracker is a suite of DOS and Python programs for composing and playing
[Adlib/YM3812/OPL2](https://en.wikipedia.org/wiki/Yamaha_YM3812) chip
music.

## Motivation

There are plenty of other, excellent Adlib trackers out there, but
none had the exact feature set I was looking for, so I wrote my own.

PSFTracker supports:

* 9 channels of 2-op synthesis.
* Arpeggiation, pitch slide, note cut, and modulator volume effects.
* A dedicated "volume" column (like MilkyTracker/XM).

PSFTracker does not support:

* Extra OPL3 channels and waveforms  (although it runs fine on an OPL3).
* Rhythm mode

## Example
The following is a YouTube video:  click to play.

[![Soap on a Rope](http://img.youtube.com/vi/TJ6nCyu1YiQ/0.jpg)](http://www.youtube.com/watch?v=TJ6nCyu1YiQ)

## Installation

### Dependencies
#### pyaudio (>= 0.2.8)
If you are lucky you will be able to simply run `apt-get install python-pyaudio`.  If that doesn't work, try manually retrieving and installing the package from [its PyPi project page](https://pypi.python.org/pypi/PyAudio/).

#### pyopl (>= 1.3)
This isn't in any distro, as far as I know.  Fortunately, it has absolutely no dependencies so it is simple to install  from its [PyPi project page](https://pypi.python.org/pypi/PyOPL/1.3).

### PSFTracker itself
Simply "git clone" this repo somewhere and you're off and running.

* The `.py` files require Python 2 (tested on 2.7.9).
* Each `.s` file is [nasm](http://nasm.us) 80386 assembly, targeting a DOS machine with a Sound Blaster or Adlib compatible sound card. Each `.s` file produces a native DOS COM binary; assemble with  `nasm -f bin foo.s -o foo.com`.

## Project Organization
###player/
DOS Adlib player.

The Real Deal.  To use this, place a song file in the directory, then modify the line `incbin "testsong"` (in `player.s`) to point to your song file.  When you compile with nasm, you will get one monolithic `.com` executable containing song and player.

###playspkr/
DOS PC-Speaker player.

This is a little hacky player that takes specially formatted 1-channel songs and blasts them out the PC speaker.

###python/
Python utilities that let you play and write songs on a modern PC.  Contains small implementations of the song player and viewer, including software OPL2 Adlib emulation via pyopl.

###tracker/
DOS Adlib tracker.  (Doesn't exist yet).

For now, contains a simple python "tracker" inspired by [edlin](https://en.wikipedia.org/wiki/Edlin).  It's pretty clunky, but it's enough to write simple songs.

###songs/
The Adlib song format, and some test songs.

###utill/
DOS technical demonstrators.

These exercise features I wanted to add to the tracker or player.  Feel free to ignore them.

## API Reference
PSFTracker is still under development and you shouldn't count on any part of the code  remaining stable.

The song format, however, *is* stable.  See `songs/format.s` and `playspkr/format.s`. for more information.

TODO add more information about the song format.

## Contributors

Honestly, it's a bit early for that.  But feel free to contact me with feature requests and general feedback.

## License

PSFTracker is released into the public domain.  If you find it useful,
then use it -- whether as a finished tool to make music,
or as a building block for your own Python/DOS audio experimentation!

Share and Enjoy.
