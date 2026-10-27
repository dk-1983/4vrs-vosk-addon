# 4VRS Vosk for Home Assistant

Unofficial Vosk add-on for Home Assistant with Wyoming support and offline
speech recognition. Vosk is developed by Alpha Cephei. This project provides
HA packaging and an adapter; it is not an official Vosk or Wyoming product.

[![Add repository to Home Assistant](https://my.home-assistant.io/badges/supervisor_add_addon_repository.svg)](https://my.home-assistant.io/redirect/supervisor_add_addon_repository/?repository_url=https%3A%2F%2Fgithub.com%2Fdk-1983%2F4vrs-vosk-addon)

## Русский

Добавьте этот репозиторий в магазин дополнений HA, установите **4VRS Vosk**,
дождитесь `Ready` в журнале и подключите его через интеграцию **Wyoming Protocol**.
По умолчанию используется полная русская модель `vosk-model-ru-0.42`.
Порт — **10301**, модель требует нескольких гигабайт памяти. В нашем контейнере
измерено около 6,5 ГиБ с загруженной моделью. Поддерживается amd64.

Настройки, запуск, остановка, перезапуск и журнал доступны из веб-интерфейса HA.
Модели хранятся отдельно и сохраняются при обновлении контейнера.
Интерфейс настроек переведён на русский и английский; язык модели выбирается отдельно.

## English

Add this repository to the HA app/add-on store, install **4VRS Vosk**, wait for
`Ready`, and connect it through **Wyoming Protocol** on port **10301**.
Default: the full Russian `vosk-model-ru-0.42`; it needs several GB of memory
(about 6.5 GiB measured in our container). Currently supports amd64.

Configure, start, stop, restart and view logs from Home Assistant's web UI.
Models persist across container updates. Configuration labels support English
and Russian; recognition model/language is independent of UI language.

## Documentation / Документация

- [Installation and configuration / Установка и настройка](addons/fourvrs_vosk/DOCS.md)
- [App details / О дополнении](addons/fourvrs_vosk/README.md)
- [Changelog / История изменений](addons/fourvrs_vosk/CHANGELOG.md)
- [Third-party licenses and attribution / Лицензии](addons/fourvrs_vosk/licenses/NOTICE.md)

Vosk engine and models retain their original licenses. Wyoming is MIT licensed.
This repository does not claim ownership of these projects or imply endorsement
by their authors. No speech models or user recordings are stored in this repository.
