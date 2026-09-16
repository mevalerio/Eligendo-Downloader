from app.scraper import parse_page_html


URL = (
    "https://elezionistorico.interno.gov.it/index.php?tpel=A&dtel=02/06/1946"
    "&tpa=I&tpe=C&ne1=20&ne2=33&ne3=330190&lev3=190"
)

HTML = """
<div id="headEnti"><h3>
  Assemblea costituente 02/06/1946 <i></i>
  Area ITALIA <i></i> Circoscrizione ROMA-VITERBO-LATINA-FROSINONE <i></i>
  Provincia FROSINONE <i></i> Comune CASSINO
</h3></div>
<table class="dati_riepilogo"><tr><th>Affluenza</th></tr>
  <tr><th>Elettori</th><td>7.697</td><td></td></tr>
  <tr><th>Votanti</th><td>5.784</td><td class="percentuale">75,15 %</td></tr>
</table>
<table class="dati_riepilogo"><tr><th>Schede</th></tr>
  <tr><th>Bianche</th><td>413</td></tr>
  <tr><th>Non valide (bianche incl.)</th><td>1.105</td></tr>
</table>
<table class="dati" summary="Risultati elezione"><tbody>
  <tr><td><img src="/symbols/dc.png"></td><th id="lista0" class="candidato">DC</th>
      <td headers="hvoti lista0">1.578</td>
      <td headers="hpercentuale lista0">33,73</td></tr>
  <tr class="totalecomplessivovoti"><th>TOTALI</th><td></td>
      <td headers="hvoti">4.679</td><td></td></tr>
</tbody></table>
"""


def test_parse_1946_page() -> None:
    result = parse_page_html(HTML, URL)

    assert result.election.code == "A"
    assert result.election.date.isoformat() == "1946-06-02"
    assert result.geography.comune == "CASSINO"
    assert result.geography.provincia == "FROSINONE"
    assert result.summary["elettori"] == 7697
    assert result.summary["votanti_percentuale"] == 75.15
    assert result.summary["non_valide_bianche_incl"] == 1105
    assert result.records[0].record_type == "list"
    assert result.records[0].name == "DC"
    assert result.records[0].votes == 1578
    assert result.records[0].percentage == 33.73
    assert result.records[0].symbol_url.endswith("/symbols/dc.png")
    assert result.records[1].record_type == "total"


def test_parse_candidate_and_linked_list() -> None:
    html = """
    <div id="headEnti"><h3>Comunali 03/10/2021 <i></i> Area ITALIA
      <i></i> Regione PIEMONTE <i></i> Provincia NOVARA <i></i> Comune NOVARA
    </h3></div>
    <table class="dati" summary="Risultato elezione"><tbody>
      <tr class="leader"><td id="candidato0">CANELLI ALESSANDRO</td>
        <td class="text-left">Eletto sind.</td><td headers="hvoti candidato0">28.204</td>
        <td headers="hpercentuale candidato0">69,59</td></tr>
      <tr><td></td><th id="lista0_0" class="candidato" headers="hlista candidato0">LEGA</th>
        <td headers="hvoti candidato0 lista0_0">8.852</td>
        <td headers="hpercentuale candidato0 lista0_0">23,22</td>
        <td headers="hseggi candidato0 lista0_0">8</td></tr>
    </tbody></table>
    """
    result = parse_page_html(html, URL.replace("tpel=A", "tpel=G"))
    assert result.records[0].record_type == "candidate"
    assert result.records[0].status == "Eletto sind."
    assert result.records[1].parent_id == "candidato0"
    assert result.records[1].seats == 8
