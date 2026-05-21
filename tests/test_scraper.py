from eqazyna_excel.scraper import parse_applications, filter_applications

HTML = """
<html><body>
<table>
<tr><th>Дата создания</th><th>Номер документа</th><th>ИИН/БИН заявителя</th><th>Наименование заявителя</th><th>Тип документа</th><th>Статус заявки</th></tr>
<tr><td>20.05.2026 16:38:55</td><td>42445-NEA</td><td>231040024610</td><td>ТОО Mugodzhar Resources</td><td>Заявка на разведку ТПИ</td><td>Отправлено на рассмотрение</td></tr>
<tr><td>20.05.2026 16:17:40</td><td>42441-NOA</td><td>250140009621</td><td>ТОО Ushalyk 111-LTD</td><td>Отчетность ЛКУ</td><td>Отправлено на рассмотрение</td></tr>
</table>
</body></html>
"""


def test_parse_and_filter_table():
    records = parse_applications(HTML, "https://example.test", 1)
    assert len(records) == 2
    filtered = filter_applications(records)
    assert len(filtered) == 1
    assert filtered[0].document_number == "42445-NEA"
