"""Testes das pecas Fritzing: o validador e as duas pecas reais."""
import importlib.util
import sys
import zipfile
from pathlib import Path
from xml.etree import ElementTree

import pytest

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ / "fritzing" / "ferramentas"))

import empacotar  # noqa: E402
import instalar  # noqa: E402
import pecas  # noqa: E402
import previa  # noqa: E402
import validar  # noqa: E402

# O gerador se chama nova-peca.py, com hifen, como novo-projeto.py em
# ferramentas/. Hifen nao passa por import, entao vem pelo importlib.
nova_peca = importlib.util.module_from_spec(
    importlib.util.spec_from_file_location(
        "nova_peca", RAIZ / "fritzing" / "ferramentas" / "nova-peca.py"))
nova_peca.__loader__.exec_module(nova_peca)


def escrever(caminho, texto):
    caminho.parent.mkdir(parents=True, exist_ok=True)
    caminho.write_text(texto, encoding="utf-8")


FZP_MINIMO = """<?xml version="1.0" encoding="UTF-8"?>
<module moduleId="peca-teste">
 <version>1</version>
 <title>Peca de teste</title>
 <description>Peca de teste</description>
 <tags><tag>teste</tag></tags>
 <properties><property name="family">teste</property></properties>
 <views>
  <breadboardView><layers image="breadboard/bb.svg"><layer layerId="breadboard"/></layers></breadboardView>
  <schematicView><layers image="schematic/sc.svg"><layer layerId="schematic"/></layers></schematicView>
  <pcbView><layers image="pcb/pcb.svg"><layer layerId="copper1"/><layer layerId="copper0"/><layer layerId="silkscreen"/></layers></pcbView>
  <iconView><layers image="icon/ic.svg"><layer layerId="icon"/></layers></iconView>
 </views>
 <connectors>
  <connector type="male" name="A" id="connector0">
   <description>A</description>
   <views>
    <breadboardView><p svgId="connector0pin" layer="breadboard"/></breadboardView>
    <schematicView><p svgId="connector0pin" layer="schematic"/></schematicView>
    <pcbView><p svgId="connector0pin" layer="copper0"/><p svgId="connector0pin" layer="copper1"/></pcbView>
   </views>
  </connector>
  <connector type="male" name="B" id="connector1">
   <description>B</description>
   <views>
    <breadboardView><p svgId="connector1pin" layer="breadboard"/></breadboardView>
    <schematicView><p svgId="connector1pin" layer="schematic"/></schematicView>
    <pcbView><p svgId="connector1pin" layer="copper0"/><p svgId="connector1pin" layer="copper1"/></pcbView>
   </views>
  </connector>
 </connectors>
 <buses/>
</module>
"""

BB_MINIMO = """<svg xmlns="http://www.w3.org/2000/svg" width="0.5in" height="0.5in" viewBox="0 0 36 36">
 <g id="breadboard">
  <rect id="connector0pin" x="7.1" y="20" width="1.8" height="10" fill="#8c8c8c"/>
  <rect id="connector1pin" x="14.3" y="20" width="1.8" height="10" fill="#8c8c8c"/>
 </g>
</svg>
"""

SC_MINIMO = """<svg xmlns="http://www.w3.org/2000/svg" width="0.5in" height="0.5in" viewBox="0 0 36 36">
 <g id="schematic">
  <rect id="connector0pin" x="0" y="7.2" width="14.4" height="0.7" fill="#787878"/>
  <rect id="connector1pin" x="0" y="14.4" width="14.4" height="0.7" fill="#787878"/>
 </g>
</svg>
"""

PCB_MINIMO = """<svg xmlns="http://www.w3.org/2000/svg" width="0.5in" height="0.5in" viewBox="0 0 500 500">
 <g id="copper1"><g id="copper0">
  <circle id="connector0pin" cx="100" cy="100" r="27.5" fill="none" stroke="rgb(255, 191, 0)" stroke-width="20"/>
  <circle id="connector1pin" cx="200" cy="100" r="27.5" fill="none" stroke="rgb(255, 191, 0)" stroke-width="20"/>
 </g></g>
 <g id="silkscreen"><rect x="10" y="10" width="480" height="480" fill="none" stroke="#f0f0f0" stroke-width="10"/></g>
</svg>
"""

IC_MINIMO = """<svg xmlns="http://www.w3.org/2000/svg" width="0.3in" height="0.3in" viewBox="0 0 21.6 21.6">
 <g id="icon"><rect x="0" y="0" width="21.6" height="21.6" fill="#1f7a34"/></g>
</svg>
"""


