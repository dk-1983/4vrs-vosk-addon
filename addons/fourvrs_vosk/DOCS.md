# Installation / Установка

## Русский

### Через магазин дополнений HA

Требуется HA OS или установка с Supervisor, процессор amd64 и интернет
для установки образа и первой загрузки отсутствующей модели.
Модель `vosk-model-ru-0.42` занимает около 1,8 ГБ в архиве; в нашем контейнере
с уже загруженной моделью измерено около 6,5 ГиБ памяти. Оставьте несколько
гигабайт свободного диска для загрузки и распаковки. Размер и время загрузки могут отличаться.

1. В магазине дополнений откройте меню **Репозитории** и добавьте:
   `https://github.com/dk-1983/4vrs-vosk-addon`.
2. Обновите список магазина. Откройте **4VRS Vosk** и нажмите **Установить**.
   Образ собирается сервером из Dockerfile; отдельной публикации в Docker Registry
   для этой версии не требуется.
3. В разделе конфигурации оставьте:

   ```yaml
   model: vosk-model-ru-0.42
   auto_download: true
   log_level: info
   ```

4. Запустите дополнение. Дождитесь строки **Ready: Wyoming port=10301** в журнале.
   Первый запуск скачивает и загружает модель; не запускайте звонок в этот момент.
   Если Watchdog перезапускает контейнер во время долгой первой загрузки,
   выключите его до появления Ready и затем включите снова.
5. В HA: **Настройки → Устройства и службы → Добавить интеграцию → Wyoming Protocol**.
   Укажите IP вашего сервера HA и порт **10301**.
   Если изменили внешний порт в разделе «Сеть» дополнения, используйте новый порт.
6. В параметрах нашей интеграции домофона откройте **Подключение и распознавание**,
   выберите новую сущность STT Vosk (обычно `stt.4vrs_vosk`) и язык **ru**.
   Ориентируйтесь на фактическую сущность в HA: entity_id может отличаться.
7. Запустите обычный звонок. Существующие пользователи, пароли, открытие двери,
   подтверждение входа и уведомления остаются в интеграции домофона.

Плата продолжает отправлять звук непосредственно в HA. Перепрошивка не нужна,
WSL и его сервер диалога не используются. Не запускайте второй сервер диалога
для управления той же платой. Сами STT-сервисы Vosk и Whisper могут существовать
параллельно; в интеграции выбирается один из них.

### Настройки и хранение

- **model**: точная модель. `ru-0.42` — та же полная модель, что была проверена
  с WSL. Малые модели не являются её эквивалентом по качеству. Английская модель
  требует языка `en` в нашей интеграции. Язык интерфейса не выбирает модель.
- **auto_download**: скачивание только отсутствующего каталога модели с
  `https://alphacephei.com/vosk/models/`. После загрузки распознавание офлайн.
- **log_level**: подробность журнала; текст речи и аудио не сохраняются даже при debug.
- Каталоги моделей: `/share/fourvrs_vosk/models/<имя-модели>/`.
  При доступе к общей папке HA это `share/fourvrs_vosk/models`.
  Можно заранее скопировать туда уже распакованную проверенную модель и
  отключить auto_download. Сам микросервис не записывает диагностические WAV.
- После смены настроек сохраните их и перезапустите дополнение штатной кнопкой HA.
- При смене языка модели перезагрузите запись интеграции Wyoming, чтобы HA
  обновил список поддерживаемых языков. Затем измените язык STT домофона.
- Порт 10301 предоставляет Wyoming без аутентификации; используйте его в локальной
  сети. Можно отключить публикацию порта на хосте и подключить HA к внутреннему
  имени/IP дополнения, указанному в его информации Supervisor.

### Обновления

Запуск, остановка, перезапуск, Watchdog, запуск при загрузке и журнал находятся
на штатной странице дополнения HA. Для установок из Git-репозитория обновления
появляются при выпуске новой версии в `config.yaml`. Если в вашей версии HA
доступно автоматическое обновление дополнений, его можно включить на этой странице.
Перед первым обновлением проверьте настройки резервного копирования HA.

