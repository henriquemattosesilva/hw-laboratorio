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


ESP32_S3_CIMA = ["GND", "TX", "RX", "1", "2", "42", "41", "40", "39", "38", "37",
                 "36", "35", "0", "45", "48", "47", "21", "20", "19", "GND2", "GND3"]
ESP32_S3_BAIXO = ["3V3", "3V32", "RST", "4", "5", "6", "7", "15", "16", "17", "18",
                  "8", "3", "46", "9", "10", "11", "12", "13", "14", "5VIN", "GND4"]


def test_esp32_s3_nao_tem_queixa():
    assert validar.problemas(RAIZ / "fritzing" / "pecas" / "esp32-s3-n16r8") == []


def test_esp32_s3_tem_a_pinagem_lida_na_serigrafia():
    """Os 44 nomes foram lidos na placa e conferidos um a um. E o dado mais caro
    da peca: sao dois GPIO seguidos que nao querem dizer nada um para o outro, e
    um erro de uma posicao poe 5 V onde deveria entrar sinal."""
    arquivo = "esp32_s3_n16r8_breadboard.svg"
    cima = ordem_da_barra("esp32-s3-n16r8", arquivo,
                          [f"connector{i}" for i in range(22)])
    baixo = ordem_da_barra("esp32-s3-n16r8", arquivo,
                           [f"connector{i}" for i in range(22, 44)])
    assert cima == ESP32_S3_CIMA
    assert baixo == ESP32_S3_BAIXO


def test_esp32_s3_tem_as_fileiras_a_0_9_polegada():
    """0,9 pol e o que deixa uma coluna livre de cada lado na protoboard. A
    LoLin v3, a 1,1 pol, nao deixa nenhuma — e a diferenca que se sente."""
    bb = ElementTree.parse(
        RAIZ / "fritzing" / "pecas" / "esp32-s3-n16r8" / "svg" / "breadboard"
        / "esp32_s3_n16r8_breadboard.svg").getroot()
    y = {e.get("id"): float(e.get("cy")) for e in bb.iter() if e.get("cy") and e.get("id")}
    assert round(y["connector22pin"] - y["connector0pin"], 3) == 64.8


def test_esp32_s3_liga_os_gnd_e_os_3v3_em_barramento():
    """Quatro GND e dois 3V3, todos o mesmo ponto na placa."""
    fzp = ElementTree.parse(
        RAIZ / "fritzing" / "pecas" / "esp32-s3-n16r8" / "part.fzp").getroot()
    barras = {b.get("id"): {m.get("connectorId") for m in b.iter("nodeMember")}
              for b in fzp.iter("bus")}
    assert barras["gnd"] == {"connector0", "connector20", "connector21", "connector43"}
    assert barras["3v3"] == {"connector22", "connector23"}


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
        publicado = zipfile.ZipFile(pecas.pacote(origem))
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


def test_gerador_aceita_fileira_que_quase_lota_a_borda(tmp_path):
    """A ESP32-S3 poe 22 furos numa borda de 57 mm e sobra 1,8 mm de cada ponta,
    menos que o recuo padrao da fileira. E a cota da placa de verdade: o que
    reprova e o furo sair da placa, nao o recuo ficar folgado."""
    pasta = nova_peca.criar("quase-lotada", 57, 28, [str(i) for i in range(22)],
                            tmp_path)
    assert validar.problemas(pasta) == []


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


def test_gerador_poe_a_fileira_na_borda_curta(tmp_path):
    """Modulo com o conector na ponta, como o buzzer P15: a fileira corre na
    vertical, e o passo passa a valer em y."""
    pasta = nova_peca.criar("na-ponta", 32, 15, ["GND", "SINAL"], tmp_path,
                            lado="esquerda")
    bb = ElementTree.parse(
        pasta / "svg" / "breadboard" / "na_ponta_breadboard.svg").getroot()
    furos = [(float(e.get("cx")), float(e.get("cy"))) for e in bb.iter()
             if (e.get("id") or "").startswith("connector")]
    assert len({x for x, _ in furos}) == 1, "os furos deviam estar na mesma coluna"
    ys = sorted(y for _, y in furos)
    assert round(ys[1] - ys[0], 3) == 7.2
    assert validar.problemas(pasta) == []