@pytest.fixture
def peca(tmp_path):
    """Peca minima e valida. Cada teste estraga um pedaco e confere a queixa."""
    escrever(tmp_path / "part.fzp", FZP_MINIMO)
    escrever(tmp_path / "svg" / "breadboard" / "bb.svg", BB_MINIMO)
    escrever(tmp_path / "svg" / "schematic" / "sc.svg", SC_MINIMO)
    escrever(tmp_path / "svg" / "pcb" / "pcb.svg", PCB_MINIMO)
    escrever(tmp_path / "svg" / "icon" / "ic.svg", IC_MINIMO)
    return tmp_path


def test_peca_minima_nao_tem_queixa(peca):
    assert validar.problemas(peca) == []


def test_acusa_svg_que_o_fzp_cita_e_nao_existe(peca):
    (peca / "svg" / "icon" / "ic.svg").unlink()
    assert any("icon/ic.svg" in p for p in validar.problemas(peca))


def test_acusa_conector_sem_elemento_no_svg(peca):
    texto = BB_MINIMO.replace('id="connector1pin"', 'id="connector9pin"')
    escrever(peca / "svg" / "breadboard" / "bb.svg", texto)
    assert any("connector1pin" in p and "breadboard" in p for p in validar.problemas(peca))


def test_acusa_svg_sem_viewbox(peca):
    texto = BB_MINIMO.replace('viewBox="0 0 36 36"', "")
    escrever(peca / "svg" / "breadboard" / "bb.svg", texto)
    assert any("viewBox" in p for p in validar.problemas(peca))


def test_acusa_largura_sem_unidade_fisica(peca):
    texto = BB_MINIMO.replace('width="0.5in"', 'width="36px"')
    escrever(peca / "svg" / "breadboard" / "bb.svg", texto)
    assert any("width" in p for p in validar.problemas(peca))


def test_acusa_fonte_fora_da_lista(peca):
    texto = SC_MINIMO.replace(
        "</g>", '<text x="1" y="1" font-family="Arial" font-size="5">x</text></g>'
    )
    escrever(peca / "svg" / "schematic" / "sc.svg", texto)
    assert any("Arial" in p for p in validar.problemas(peca))


def test_aceita_noto_sans(peca):
    texto = SC_MINIMO.replace(
        "</g>", '<text x="1" y="1" font-family="Noto Sans" font-size="5">x</text></g>'
    )
    escrever(peca / "svg" / "schematic" / "sc.svg", texto)
    assert validar.problemas(peca) == []


def test_acusa_id_duplicado_no_mesmo_svg(peca):
    texto = BB_MINIMO.replace('id="connector1pin"', 'id="connector0pin"')
    escrever(peca / "svg" / "breadboard" / "bb.svg", texto)
    assert any("duplicado" in p for p in validar.problemas(peca))


def test_acusa_propriedade_vazia(peca):
    texto = FZP_MINIMO.replace(
        '<property name="family">teste</property>',
        '<property name="family">teste</property><property name="mpn"></property>',
    )
    escrever(peca / "part.fzp", texto)
    assert any("mpn" in p for p in validar.problemas(peca))


def test_acusa_barramento_com_conector_inexistente(peca):
    texto = FZP_MINIMO.replace(
        "<buses/>",
        '<buses><bus id="dados"><nodeMember connectorId="connector7"/></bus></buses>',
    )
    escrever(peca / "part.fzp", texto)
    assert any("connector7" in p for p in validar.problemas(peca))


def test_acusa_terminalid_declarado(peca):
    """A 1.0.3 calcula o terminal sozinho; declarar a mao e a causa mais comum
    de terminal invisivel, que e o defeito classico de peca caseira."""
    texto = FZP_MINIMO.replace(
        '<p svgId="connector0pin" layer="schematic"/>',
        '<p svgId="connector0pin" terminalId="connector0terminal" layer="schematic"/>',
    )
    escrever(peca / "part.fzp", texto)
    assert any("terminalId" in p for p in validar.problemas(peca))


def test_acusa_passo_fora_da_grade_no_breadboard(peca):
    """7,2 unidades e o passo de 0,1 polegada. Fora disso a peca nao encaixa."""
    texto = BB_MINIMO.replace('x="14.3"', 'x="13.0"')
    escrever(peca / "svg" / "breadboard" / "bb.svg", texto)
    assert any("passo" in p for p in validar.problemas(peca))


