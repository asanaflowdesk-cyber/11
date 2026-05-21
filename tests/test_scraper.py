from eqazyna_export.scraper import filter_records, parse_html_page


def test_parse_table_and_filter():
    html = """
    <table><tbody>
      <tr><th>Дата создания</th><th>Номер документа</th><th>ИИН/БИН заявителя</th><th>Наименование заявителя</th><th>Тип документа</th><th>Статус заявки</th></tr>
      <tr><td>21.05.2026 02:31:42</td><td>42458-NEA</td><td>241140027214</td><td>ТОО Конор</td><td>Заявка на разведку ТПИ</td><td>Отправлено на рассмотрение</td></tr>
      <tr><td>20.05.2026 20:45:42</td><td>42454-NOA</td><td>241040029722</td><td>ТОО BOSAGA</td><td>Отчетность ЛКУ</td><td>Отправлено на рассмотрение</td></tr>
    </tbody></table>
    """
    rows = parse_html_page(html, "https://example.test")
    assert len(rows) == 2
    filtered = filter_records(rows)
    assert len(filtered) == 1
    assert filtered[0].bin_iin == "241140027214"