Версии движка и библиотеки зафиксированы: Vosk 0.3.45, Wyoming 1.5.2.
Они меняются вместе с проверенным выпуском оболочки, а не через pip при старте.
Это сохраняет возможность обновлений, не подменяя движок без выпуска новой версии.
Файлы моделей переживают обновление контейнера. Одинаковое имя модели не означает
проверку или скачивание её новой редакции: автоматической замены модели нет.

### Что остаётся вне дополнения

Сервис возвращает текст, а правила доступа выполняет интеграция домофона.
HA STT не передаёт ей числовую confidence Vosk, поэтому прежний порог confidence
из WSL не применяется. Сравнение пароля остаётся точным; списки допустимых паролей,
ограниченная грамматика и приблизительная подстановка текста не используются.
Для повреждённой аудиозаписи сохраняется отказ от авторизации в нашей интеграции.

### Локальная установка без публичного репозитория

Распакуйте папку `fourvrs_vosk` из `addons/` в каталог локальных дополнений
Supervisor (`/addons` в соответствующей общей папке или каталог
`addons/local` в данных Supervisor). Обновите магазин и установите из раздела
локальных дополнений. Не копируйте эти файлы в `custom_components`.
Точный путь на хосте зависит от установки HA. Для обновлений через веб-панель
предпочтительнее постоянный Git-репозиторий.

## English

### Install from the HA app store

Requires Home Assistant OS or a Supervisor installation on amd64. Add
`https://github.com/dk-1983/4vrs-vosk-addon` to the app/add-on store repositories,
refresh the store, open **4VRS Vosk**, and install. Supervisor builds the Dockerfile
on the server; no separately published image is required for this release.

Keep the default model `vosk-model-ru-0.42`, `auto_download: true`, and
`log_level: info`. Start the app and wait for **Ready: Wyoming port=10301**.
The first start downloads the model; temporarily disable Watchdog if it interrupts
that first download. Our running full-model container used about 6.5 GiB RAM.
Allow several GB of disk space for download and extraction. Smaller models can
produce different recognition results and are not drop-in quality equivalents.

Add the **Wyoming Protocol** integration to HA using the HA server address and
port **10301** (or the mapped host port you selected). In the intercom connection
options choose the new Vosk STT entity and language **ru**. Select the actual
entity ID shown by HA; it is commonly `stt.4vrs_vosk` but may differ.
No firmware change or WSL dialog server is needed. Keep the existing users,
passwords, door control and notifications in the intercom integration. Whisper
can remain installed; switching the STT entity chooses the active recognizer.

### Options, storage and updates

Models live in `/share/fourvrs_vosk/models/<model-name>/` and survive app updates.
Copy an extracted model there and disable `auto_download` to avoid downloading it.
Downloading uses the official Alpha Cephei model site and occurs only when the
selected model directory is missing. Recognition itself works offline.

Save options and restart the app after changes. When switching the model language,
reload the Wyoming config entry so HA refreshes supported languages, then change
the intercom STT language to match (`ru` or `en`). UI language never selects a model.
The app does not save recordings or log transcripts, including at debug level.

Use HA's standard page for start, stop, restart, logs, start-on-boot and Watchdog.
New repository releases are announced by changes to the app version. Enable
automatic app updates if offered by your HA version. Engine and library versions
are pinned and updated in tested app releases, never silently at startup. Model
files are not automatically replaced when they retain the same name.

Wyoming port 10301 is unauthenticated and intended for the local network. It can
also be left unexposed when HA uses the app's internal Supervisor hostname/IP.
HA STT exposes text, not Vosk numeric confidence; the old WSL confidence threshold
is therefore not applied. Password comparison stays exact, with no password-only
grammar, sentence correction or fuzzy authorization.

For local installation, copy `addons/fourvrs_vosk` into Supervisor's local app
directory, refresh the store, and install from the local section. Do not put it
under `custom_components`. Repository installation is preferable for web updates.

Licenses and attribution: [licenses/NOTICE.md](licenses/NOTICE.md).