def ordem_da_barra(pasta, svg, conectores):
    """Nomes dos pinos da barra, da esquerda para a direita na vista de cima."""
    peca = RAIZ / "fritzing" / "pecas" / pasta
    fzp = ElementTree.parse(peca / "part.fzp").getroot()
    bb = ElementTree.parse(peca / "svg" / "breadboard" / svg).getroot()
    # Os furos sao circulos, entao a posicao vem de cx e nao de x.
    x_de = {e.get("id"): float(e.get("cx")) for e in bb.iter() if e.get("cx") and e.get("id")}
    nome_de = {c.get("id"): c.get("name") for c in fzp.iter("connector")}
    return [nome_de[c] for c in sorted(conectores, key=lambda c: x_de[c + "pin"])]


def test_transmissor_nao_tem_queixa():
    assert validar.problemas(RAIZ / "fritzing" / "pecas" / "rf433-tx") == []


def test_transmissor_tem_a_ordem_de_pinos_conferida_na_plaquinha():
    """DATA VCC GND da esquerda para a direita, vista de cima. Trocar isto
    liga alimentacao no lugar errado."""
    ordem = ordem_da_barra(
        "rf433-tx",
        "rf433_tx_breadboard.svg",
        ["connector0", "connector1", "connector2"],
    )
    assert ordem == ["DATA", "VCC", "GND"]


def test_receptor_nao_tem_queixa():
    assert validar.problemas(RAIZ / "fritzing" / "pecas" / "rf433-rx") == []


def test_receptor_tem_a_ordem_espelhada_da_serigrafia():
    """De cima e VCC DATA DATA GND. A serigrafia fica no verso, e ler o verso
    sem espelhar troca alimentacao com terra."""
    ordem = ordem_da_barra(
        "rf433-rx",
        "rf433_rx_breadboard.svg",
        ["connector0", "connector1", "connector2", "connector3"],
    )
    assert ordem == ["VCC", "DATA", "DATA2", "GND"]


def test_receptor_liga_os_dois_data_em_barramento():
    """Sao o mesmo ponto na placa. Sem o barramento o Fritzing acusa
    conexao faltando quando so um DATA e usado."""
    fzp = ElementTree.parse(RAIZ / "fritzing" / "pecas" / "rf433-rx" / "part.fzp").getroot()
    membros = {m.get("connectorId") for m in fzp.iter("nodeMember")}
    assert membros == {"connector1", "connector2"}


def test_empacota_com_os_nomes_planos_que_o_fritzing_espera(tmp_path, peca):
    destino = empacotar.empacotar(peca, tmp_path / "Peca.fzpz")
    nomes = set(zipfile.ZipFile(destino).namelist())
    assert nomes == {
        "part.peca-teste.fzp",
        "svg.breadboard.bb.svg",
        "svg.schematic.sc.svg",
        "svg.pcb.pcb.svg",
        "svg.icon.ic.svg",
    }


def test_recusa_empacotar_peca_com_problema(tmp_path, peca):
    (peca / "svg" / "icon" / "ic.svg").unlink()
    with pytest.raises(ValueError, match="icon/ic.svg"):
        empacotar.empacotar(peca, tmp_path / "Peca.fzpz")


def _lf(dados):
    return dados.replace(b"\r\n", b"\n")


def test_os_fzpz_publicados_estao_em_dia_com_os_fontes():
    """Editar uma SVG e esquecer de rodar empacotar.py deixa dist/ velho em
    silencio: o zip continua la, com o desenho antigo dentro."""
    for origem in pecas.descobrir():
        nome = pecas.nome_do_pacote(origem)
        publicado = zipfile.ZipFile(pecas.DIST / nome)
        conteudo = {n: _lf(publicado.read(n)) for n in publicado.namelist()}

        # O .gitattributes normaliza os fontes para LF, mas o .fzpz e binario
        # e guarda os bytes como estavam. Comparar sem normalizar faria o teste
        # falhar num clone novo, sem nenhuma peca ter mudado.
        fzp = origem / "part.fzp"
        fonte = {f"part.{pecas.module_id(origem)}.fzp": _lf(fzp.read_bytes())}
        for arquivo in (origem / "svg").rglob("*.svg"):
            fonte[f"svg.{arquivo.parent.name}.{arquivo.name}"] = _lf(arquivo.read_bytes())

        assert conteudo == fonte, (
            f"{nome} esta velho; rode python fritzing/ferramentas/empacotar.py")


