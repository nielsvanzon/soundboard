from asyncio.futures import CancelledError

import config
import json
from slacksocket import SlackSocket
import os
import asyncio
import asyncio.queues
import logging
import random

logging.basicConfig(level=logging.DEBUG)
log = logging.getLogger('soundbot')

class AiterQueue(asyncio.queues.Queue):
    def __aiter__(self):
        return self
    async def __anext__(self):
        return await self.get()


'''
def aiter(q):
    q.__aiter__ = lambda self: self
    q.__anext__ = asyncio.queues.Queue.get
    return q
'''

def handle_cmd(cmd,user,fplayer,bplayer,tplayer):
    log.debug(user)
    cmd = cmd.replace(':','')
    if user=='soundbot': #TODO fetch username
        pass
    elif cmd in ('--help'):
        asyncio.get_event_loop().create_task(s.send_msg_async(helpme(), channel_name=config.slack_channel))
    elif cmd in ('ls'):
        asyncio.get_event_loop().create_task(s.send_msg_async(ls_files(), channel_name=config.slack_channel))
    elif cmd in ('list'):
        asyncio.get_event_loop().create_task(s.send_msg_async(list_files(), channel_name=config.slack_channel))
    elif cmd in ('ll'):
        asyncio.get_event_loop().create_task(s.send_msg_async(ll_files(), channel_name=config.slack_channel))    
    elif cmd=='stop':
        fplayer.cancel()
    elif cmd=='!stop':
        bplayer.cancel()
    elif cmd=='%stop':
        tplayer.cancel()
    elif cmd.startswith('!'):
        soundq_back.put_nowait(cmd[1:])
    elif cmd.startswith('%'):
        soundq_third.put_nowait(cmd[1:])
    elif cmd.startswith('?'):
        soundq_fore.put_nowait('duhast')
        soundq_fore.put_nowait(cmd[1:])
        soundq_fore.put_nowait('gesagt')
    elif cmd=='~':
        soundq_fore.put_nowait('shotgun')
        fplayer.cancel()
        bplayer.cancel() 
        tplayer.cancel()
    elif cmd.startswith('&amp;'):
        log.debug(cmd[5:])
        soundq_fore.put_nowait(cmd[5:])
        soundq_fore.put_nowait("${0}".format(cmd[5:]))
    elif user=='tim' and cmd=='man man man':
        fplayer.cancel()
        bplayer.cancel()
        tplayer.cancel()
        soundq_fore.put_nowait('neetim')
    elif cmd=='random':
        soundq_fore.put_nowait(ran()) 
    else:
        soundq_fore.put_nowait(cmd)

async def playsounds(q):
    while True:
        try:
            async for sound in q:
                log.debug("starting {}".format(sound))
                try:
                    if sound.startswith('+'):
                        speed = 1 + ( sound.count('+') * 0.1 )
                        sound = sound.replace('+','')
                        process = await asyncio.create_subprocess_exec(config.play_cmd_rev,"mp3s/{0}.mp3".format(sound), "speed", "{0}".format(speed))
                    elif sound.startswith('-'):
                        speed = 1 - ( sound.count('-') * 0.1 )
                        sound = sound.replace('-','')
                        process = await asyncio.create_subprocess_exec(config.play_cmd_rev,"mp3s/{0}.mp3".format(sound), "speed", "{0}".format(speed))
                    elif sound.startswith(']'):
                        vol = 1 + ( sound.count(']') * 0.2 )
                        sound = sound.replace(']','')
                        process = await asyncio.create_subprocess_exec(config.play_cmd_rev,"mp3s/{0}.mp3".format(sound), "vol", "{0}".format(vol))
                    elif sound.startswith('['):
                        vol = 1 - ( sound.count('[') * 0.1 )
                        vol = 0.01 if vol < 0 else vol
                        sound = sound.replace('[','')
                        process = await asyncio.create_subprocess_exec(config.play_cmd_rev,"mp3s/{0}.mp3".format(sound), "vol", "{0}".format(vol))
                    elif sound.startswith('}'):
                        pitch = sound.count('}') * 100 
                        sound = sound.replace('}','')
                        process = await asyncio.create_subprocess_exec(config.play_cmd_rev,"mp3s/{0}.mp3".format(sound), "pitch", "{0}".format(pitch))
                    elif sound.startswith('{'):
                        pitch = 0 - sound.count('{') * 100
                        sound = sound.replace('{','')
                        process = await asyncio.create_subprocess_exec(config.play_cmd_rev,"mp3s/{0}.mp3".format(sound), "pitch", "{0}".format(pitch))
                    elif sound.startswith('$'): 
                        process = await asyncio.create_subprocess_exec(config.play_cmd_rev,"mp3s/{0}.mp3".format(sound[1:]), "reverse")
                    elif sound.startswith('heavy_dollar_sign'):
                        process = await asyncio.create_subprocess_exec(config.play_cmd_rev,"mp3s/{0}.mp3".format(sound[17:]), "reverse") 
                    else:
                        process = await asyncio.create_subprocess_exec(config.play_cmd,"mp3s/{0}.mp3".format(sound)) 
                except:
                    pass
                try:
                    await process.wait()
                    log.debug("{} played".format(sound))
                except CancelledError:
                    process.terminate()
                    log.debug("{} cancelled".format(sound))
        except CancelledError:
            pass

def ls_files():
    all_files = os.listdir('mp3s')
    mp3s = [parts[0] for file in all_files for parts in [file.split('.')] if parts[-1]=='mp3']
    mp3s.sort()
    return ' '.join(mp3s)

def list_files():
    all_files = os.listdir('mp3s')
    mp3s = [parts[0] for file in all_files for parts in [file.split('.')] if parts[-1]=='mp3']
    mp3s.sort()
    return ','.join(mp3s)

def ll_files():
    all_files = os.listdir('mp3s')
    mp3s = [parts[0] for file in all_files for parts in [file.split('.')] if parts[-1]=='mp3']
    mp3s.sort()
    return '\n:notes: '.join(mp3s)

def ran():
    all_files = os.listdir('mp3s')
    mp3s = [parts[0] for file in all_files for parts in [file.split('.')] if parts[-1]=='mp3']
    return random.choice(mp3s) 

def helpme():
    return "+ = Snelheid verhogen\n- = Snelheid verlagen\n} = Pitch verhogen\n{ = Pitch verlagen\n] = Volume verhogen (Nee Tim)\n[ = Volume verlagen\n$ = Achterstevoren afspelen\n~ = Kill all\n& = Heen en weer"


async def handler(fplayer,bplayer,tplayer):
    while True:
        log.debug("in handler loop")
        event = await s.get_event_aio()
        log.debug("processing: "+ event.json)
        
        data = json.loads(event.json) 
        log.debug("data type: " + data['type'])
        log.debug("text in data: " + str('text' in data))
        
        if event.event.get('channel')==config.slack_channel and event.event.get('type')=='message': 
            handle_cmd(event.event.get('text'),event.event.get('user'),fplayer,bplayer,tplayer)

soundq_fore = AiterQueue()
soundq_back = AiterQueue()
soundq_third = AiterQueue()

s = SlackSocket(config.api_key,asyncio.get_event_loop(),translate=True)
fplayer = asyncio.get_event_loop().create_task(playsounds(soundq_fore))
bplayer = asyncio.get_event_loop().create_task(playsounds(soundq_back))
tplayer = asyncio.get_event_loop().create_task(playsounds(soundq_third))
asyncio.get_event_loop().run_until_complete(handler(fplayer,bplayer, tplayer))


