# 4VRS Vosk

Offline speech recognition for Home Assistant over Wyoming. An unofficial
4VRS adapter around **Vosk by Alpha Cephei**, using the **Wyoming library by
Michael Hansen**. We do not claim authorship of Vosk, Wyoming or their models,
and this app is not an official product of their authors.

Распознавание речи Vosk в отдельном контейнере с настройками, запуском,
остановкой и журналом в интерфейсе Home Assistant. Неофициальная оболочка
4VRS; авторство Vosk, Wyoming и моделей принадлежит их разработчикам.

- Default model: `vosk-model-ru-0.42`, the model already tested with this intercom.
- Vosk engine: 0.3.45. Wyoming library: 1.5.2.
- PCM16 mono, 16 kHz; open vocabulary, no forced password matching.
- Model loaded before the server reports `Ready`.
- Recognition runs outside the protocol event loop; one active request at a time.
- No audio storage and no transcript logging.
- Settings translated into English and Russian.
- Current supported/tested architecture: amd64.

See [DOCS.md](DOCS.md) for installation and switching between Vosk and Whisper.
Licenses and attribution: [licenses/NOTICE.md](licenses/NOTICE.md).
