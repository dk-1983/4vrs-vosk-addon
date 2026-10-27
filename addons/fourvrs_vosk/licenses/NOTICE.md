# Third-party notices / Сторонние компоненты

4VRS Vosk is an unofficial Home Assistant packaging and protocol adapter.
Vosk recognition engine and speech models are developed by Alpha Cephei and
their contributors. Wyoming is developed by Michael Hansen and contributors.
No ownership of these projects or endorsement by their authors is claimed.

Это неофициальная оболочка 4VRS для Home Assistant. Мы не заявляем авторство
Vosk, Wyoming и моделей и не представляем дополнение как официальный продукт
их разработчиков. Собственный код оболочки расположен в app/.

## Vosk API 0.3.45

- Project: https://github.com/alphacep/vosk-api
- License: Apache License 2.0; see VOSK-APACHE-2.0.txt.
- Model publisher and model-specific licenses: https://alphacephei.com/vosk/models
- The four offered models are listed as Apache 2.0 by the publisher.
- Models are downloaded separately; original model files and notices are retained.

## Wyoming 1.5.2 / dependency runtime

- Project: https://github.com/rhasspy/wyoming
- Copyright (c) 2023 Michael Hansen. MIT License; see WYOMING-MIT.txt.
- Runtime image: rhasspy/wyoming-vosk:1.5.1, pinned by digest in Dockerfile.
- Its bundled Wyoming Vosk 1.5.0 package is not our recognition server;
  its original MIT license is retained (WYOMING-VOSK-MIT.txt).
- Other runtime dependencies retain their respective licenses in the image.

The base image and upstream libraries are not modified. The app implements its
own bounded protocol handler around their public APIs. No password vocabulary,
sentence correction or forced transcript matching is enabled.
