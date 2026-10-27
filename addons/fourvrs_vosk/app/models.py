"""Explicit model selection and atomic installation from the model publisher."""
import json
import logging
from pathlib import Path, PurePosixPath
import shutil
import stat
import tempfile
import urllib.request
import zipfile

MODELS = {
    'vosk-model-ru-0.42': 'ru',
    'vosk-model-small-ru-0.22': 'ru',
    'vosk-model-small-en-us-0.15': 'en',
    'vosk-model-en-us-0.22': 'en',
}
MODEL_ROOT = Path('/share/fourvrs_vosk/models')
LOGGER = logging.getLogger('fourvrs_vosk')


def options(path=Path('/data/options.json')):
    data = json.loads(path.read_text(encoding='utf-8'))
    model = data.get('model', 'vosk-model-ru-0.42')
    level = data.get('log_level', 'info')
    download = data.get('auto_download', True)
    if model not in MODELS or level not in ('debug', 'info', 'warning', 'error') or type(download) is not bool:
        raise ValueError('Invalid app options')
    return {'model': model, 'log_level': level, 'auto_download': download}


def validate_model(path):
    if not all((path/item).is_file() for item in ('am/final.mdl', 'conf/model.conf')):
        raise ValueError('Model directory is incomplete')


def extract_model(archive, destination, name):
    """Reject unsafe paths, symlinks and unexpected roots before extraction."""
    with zipfile.ZipFile(archive) as source:
        members = source.infolist()
        total = sum(item.file_size for item in members)
        if total > 8 * 1024**3 or total + 128 * 1024**2 > shutil.disk_usage(destination).free:
            raise ValueError('Not enough space for model extraction')
        for item in members:
            path = PurePosixPath(item.filename)
            if (not path.parts or path.is_absolute() or '..' in path.parts or
                    path.parts[0] != name or '\\' in item.filename or
                    stat.S_ISLNK(item.external_attr >> 16)):
                raise ValueError('Invalid model archive path')
        source.extractall(destination)
    validate_model(destination/name)


def ensure_model(config, root=MODEL_ROOT):
    name = config['model']
    if name not in MODELS:
        raise ValueError('Unsupported model')
    root.mkdir(parents=True, exist_ok=True)
    target = root/name
    if target.is_dir():
        validate_model(target)
        return target
    if not config['auto_download']:
        raise ValueError(f'Model missing: copy {name} into {root}, or enable auto_download')
    LOGGER.info('Downloading model %s from Alpha Cephei; the first start can take several minutes', name)
    with tempfile.TemporaryDirectory(prefix='.install-', dir=root) as temporary:
        stage = Path(temporary)
        archive = stage/'model.zip'
        request = urllib.request.Request(f'https://alphacephei.com/vosk/models/{name}.zip',
                                         headers={'User-Agent': '4VRS-Vosk/0.1.1'})
        total = 0
        with urllib.request.urlopen(request, timeout=60) as response, archive.open('wb') as output:
            while chunk := response.read(1024 * 1024):
                total += len(chunk)
                if total > 3 * 1024**3 or shutil.disk_usage(root).free < 128 * 1024**2:
                    raise ValueError('Model download exceeds available space or size limit')
                output.write(chunk)
        extract_model(archive, stage, name)
        (stage/name).rename(target)
    LOGGER.info('Model installed: %s', name)
    return target
