"""HA app entrypoint; load the model before accepting speech requests."""
import asyncio
import logging
import signal

from vosk import Model, SetLogLevel
from models import MODELS, ensure_model, options
from service import Service


async def main():
    config = options()
    logging.basicConfig(level=config['log_level'].upper(), format='%(asctime)s %(levelname)s %(message)s')
    SetLogLevel(-1)
    logging.info('Preparing model %s; Wyoming is not ready yet', config['model'])
    path = await asyncio.to_thread(ensure_model, config)
    model = await asyncio.to_thread(Model, str(path))
    service = Service(model, config['model'], MODELS[config['model']])
    stopped = asyncio.Event()
    loop = asyncio.get_running_loop()
    for sig in (signal.SIGTERM, signal.SIGINT):
        loop.add_signal_handler(sig, stopped.set)
    server = await asyncio.start_server(service.handle, '0.0.0.0', 10301, limit=65536)
    logging.info('Ready: Wyoming port=10301 language=%s model=%s', service.language, service.model_name)
    try:
        async with server:
            await stopped.wait()
    finally:
        server.close()
        await server.wait_closed()
        await service.close()


if __name__ == '__main__':
    try:
        asyncio.run(main())
    except Exception as exc:
        # Paths/config are useful here; no audio/transcripts are handled at startup.
        logging.error('Startup failed: %s', exc)
        raise SystemExit(1) from None
