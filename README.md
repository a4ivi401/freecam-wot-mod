# FreeCam

Код мода FreeCam для World of Tanks / Mir Tankov.

## Что лежит в репозитории

- `mod_FreeCam_Hangar_and_Replays.py` — основной entrypoint мода.
- `meta.xml` — описание пакета и версия.
- `configs/` — настройки мода.
- `res/` — иконка и ресурсы для упаковки.
- `pack_mtmod.py` — упаковка в `.mtmod`.
- `build.bat` — локальная сборка на Windows через Python 2.7.
- `build.sh` — сборка для GitHub Actions.
- `.github/workflows/release.yaml` — автосборка и публикация релиза.

## Локальная сборка

Windows:

```bat
build.bat 2.11
```

Linux / GitHub Actions:

```bash
bash build.sh 2.11
```

Если версия не передана, `build.sh` пытается взять её из `meta.xml`.

## Автосборка на GitHub

Workflow запускается при пуше тега `v*`, например `v2.11`.
После сборки создаётся релиз с файлом `.mtmod`.

## Первый запуск

1. Создать первый коммит.
2. Отправить его в GitHub.
3. Создать тег `v2.11`.
4. Запушить тег: `git push origin v2.11`.
