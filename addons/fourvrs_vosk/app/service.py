"""Bounded Wyoming adapter. No dialog, password list or transcript logging."""
import asyncio
from concurrent.futures import ThreadPoolExecutor
import json
import logging
import time

from vosk import KaldiRecognizer
from wyoming.asr import Transcribe, Transcript
from wyoming.audio import AudioChunk, AudioStart, AudioStop
from wyoming.event import Event, async_write_event
from wyoming.info import AsrModel, AsrProgram, Attribution, Describe, Info

LOGGER = logging.getLogger('fourvrs_vosk')
MAX_AUDIO_BYTES = 30 * 16000 * 2
MAX_EVENT_BYTES = 65536


async def read_event(reader):
    """Apply size limits before reading Wyoming JSON/data/payload bodies."""
    line = await reader.readline()
    if not line:
        return None
    header = json.loads(line)
    if not isinstance(header, dict) or not isinstance(header.get('type'), str):
        raise ValueError('Invalid event')
    lengths = []
    for key in ('data_length', 'payload_length'):
        value = header.get(key, 0)
        if type(value) is not int or not 0 <= value <= MAX_EVENT_BYTES:
            raise ValueError('Event too large')
        lengths.append(value)
    data = header.get('data', {})
    if not isinstance(data, dict):
        raise ValueError('Invalid event data')
    if lengths[0]:
        extra = json.loads(await reader.readexactly(lengths[0]))
        if not isinstance(extra, dict):
            raise ValueError('Invalid event data')
        data.update(extra)
    payload = await reader.readexactly(lengths[1]) if lengths[1] else None
    return Event(type=header['type'], data=data, payload=payload)


def recognize(model, pcm):
    # Same Vosk version, full vocabulary and result aggregation as WSL VoskSpeech.
    recognizer = KaldiRecognizer(model, 16000)
    recognizer.SetWords(True)
    parts = []
    for offset in range(0, len(pcm), 4000):
        if recognizer.AcceptWaveform(pcm[offset:offset+4000]):
            parts.append(json.loads(recognizer.Result()))
    parts.append(json.loads(recognizer.FinalResult()))
    return ' '.join(part.get('text', '') for part in parts).strip()


class Service:
    def __init__(self, model, model_name, language):
        self.model, self.model_name, self.language = model, model_name, language
        self.executor = ThreadPoolExecutor(max_workers=1, thread_name_prefix='vosk')
        self.busy = False
        self.connections = 0
        self.tasks = set()
        self.info = Info(asr=[AsrProgram(name='4vrs-vosk',
            description='Vosk speech recognition; unofficial 4VRS Home Assistant adapter',
            attribution=Attribution(name='Alpha Cephei / Vosk', url='https://alphacephei.com/vosk/'),
            installed=True, version='0.1.0', models=[AsrModel(name=model_name,
                description=model_name, attribution=Attribution(name='Alpha Cephei',
                    url='https://alphacephei.com/vosk/models'), installed=True,
                version=None, languages=[language])])]).event()

    async def handle(self, reader, writer):
        task = asyncio.current_task()
        self.tasks.add(task)
        self.connections += 1
        acquired = False
        try:
            if self.connections > 8:
                raise ValueError('Too many connections')
            pcm = bytearray()
            transcribe = started = False
            deadline = time.monotonic() + 45
            while True:
                timeout = min(15, deadline - time.monotonic())
                if timeout <= 0:
                    raise ValueError('Audio request timed out')
                event = await asyncio.wait_for(read_event(reader), timeout)
                if event is None:
                    return
                if Describe.is_type(event.type):
                    await async_write_event(self.info, writer)
                    continue
                if Transcribe.is_type(event.type):
                    if transcribe or started:
                        raise ValueError('Duplicate transcription request')
                    request = Transcribe.from_event(event)
                    if request.language and request.language.replace('_','-').split('-')[0] != self.language:
                        raise ValueError('Language does not match the selected model')
                    if request.name and request.name != self.model_name:
                        raise ValueError('Model does not match the selected model')
                    transcribe = True
                elif AudioStart.is_type(event.type):
                    if not transcribe or started:
                        raise ValueError('Unexpected audio start')
                    audio = AudioStart.from_event(event)
                    if (audio.rate, audio.width, audio.channels) != (16000, 2, 1):
                        raise ValueError('Expected PCM16 mono 16000 Hz')
                    if self.busy:
                        raise ValueError('Recognizer is busy; retry later')
                    self.busy = acquired = started = True
                elif AudioChunk.is_type(event.type):
                    if not started:
                        raise ValueError('Audio start required')
                    chunk = AudioChunk.from_event(event)
                    if (chunk.rate, chunk.width, chunk.channels) != (16000, 2, 1) or len(chunk.audio) % 2:
                        raise ValueError('Invalid PCM format')
                    if len(pcm) + len(chunk.audio) > MAX_AUDIO_BYTES:
                        raise ValueError('Audio exceeds 30 seconds')
                    pcm.extend(chunk.audio)
                elif AudioStop.is_type(event.type):
                    if not started or not pcm:
                        raise ValueError('No audio received')
                    began = time.monotonic()
                    text = await asyncio.get_running_loop().run_in_executor(
                        self.executor, recognize, self.model, bytes(pcm))
                    await async_write_event(Transcript(text=text).event(), writer)
                    LOGGER.info('Recognition complete: audio_ms=%d elapsed_ms=%d words=%d',
                        len(pcm)*1000//32000, (time.monotonic()-began)*1000, len(text.split()))
                    return
                else:
                    raise ValueError('Unsupported event')
        except (ValueError, KeyError, TypeError, asyncio.TimeoutError, asyncio.IncompleteReadError) as exc:
            # Log only the exception class: malformed JSON can contain private speech.
            LOGGER.warning('Request rejected: %s', type(exc).__name__)
            try:
                await async_write_event(Event(type='error', data={
                    'code':'transcription-failed', 'text':'Vosk request failed; check model, format or server load'}), writer)
            except (OSError, ConnectionError):
                pass
        except (OSError, ConnectionError):
            LOGGER.debug('Client disconnected')
        except Exception:
            LOGGER.error('Recognition failed; restart the app if the problem persists')
        finally:
            if acquired:
                self.busy = False
            self.connections -= 1
            self.tasks.discard(task)
            writer.close()
            try:
                await writer.wait_closed()
            except OSError:
                pass

    async def close(self):
        for task in list(self.tasks):
            task.cancel()
        if self.tasks:
            await asyncio.gather(*self.tasks, return_exceptions=True)
        self.executor.shutdown(wait=True, cancel_futures=True)
