#!/usr/bin/env python3
import os
from pybass import *
import wave
from ctypes import create_string_buffer
__author__ = 'Jakub Pelikan'

class AudioDecoder():
    '''
    Class decode audio packets form ts stream, and save audio in wav format to file.
    '''

    def __init__(self, audio_bits, path):
        self.music = b''
        self.count = 0
        self.path = path
        self.addData(audio_bits)


    def addData(self,audio_bits):
        '''
        Method add audio packet to wav file
        :param bytes: bits with audio
        :return: None
        '''
        self.music = self.music + audio_bits
        self.count = self.count + 1


    def saveAudio(self):
        '''
        Method save audio packets to wav files
        :return:
        '''
        BASS_Init(0, 48000, 0, 0, 0)
        audio = BASS_StreamCreateFile(True,self.music,0,len(self.music), BASS_STREAM_DECODE )
        if audio == 0:
            sys.stderr.write('Error in BASS_StreamCreateFile.')
            return
        buffer = create_string_buffer(1024)
        with wave.open(os.path.join(self.path,'audio.wav'), 'wb') as writeFile :
            writeFile.setparams((2, 2, 48000, 0, 'NONE', 'not compressed'))
            while (BASS_ChannelIsActive(audio) == BASS_ACTIVE_PLAYING):
                BASS_ChannelGetData(audio, buffer, 1024)
                writeFile.writeframesraw(buffer)
        BASS_Free(audio)