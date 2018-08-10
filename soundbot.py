from asyncio.futures import CancelledError

import config
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

def handle_cmd(cmd,user,fplayer,bplayer):
    log.debug(user)
    cmd = cmd.replace(':','')
    if user=='soundbot': #TODO fetch username
        pass
    elif cmd in ('ls','list'):
        asyncio.get_event_loop().create_task(s.send_msg_async(list_files(), channel_name=config.slack_channel))
    elif cmd in ('ll'):
        asyncio.get_event_loop().create_task(s.send_msg_async(ll_files(), channel_name=config.slack_channel))    
    elif cmd=='stop':
        fplayer.cancel()
    elif cmd=='!stop':
        bplayer.cancel()
    elif cmd.startswith('!'):
        soundq_back.put_nowait(cmd[1:])
    elif cmd.startswith('?'):
        soundq_fore.put_nowait('duhast')
        soundq_fore.put_nowait(cmd[1:])
        soundq_fore.put_nowait('gesagt')
    elif cmd=='~':
        soundq_fore.put_nowait('shotgun')
        fplayer.cancel()
        bplayer.cancel() 
    elif user=='tim' and cmd=='man man man':
        fplayer.cancel()
        bplayer.cancel()
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
                        log.debug('SOUND {}, speed {}'.format(sound, speed))
                        process = await asyncio.create_subprocess_shell("play mp3s/{}.mp3 speed {}".format(sound, speed))

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

def list_files():
    all_files = os.listdir('mp3s')
    mp3s = [parts[0] for file in all_files for parts in [file.split('.')] if parts[-1]=='mp3']
    mp3s.sort()
    return ' '.join(mp3s)


def ll_files():
    all_files = os.listdir('mp3s')
    mp3s = [parts[0] for file in all_files for parts in [file.split('.')] if parts[-1]=='mp3']
    mp3s.sort()
    return '\n:notes: '.join(mp3s)

def ran():
    all_files = os.listdir('mp3s')
    mp3s = [parts[0] for file in all_files for parts in [file.split('.')] if parts[-1]=='mp3']
    return random.choice(mp3s) 

async def handler(fplayer,bplayer):
    while True:
        log.debug("in handler loop")
        event = await s.get_event_aio()
        if event.event.get('channel')==config.slack_channel and event.event.get('type')=='message':
            log.debug("processing: "+event.json)
            handle_cmd(event.event.get('text'),event.event.get('user'),fplayer,bplayer)

soundq_fore = AiterQueue()
soundq_back = AiterQueue()

s = SlackSocket(config.api_key,asyncio.get_event_loop(),translate=True)
fplayer = asyncio.get_event_loop().create_task(playsounds(soundq_fore))
bplayer = asyncio.get_event_loop().create_task(playsounds(soundq_back))
asyncio.get_event_loop().run_until_complete(handler(fplayer,bplayer))