def test_instala_no_layout_de_pastas_da_biblioteca_do_fritzing(tmp_path, peca):
    """O Fritzing procura o FZP em parts/user/<moduleid>.fzp e as SVGs em
    parts/svg/user/<vista>/. Fora desse layout ele nao acha a peca."""
    escritos = instalar.instalar(peca, tmp_path)
    relativos = sorted(str(c.relative_to(tmp_path)).replace("\\", "/") for c in escritos)
    assert relativos == [
        "svg/user/breadboard/bb.svg",
        "svg/user/icon/ic.svg",
        "svg/user/pcb/pcb.svg",
        "svg/user/schematic/sc.svg",
        "user/peca-teste.fzp",
    ]


def test_instalar_recusa_peca_com_problema(tmp_path, peca):
    (peca / "svg" / "icon" / "ic.svg").unlink()
    with pytest.raises(ValueError, match="icon/ic.svg"):
        instalar.instalar(peca, tmp_path)


# ------------------------------------------------------------ gerador de peca


def test_peca_gerada_nasce_valida(tmp_path):
    """O gerador so vale a pena se o que ele cospe passa no validador sem
    ninguem tocar. E o unico teste que importa de verdade aqui."""
    pasta = nova_peca.criar("hc-sr04", 45, 20, ["VCC", "TRIG", "ECHO", "GND"], tmp_path)
    assert validar.problemas(pasta) == []


def test_gerador_poe_os_furos_no_passo_de_um_decimo_de_polegada(tmp_path):
    pasta = nova_peca.criar("tres-pinos", 20, 20, ["A", "B", "C"], tmp_path)
    bb = ElementTree.parse(
        pasta / "svg" / "breadboard" / "tres_pinos_breadboard.svg").getroot()
    cx = sorted(float(e.get("cx")) for e in bb.iter()
                if e.get("id", "").startswith("connector"))
    assert [round(b - a, 3) for a, b in zip(cx, cx[1:])] == [7.2, 7.2]


def test_gerador_liga_pino_repetido_em_barramento(tmp_path):
    """Nome repetido quer dizer o mesmo ponto na placa. Foi a licao do MX-05V,
    e agora o gerador ja nasce sabendo."""
    pasta = nova_peca.criar("rx-generico", 30, 14,
                            ["VCC", "DATA", "DATA", "GND"], tmp_path)
    fzp = ElementTree.parse(pasta / "part.fzp").getroot()
    nomes = [c.get("name") for c in fzp.iter("connector")]
    assert nomes == ["VCC", "DATA", "DATA2", "GND"]
    assert {m.get("connectorId") for m in fzp.iter("nodeMember")} == {
        "connector1", "connector2"}
    assert validar.problemas(pasta) == []


def test_gerador_recusa_placa_pequena_demais_para_os_pinos(tmp_path):
    with pytest.raises(ValueError, match="nao cabem"):
        nova_peca.criar("apertada", 8, 10, ["A", "B", "C", "D"], tmp_path)


def test_gerador_recusa_sobrescrever_peca_existente(tmp_path):
    nova_peca.criar("repetida", 20, 20, ["A", "B"], tmp_path)
    with pytest.raises(ValueError, match="ja existe"):
        nova_peca.criar("repetida", 20, 20, ["A", "B"], tmp_path)


def test_peca_gerada_empacota_e_instala(tmp_path):
    """Fecha o circuito: o que o gerador cria passa pelas outras ferramentas."""
    pasta = nova_peca.criar("ponta-a-ponta", 25, 15, ["VCC", "SIG", "GND"], tmp_path)
    zip_ = empacotar.empacotar(pasta, tmp_path / "saida" / "P.fzpz")
    assert len(zipfile.ZipFile(zip_).namelist()) == 5
    assert len(instalar.instalar(pasta, tmp_path / "biblioteca")) == 5


def test_previa_lista_todas_as_pecas(tmp_path):
    destino = tmp_path / "previa.html"
    _, quantas = previa.gerar(destino)
    pagina = destino.read_text(encoding="utf-8")
    assert quantas == len(pecas.descobrir())
    for peca in pecas.descobrir():
        assert f'src="pecas/{peca.name}/svg/breadboard/' in pagina


def test_previa_tira_o_tamanho_do_proprio_svg(tmp_path):
    """Escrever os pixels a mao era errar em silencio, mostrando o desenho
    esticado. Agora eles saem do width e height declarados."""
    destino = tmp_path / "previa.html"
    previa.gerar(destino)
    pagina = destino.read_text(encoding="utf-8")
    # rf433-tx tem 0,74803 pol de lado e o breadboard vai ampliado 4x.
    assert f'width="{round(0.74803 * 96 * 4)}" height="{round(0.74803 * 96 * 4)}"' in pagina
