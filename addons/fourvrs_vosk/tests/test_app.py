import asyncio
import io
import json
from pathlib import Path
import sys
import tempfile
import threading
import unittest
from unittest.mock import patch
import zipfile

sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'app'))
from models import ensure_model, extract_model, options
from service import Service, MAX_AUDIO_BYTES, recognize
from wyoming.asr import Transcribe, Transcript
from wyoming.audio import AudioStart, AudioChunk, AudioStop
from wyoming.event import async_read_event, async_write_event
from wyoming.info import Describe, Info


class ModelTests(unittest.TestCase):
    def test_download_is_installed_atomically_and_not_repeated(self):
        name='vosk-model-small-ru-0.22'
        content=io.BytesIO()
        with zipfile.ZipFile(content,'w') as archive:
            archive.writestr(name+'/am/final.mdl', b'model')
            archive.writestr(name+'/conf/model.conf', b'configuration')
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder)
            config={'model':name,'auto_download':True}
            with patch('urllib.request.urlopen',return_value=io.BytesIO(content.getvalue())) as download:
                target=ensure_model(config,root)
                self.assertTrue((target/'am/final.mdl').is_file())
                request=download.call_args.args[0]
                self.assertEqual(request.full_url, f'https://alphacephei.com/vosk/models/{name}.zip')
            self.assertEqual(list(root.iterdir()), [target])
            with patch('urllib.request.urlopen',side_effect=AssertionError('unexpected redownload')):
                self.assertEqual(ensure_model(config,root), target)

    def test_recognition_retains_intermediate_results_with_open_vocabulary(self):
        with patch('service.KaldiRecognizer') as factory:
            recognizer=factory.return_value
            recognizer.AcceptWaveform.side_effect=[True,False,True]
            recognizer.Result.side_effect=['{"text":"первая часть"}','{"text":"вторая часть"}']
            recognizer.FinalResult.return_value='{"text":"завершение"}'
            self.assertEqual(recognize('model',bytes(10000)), 'первая часть вторая часть завершение')
            factory.assert_called_once_with('model',16000)
            recognizer.SetWords.assert_called_once_with(True)

    def test_options_and_existing_model_need_no_network(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder)
            config=root/'options.json'
            config.write_text(json.dumps({'model':'vosk-model-ru-0.42','auto_download':False}))
            settings=options(config)
            model=root/settings['model']
            (model/'am').mkdir(parents=True)
            (model/'conf').mkdir()
            (model/'am/final.mdl').write_bytes(b'model')
            (model/'conf/model.conf').write_text('test')
            with patch('urllib.request.urlopen', side_effect=AssertionError('network')):
                self.assertEqual(ensure_model(settings, root), model)
            config.write_text('{"model":"../../other"}')
            with self.assertRaises(ValueError):
                options(config)

    def test_missing_model_with_download_disabled_and_unsafe_archives(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder)
            with self.assertRaises(ValueError):
                ensure_model({'model':'vosk-model-ru-0.42','auto_download':False},root)
            for path in ('../escape','/escape','other/am/final.mdl','model/../escape','model\\escape'):
                archive=io.BytesIO()
                with zipfile.ZipFile(archive,'w') as output:
                    output.writestr(path,b'test')
                archive.seek(0)
                with self.subTest(path=path), self.assertRaises(ValueError):
                    extract_model(archive,root,'model')


class ProtocolTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.service=Service(object(),'vosk-model-ru-0.42','ru')
        self.server=await asyncio.start_server(self.service.handle,'127.0.0.1',0,limit=65536)
        self.port=self.server.sockets[0].getsockname()[1]
        self.writers=[]

    async def asyncTearDown(self):
        for writer in self.writers:
            writer.close()
            await writer.wait_closed()
        self.server.close()
        await self.server.wait_closed()
        await self.service.close()

    async def connect(self):
        reader,writer=await asyncio.open_connection('127.0.0.1',self.port)
        self.writers.append(writer)
        return reader,writer

    async def send_audio(self,writer,pcm=b'\x00\x01'*1600,language='ru',rate=16000):
        await async_write_event(Transcribe(language=language).event(),writer)
        await async_write_event(AudioStart(rate=rate,width=2,channels=1).event(),writer)
        await async_write_event(AudioChunk(rate=rate,width=2,channels=1,audio=pcm).event(),writer)
        await async_write_event(AudioStop().event(),writer)

    async def test_describe_and_exact_pcm_forwarding_without_transcript_logs(self):
        reader,writer=await self.connect()
        await async_write_event(Describe().event(),writer)
        info=Info.from_event(await async_read_event(reader))
        self.assertEqual(info.asr[0].models[0].languages,['ru'])
        self.assertEqual(info.asr[0].models[0].name,'vosk-model-ru-0.42')
        pcm=b'\x03\x04'*1600
        with patch('service.recognize',return_value='секретное слово') as recognize, self.assertLogs('fourvrs_vosk',level='INFO') as logs:
            await self.send_audio(writer,pcm)
            result=await asyncio.wait_for(async_read_event(reader),2)
        self.assertEqual(Transcript.from_event(result).text,'секретное слово')
        self.assertEqual(recognize.call_args.args[1],pcm)
        self.assertNotIn('секретное',str(logs.output))

    async def test_wrong_language_format_and_oversized_payload_are_rejected(self):
        for language,rate in [('en',16000),('ru',8000)]:
            reader,writer=await self.connect()
            await self.send_audio(writer,language=language,rate=rate)
            self.assertEqual((await asyncio.wait_for(async_read_event(reader),2)).type,'error')
        reader,writer=await self.connect()
        writer.write(b'{"type":"audio-chunk","payload_length":999999999}\n')
        await writer.drain()
        self.assertEqual((await asyncio.wait_for(async_read_event(reader),2)).type,'error')

    async def test_long_audio_is_rejected_without_recognition(self):
        reader,writer=await self.connect()
        with patch('service.recognize') as recognize:
            await async_write_event(Transcribe(language='ru').event(),writer)
            await async_write_event(AudioStart(rate=16000,width=2,channels=1).event(),writer)
            for _ in range(MAX_AUDIO_BYTES//32000+1):
                await async_write_event(AudioChunk(rate=16000,width=2,channels=1,audio=bytes(32000)).event(),writer)
            result=await asyncio.wait_for(async_read_event(reader),2)
            self.assertEqual(result.type,'error')
            recognize.assert_not_called()

    async def test_describe_remains_responsive_and_busy_request_is_not_queued(self):
        started,release=threading.Event(),threading.Event()
        def slow(*_):
            started.set()
            release.wait(3)
            return 'готово'
        with patch('service.recognize',side_effect=slow):
            reader,writer=await self.connect()
            await self.send_audio(writer)
            try:
                self.assertTrue(await asyncio.to_thread(started.wait,2))
                other_reader,other_writer=await self.connect()
                await async_write_event(Describe().event(),other_writer)
                self.assertEqual((await asyncio.wait_for(async_read_event(other_reader),1)).type,'info')
                await self.send_audio(other_writer)
                self.assertEqual((await asyncio.wait_for(async_read_event(other_reader),1)).type,'error')
            finally:
                release.set()
            self.assertEqual((await asyncio.wait_for(async_read_event(reader),2)).type,'transcript')
