# e-Qazyna XLSX exporter

Онлайн-выгрузка заявок e-Qazyna в Excel через **GitHub Actions**. Локальный запуск с компьютера не нужен.

Сценарий: открыть GitHub в браузере → нажать **Run workflow** → скачать готовый `.xlsx` из артефактов.

## Что выгружается

Фильтр по реестру e-Qazyna:

- тип документа: `Заявка на разведку ТПИ`;
- статусы: `Отправлено на рассмотрение`, `Принято`;
- сортировка: самые новые заявки сверху;
- обогащение по БИН через `data.egov.kz`, если задан `EGOV_API_KEY`.

В Excel попадают:

- дата создания;
- номер документа;
- БИН/ИИН заявителя;
- заявитель из e-Qazyna;
- тип документа;
- статус заявки;
- наименование из eGov;
- юридический адрес eGov;
- регион по адресу;
- руководитель / контактное лицо из eGov, если поле пришло из API;
- вид деятельности / ОКЭД, если поле пришло из API;
- ссылки на 2GIS / Google / Яндекс для ручного поиска телефона;
- источник e-Qazyna;
- сырой eGov JSON-фрагмент для диагностики.

## Как запустить в GitHub без компьютера

### 1. Создать репозиторий

1. Зайти в GitHub.
2. Создать новый репозиторий, например `eqazyna-xlsx-exporter`.
3. Загрузить содержимое этого архива в репозиторий.

Можно через браузер:

- кнопка **Add file**;
- **Upload files**;
- перетащить все файлы и папки из архива;
- **Commit changes**.

### 2. Добавить API-ключ eGov

В репозитории открыть:

`Settings → Secrets and variables → Actions → New repository secret`

Создать secret:

```text
Name: EGOV_API_KEY
Secret: твой API-ключ data.egov.kz
```

Не вставляй API-ключ в workflow inputs и не коммить его в файлы. Ключ должен жить только в GitHub Secrets.

### 3. Запустить выгрузку

Открыть:

`Actions → Export e-Qazyna XLSX → Run workflow`

Параметры:

- `pages` — сколько первых страниц реестра проверить, например `5`, `10`, `20`;
- `no_egov` — поставить `true`, если надо выгрузить только заявки без обогащения по БИН.

Нажать зелёную кнопку **Run workflow**.

### 4. Скачать Excel

После завершения запуска открыть последний run. Внизу будет блок **Artifacts**.

Скачать:

```text
eqazyna-xlsx-export
```

Внутри будет файл:

```text
eqazyna_export.xlsx
```

## Как часто запускать

Для ручной работы команды достаточно запускать по мере необходимости: утром, перед обзвоном, перед планёркой.

Рекомендуемые значения:

- `pages = 5` — быстрая свежая выгрузка;
- `pages = 10` — нормальный дневной запас;
- `pages = 20+` — если долго не запускали.

## Почему не сайт

Сайт не нужен. GitHub Actions уже выполняет роль веб-клиента: есть кнопка запуска, серверное выполнение Python и скачивание результата. API-ключ не попадает в браузер и не светится в файлах.

## Важные ограничения

1. eGov-адрес может быть устаревшим. Его надо считать рабочей подсказкой, а не абсолютной истиной.
2. Телефон автоматически не парсится. Для телефона в Excel добавлены ссылки на 2GIS / Google / Яндекс.
3. Если структура e-Qazyna изменится, парсер может потребовать правки. Это нормально: государственные порталы любят менять HTML так, будто им за это дают премию.
4. Если eGov API временно не отвечает, выгрузка заявок всё равно создаётся, но eGov-колонки будут пустыми или со статусом ошибки.

## Локальный запуск, если когда-нибудь понадобится

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
export EGOV_API_KEY="your_key"
python -m eqazyna_export.main --pages 5 --out exports/eqazyna_export.xlsx
```

Windows PowerShell:

```powershell
python -m venv .venv
. .\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
$env:EGOV_API_KEY="your_key"
python -m eqazyna_export.main --pages 5 --out exports/eqazyna_export.xlsx
```

## Структура проекта

```text
eqazyna_actions_exporter/
├─ .github/workflows/export-xlsx.yml
├─ eqazyna_export/
│  ├─ main.py
│  ├─ pipeline.py
│  ├─ scraper.py
│  ├─ egov_client.py
│  ├─ exporter.py
│  ├─ region.py
│  ├─ models.py
│  └─ utils.py
├─ tests/
├─ requirements.txt
├─ .env.example
└─ README.md
```
