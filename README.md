# e-Qazyna Excel Exporter

Выгрузка новых заявок из публичного реестра e-Qazyna в Excel с обогащением по БИН через `data.egov.kz`.

Первая версия специально сделана без Telegram-бота, рассылок и автоматического парсинга 2GIS. Цель — быстро дать команде рабочий Excel:

- заявка из e-Qazyna;
- дата создания;
- номер документа;
- БИН;
- заявитель;
- тип документа;
- статус;
- данные юрлица из `data.egov.kz`;
- юридический адрес;
- руководитель, если поле есть в наборе;
- ОКЭД / вид деятельности, если поле есть в наборе;
- регион по адресу;
- ссылки на ручной поиск телефона в 2GIS / Google / Яндекс.

## 1. Что фильтруется

По умолчанию выгружаются только строки:

```text
Тип документа = Заявка на разведку ТПИ
Статус заявки = Отправлено на рассмотрение / Принято
```

Страницы e-Qazyna уже отсортированы от новых записей к старым, поэтому для оперативной работы обычно хватает первых 3–10 страниц.

## 2. Источники

- e-Qazyna: `https://minerals.e-qazyna.kz/ru/guest/reestr/doc/list`
- API data.egov.kz: `https://data.egov.kz/pages/samples`
- Набор юрлиц: `https://data.egov.kz/api/v4/gbd_ul/v1?apiKey=yourApiKey`

Для полноценного БИН-обогащения нужен API-ключ от `data.egov.kz`.

## 3. Установка на Windows через VS Code

Открой папку проекта в VS Code.

В терминале PowerShell:

```powershell
python -m venv .venv
. .\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
copy .env.example .env
```

Открой файл `.env` и вставь свой ключ:

```env
EGOV_API_KEY=твой_ключ_data_egov
```

Запуск:

```powershell
python -m eqazyna_excel.main --pages 5
```

Excel появится в папке `exports/`.

## 4. Быстрый запуск через файл

Можно запустить:

```text
scripts/run_export.bat
```

При первом запуске он создаст `.env`. После этого нужно вставить API-ключ и запустить ещё раз.

## 5. Команды

Выгрузить первые 5 страниц:

```bash
python -m eqazyna_excel.main --pages 5
```

Выгрузить первые 10 страниц:

```bash
python -m eqazyna_excel.main --pages 10
```

Выгрузить без eGov-обогащения:

```bash
python -m eqazyna_excel.main --pages 5 --no-egov
```

Сохранить в конкретный файл:

```bash
python -m eqazyna_excel.main --pages 10 --output exports/test.xlsx
```

Изменить статусы:

```bash
python -m eqazyna_excel.main --statuses "Отправлено на рассмотрение,Принято"
```

## 6. Как обновлять регионы

Регион определяется по адресу из `data.egov.kz` через словарь:

```text
config/regions.yaml
```

Если в Excel регион не определился, добавь нужное слово/город/вариант написания в `keywords` соответствующего региона.

Пример:

```yaml
karaganda:
  name: "Карагандинская область"
  keywords:
    - "карагандинская область"
    - "караганда"
    - "темиртау"
```

## 7. Что делать с телефоном

Телефон пока не тянется автоматически. В Excel есть три колонки:

- `Поиск 2GIS`
- `Поиск Google`
- `Поиск Яндекс`

Человек открывает ссылку и проверяет контакты вручную. Это безопаснее для MVP, чем сразу скрейпить 2GIS. Потом можно подключить официальный 2GIS Places API, если будет ключ и разрешение на контактные поля.

## 8. Что делать, если eGov ничего не нашёл

Проверь:

1. В `.env` реально вставлен `EGOV_API_KEY`.
2. Нет лишних пробелов вокруг ключа.
3. Команда запущена не с `--no-egov`.
4. БИН состоит из 12 цифр.
5. API data.egov.kz не лежит. Да, такое бывает. Бюрократическая магия не всегда SLA.

Если обогащение не сработало, заявки всё равно выгружаются: БИН и ссылки на ручной поиск остаются.

## 9. GitHub

Инициализация репозитория:

```bash
git init
git add .
git commit -m "Initial e-Qazyna Excel exporter"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/eqazyna-excel-exporter.git
git push -u origin main
```

Не загружай `.env` в GitHub. Он уже добавлен в `.gitignore`.

## 10. План развития

Версия 1 сейчас:

```text
e-Qazyna → Excel → БИН-обогащение через data.egov.kz → ручной поиск телефона
```

Следующие версии:

```text
v2: SQLite-память, чтобы выгружать только новые заявки
v3: Telegram/email-уведомления
v4: региональная рассылка
v5: 2GIS Places API для автоматического телефона и фактического адреса
```