def test_validador_mede_o_passo_em_linha_reta(tmp_path, peca):
    """Medir so no eixo x veria zero na fileira vertical e deixaria passar
    qualquer espacamento errado."""
    torto = BB_MINIMO.replace('x="7.1" y="20"', 'x="7.1" y="20"').replace(
        'x="14.3" y="20"', 'x="7.1" y="26.0"')
    escrever(peca / "svg" / "breadboard" / "bb.svg", torto)
    assert any("passo" in p for p in validar.problemas(peca))


def test_gerador_recusa_lado_e_cor_desconhecidos(tmp_path):
    with pytest.raises(ValueError, match="lado"):
        nova_peca.criar("x1", 20, 20, ["A"], tmp_path, lado="diagonal")
    with pytest.raises(ValueError, match="cor"):
        nova_peca.criar("x2", 20, 20, ["A"], tmp_path, cor="roxa")


def test_gerador_pinta_a_placa(tmp_path):
    pasta = nova_peca.criar("azulzinha", 20, 20, ["A", "B"], tmp_path, cor="azul")
    bb = (pasta / "svg" / "breadboard" / "azulzinha_breadboard.svg").read_text("utf-8")
    assert "#1c4f8c" in bb and "#1f7a34" not in bb


def test_o_pacote_importavel_fica_dentro_da_pasta_da_peca():
    """O part.fzp sozinho nao importa no Fritzing: ele cita as SVGs por caminho
    relativo, e quem junta tudo e o .fzpz. Os dois ficam lado a lado para quem
    abre a pasta da peca achar o que precisa sem procurar em outro lugar."""
    for peca in pecas.descobrir():
        pacote = pecas.pacote(peca)
        assert pacote.parent == peca, f"{pacote} devia estar dentro de {peca}"
        assert pacote.exists(), f"{pacote.name} nao existe; rode empacotar.py"


def test_gerador_faz_placa_de_duas_fileiras(tmp_path):
    """Placa de desenvolvimento tem duas fileiras, e o vao entre elas decide se
    a peca encaixa. Aqui: 1,1 polegada, que e a NodeMCU larga."""
    pasta = nova_peca.criar(
        "duas-fileiras", 59, 31, None, tmp_path, vao=27.94, alinhar="centro",
        fileiras=[("cima", ["D0", "D1", "D2"]), ("baixo", ["A0", "G", "VU"])])
    bb = ElementTree.parse(
        pasta / "svg" / "breadboard" / "duas_fileiras_breadboard.svg").getroot()
    furos = {e.get("id"): (float(e.get("cx")), float(e.get("cy")))
             for e in bb.iter() if (e.get("id") or "").startswith("connector")}
    assert len(furos) == 6
    ys = sorted({round(y, 2) for _, y in furos.values()})
    assert len(ys) == 2
    assert round((ys[1] - ys[0]) / 2.834646, 2) == 27.94   # o vao pedido, em mm
    assert round((ys[0] + ys[1]) / 2 / 2.834646, 2) == 15.5  # simetricas no meio
    assert validar.problemas(pasta) == []


def test_gerador_recusa_vao_fora_da_grade(tmp_path):
    """Vao fora de multiplo de 0,1 polegada e peca que nao senta na protoboard,
    e nada mais acusaria isso."""
    with pytest.raises(ValueError, match="nao encaixaria"):
        nova_peca.criar("torta", 59, 31, None, tmp_path, vao=25.0,
                        fileiras=[("cima", ["A"]), ("baixo", ["B"])])


def test_validador_confere_o_passo_dentro_de_cada_fileira(tmp_path, peca):
    """Com duas fileiras, medir a distancia entre conectores quaisquer acharia
    todo vizinho longe demais e o passo deixaria de ser conferido."""
    torto = BB_MINIMO.replace(
        '<rect id="connector1pin" x="14.3" y="20"',
        '<rect id="connector1pin" x="13.0" y="20"').replace(
        "</g>",
        '<rect id="connector2pin" x="7.1" y="2" width="1.8" height="10" fill="#8c8c8c"/>'
        '<rect id="connector3pin" x="14.3" y="2" width="1.8" height="10" fill="#8c8c8c"/></g>')
    escrever(peca / "svg" / "breadboard" / "bb.svg", torto)
    assert any("passo" in p for p in validar.problemas(peca))
