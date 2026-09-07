"""Cria uma peca Fritzing nova, com a geometria ja certa.

  python fritzing/ferramentas/nova-peca.py hc-sr04 --mm 45x20 \
         --pinos VCC,TRIG,ECHO,GND --titulo "Sensor ultrassonico HC-SR04"

Placa de desenvolvimento tem duas fileiras, uma em cada borda longa:

  python fritzing/ferramentas/nova-peca.py nodemcu --mm 59x31 --vao 27.94 \
         --fileira cima:D0,D1,D2 --fileira baixo:A0,G,VU

Sai uma peca completa e valida: as vistas, os furos no passo de 0,1 polegada,
o viewBox na unidade certa de cada vista e o FZP com os conectores. Falta so o
ornamento — o desenho dos componentes da placa, que nenhum gerador tem como
adivinhar. Cada SVG diz onde ele entra.

O que o gerador resolve e justamente a parte que da errado em silencio: unidade
do viewBox, passo dos furos, ordem dos conectores e o barramento de pinos
repetidos. Ornamento errado se ve na previa; passo errado so aparece quando a
peca nao encaixa.

**Pino repetido vira barramento.** `--pinos VCC,DATA,DATA,GND` cria DATA e
DATA2 e os declara ligados, porque nome repetido quer dizer o mesmo ponto na
placa. Sem isso o Fritzing acusaria conexao faltando ao usar so um deles. Numa
placa com varios GND e varios 3V isso sai de graca e e o comportamento certo:
eles sao mesmo o mesmo ponto.

**`--vao` e a cota que decide se a peca encaixa.** E a distancia entre as duas
fileiras, de centro a centro, e precisa ser multiplo de 0,1". Sem ela as
fileiras ficam a BORDA_MM da borda, que serve para modulo pequeno e nao para
placa de desenvolvimento.
"""
import argparse
import re
import sys
from pathlib import Path

import pecas
import validar

MM = 2.834646    # unidades por milimetro no breadboard, esquema e icone (72/pol)
MIL = 39.3701    # unidades por milimetro no pcb (1000/pol)
PASSO_MM = 2.54  # 0,1 polegada
BORDA_MM = 2.2   # recuo padrao da fileira, do centro do furo ate a borda
MIN_BORDA_MM = 1.2  # o minimo fisico: menos que isso o furo sai da placa
MARGEM_MM = 3.2  # da borda ate o primeiro furo

METAL, FURO = "#c9c9c9", "#3a3a3a"

# Cor da placa, com a borda mais escura e a tinta da serigrafia.
CORES = {
    "verde": ("#1f7a34", "#14562a", "#ffffff"),
    "azul": ("#1c4f8c", "#123566", "#ffffff"),
    "vermelha": ("#8c2020", "#5e1414", "#ffffff"),
    "preta": ("#1e1e1e", "#000000", "#e8e8e8"),
    "branca": ("#e4e4e4", "#b0b0b0", "#333333"),
    "amarela": ("#b8901c", "#856612", "#ffffff"),
}

LADOS = ("baixo", "cima", "esquerda", "direita")
ALINHAMENTOS = ("inicio", "centro", "fim")
OPOSTO = {"baixo": "cima", "cima": "baixo", "esquerda": "direita", "direita": "esquerda"}

ALIMENTACAO = {"VCC", "VDD", "V+", "5V", "3V3", "3.3V", "VIN", "VBAT", "3V", "VU"}
TERRA = {"GND", "GROUND", "VSS", "0V", "-", "G"}
DIREITA = {"ANT", "ANTENNA", "RF"}


def posicoes(larg, alt, n, lado, alinhar="inicio", vao=None):
    """Centro de cada furo em milimetros, na ordem em que os pinos foram dados.

    Fileira em cima ou embaixo corre da esquerda para a direita; nas bordas
    curtas corre de cima para baixo. E a ordem em que se le a serigrafia.

    `alinhar` decide onde a fileira encosta na borda. Header longo em borda
    longa costuma ficar encostado no comeco, que e o padrao; conector de dois
    pinos na ponta da placa costuma ficar centrado.

    `vao` e a distancia entre as duas fileiras opostas, de centro a centro.
    Dado, ele manda: as fileiras ficam simetricas em relacao ao meio da placa.
    Sem ele, cada fileira fica a BORDA_MM da sua borda.
    """
    corrida = (n - 1) * PASSO_MM
    if lado in ("baixo", "cima"):
        livre = larg
        fixo = ((alt + vao) / 2 if lado == "baixo" else (alt - vao) / 2) \
            if vao is not None else (alt - BORDA_MM if lado == "baixo" else BORDA_MM)
    else:
        livre = alt
        fixo = ((larg + vao) / 2 if lado == "direita" else (larg - vao) / 2) \
            if vao is not None else (BORDA_MM if lado == "esquerda" else larg - BORDA_MM)

    if alinhar == "centro" or MARGEM_MM * 2 + corrida > livre:
        a0 = (livre - corrida) / 2
    elif alinhar == "fim":
        a0 = livre - MARGEM_MM - corrida
    else:
        a0 = MARGEM_MM

    if lado in ("baixo", "cima"):
        return [(a0 + i * PASSO_MM, fixo) for i in range(n)]
    return [(fixo, a0 + i * PASSO_MM) for i in range(n)]


# ---------------------------------------------------------------- conectores

def nomear(nomes):
    """Desambigua nome repetido: VCC,DATA,DATA,GND vira VCC,DATA,DATA2,GND."""
    vistos, saida = {}, []
    for nome in nomes:
        vistos[nome] = vistos.get(nome, 0) + 1
        saida.append(nome if vistos[nome] == 1 else f"{nome}{vistos[nome]}")
    return saida


def barramentos(originais, nomeados):
    """Agrupa os conectores que vieram do mesmo nome. Nome repetido e o mesmo
    ponto na placa, e sem barramento o Fritzing acusa conexao faltando."""
    grupos = {}
    for i, bruto in enumerate(originais):
        grupos.setdefault(bruto, []).append(i)
    return {nome: idx for nome, idx in grupos.items() if len(idx) > 1}


# -------------------------------------------------------------------- vistas

DESLOCA = {"baixo": (0, -4.6, "middle"), "cima": (0, 6.6, "middle"),
           "esquerda": (3.6, 1.0, "start"), "direita": (-3.6, 1.0, "end")}


def breadboard(cfg):
    larg, alt = cfg["larg"] * MM, cfg["alt"] * MM
    r_pad, r_furo, tam_rotulo = 2.4, 1.15, 2.4
    tinta = cfg["tinta"]

    corpo = [
        f'  <rect x="0" y="0" width="{larg:.3f}" height="{alt:.3f}" rx="1.5"'
        f' fill="{cfg["placa"]}"/>',
        f'  <rect x="0.4" y="0.4" width="{larg - 0.8:.3f}" height="{alt - 0.8:.3f}" rx="1.2"',
        f'        fill="none" stroke="{cfg["borda"]}" stroke-width="0.8"/>',
        "",
        "  <!-- O ornamento entra aqui: os componentes da placa, sem id nenhum para",
        "       nao colidir com os conectores. Ver CONVENCOES.md. -->",
        "",
    ]

    for fileira in cfg["fileiras"]:
        dx, dy, ancora = DESLOCA[fileira["lado"]]
        for i, nome in zip(fileira["indices"], fileira["nomes"]):
            cx, cy = (v * MM for v in cfg["furos"][i])
            corpo += [
                f'  <text x="{cx + dx:.3f}" y="{cy + dy:.3f}" font-family="Noto Sans"'
                f' font-size="{tam_rotulo}" fill="{tinta}"'
                f' text-anchor="{ancora}">{nome}</text>',
                f'  <circle id="connector{i}pin" cx="{cx:.3f}" cy="{cy:.3f}" r="{r_pad}"'
                f' fill="{METAL}" stroke="none"/>',
                f'  <circle cx="{cx:.3f}" cy="{cy:.3f}" r="{r_furo}" fill="{FURO}"/>',
            ]

    if cfg["ant"]:
        i, cx, cy = cfg["indice_ant"], larg - 4.0 * MM, 4.0 * MM
        corpo += [
            f'  <circle id="connector{i}pin" cx="{cx:.3f}" cy="{cy:.3f}" r="{r_pad}"'
            f' fill="{METAL}" stroke="none"/>',
            f'  <circle cx="{cx:.3f}" cy="{cy:.3f}" r="{r_furo}" fill="{FURO}"/>',
            f'  <text x="{cx:.3f}" y="{cy + 7.2:.3f}" font-family="Noto Sans"'
            f' font-size="2.8" fill="{tinta}" text-anchor="middle">ANT</text>',
        ]

    corpo += rotulo_da_placa(cfg, larg, alt, r_pad, tam_rotulo)

    lados = " e ".join(f["lado"] for f in cfg["fileiras"])
    cabeca = (f'<!-- {cfg["titulo"]}, vista de cima. Placa de {cfg["larg"]:g} x '
              f'{cfg["alt"]:g} mm, conectores na borda de {lados}.\n'
              f'     72 unidades por polegada: 1 mm = 2,834646 u e o passo de 0,1" = 7,2 u.\n'
              f'     Furo de encaixe, sem pino saindo: e assim que o fio entra. -->')
    return svg(cabeca, larg, alt, "breadboard", corpo)


def rotulo_da_placa(cfg, larg, alt, r_pad, tam_rotulo):
    """Poe o nome da peca no espaco que as fileiras deixaram livre."""
    nome = cfg["rotulo"]
    lados = {f["lado"] for f in cfg["fileiras"]}

    # Duas fileiras opostas deixam o meio da placa livre, e e la que o nome vai.
    if len(lados) > 1:
        tam = min(3.2, (larg - 8) / (len(nome) * 0.62))
        return [f'  <text x="{larg / 2:.3f}" y="{alt / 2 + tam * 0.36:.3f}"'
                f' font-family="Noto Sans" font-size="{tam:.2f}" fill="{cfg["tinta"]}"'
                f' text-anchor="middle">{nome}</text>']

    lado = cfg["fileiras"][0]["lado"]
    furos = [(x * MM, y * MM) for x, y in cfg["furos"][: len(cfg["fileiras"][0]["nomes"])]]
    largo_rotulos = max(len(p) for p in cfg["pinos"]) * 0.62 * tam_rotulo
    xs = [x for x, _ in furos]

    if lado in ("baixo", "cima"):
        x0, x1 = max(xs) + r_pad + 2.5, larg - 2.0
        cy = furos[0][1] + 1.0
    elif lado == "esquerda":
        x0, x1 = max(xs) + r_pad + 1.2 + largo_rotulos + 2.0, larg - 2.0
        cy = alt / 2 + 1.0
    else:
        x0, x1 = 2.0, min(xs) - r_pad - 1.2 - largo_rotulos - 2.0
        cy = alt / 2 + 1.0

    sobra = x1 - x0
    if sobra < 14:
        return [f'  <text x="{larg / 2:.3f}" y="{alt / 2 + 1.2:.3f}"'
                f' font-family="Noto Sans" font-size="3.0" fill="{cfg["tinta"]}"'
                f' text-anchor="middle">{nome}</text>']
    tam = min(3.2, sobra / (len(nome) * 0.62))
    return [f'  <text x="{(x0 + x1) / 2:.3f}" y="{cy:.3f}" font-family="Noto Sans"'
            f' font-size="{tam:.2f}" fill="{cfg["tinta"]}"'
            f' text-anchor="middle">{nome}</text>']


def _fatia_schematic(cfg):
    """Reparte os conectores entre os lados da caixa do esquema.

    Com duas fileiras, cada fileira vira um lado: e o que faz o esquema lembrar
    a placa na bancada. Com uma so, alimentacao vai para cima e para baixo e o
    resto para a esquerda, que e o desenho classico de modulo pequeno.
    """
    if len(cfg["fileiras"]) > 1:
        lados = ["esquerda", "direita", "esquerda", "direita"]
        esquerda, direita = [], []
        for ordem, fileira in enumerate(cfg["fileiras"]):
            destino = esquerda if lados[ordem] == "esquerda" else direita
            destino += list(zip(fileira["indices"], fileira["nomes"]))
        if cfg["ant"]:
            direita.append((cfg["indice_ant"], "ANT"))
        return None, None, esquerda, direita

    topo = baixo = None
    esquerda, direita = [], []
    for i, nome in enumerate(cfg["pinos"]):
        base = re.sub(r"\d+$", "", nome).upper()
        if topo is None and base in ALIMENTACAO:
            topo = (i, nome)
        elif baixo is None and base in TERRA:
            baixo = (i, nome)
        elif base in DIREITA:
            direita.append((i, nome))
        else:
            esquerda.append((i, nome))
    if cfg["ant"]:
        direita.append((cfg["indice_ant"], "ANT"))
    return topo, baixo, esquerda, direita


def schematic(cfg):
    pino = 14.4
    topo, baixo, esquerda, direita = _fatia_schematic(cfg)
    linhas = max(len(esquerda), len(direita))
    # Fileira longa em passo de 0,2" faria uma caixa de tres polegadas. O passo
    # de 0,1" continua na grade do esquema e cabe na tela.
    passo = 7.2 if linhas > 8 else 14.4
    caixa_h = max(43.2, passo * (linhas + 1))
    caixa_x, caixa_y = 14.4, 14.4
    caixa_w = 64.8 if linhas > 8 else 50.4
    larg, alt = caixa_x + caixa_w + pino, caixa_y + caixa_h + pino

    corpo = [
        f'  <rect x="{caixa_x}" y="{caixa_y}" width="{caixa_w}" height="{caixa_h:.1f}"',
        '        fill="none" stroke="#000000" stroke-width="0.9"',
        '        stroke-linecap="round" stroke-linejoin="round"/>',
        "",
    ]
    tam_rotulo = 4 if passo > 7.2 else 3.2

    def horizontal(i, nome, y, esq):
        x = 0 if esq else caixa_x + caixa_w
        rx, ancora = (caixa_x + 3.0, "start") if esq else (caixa_x + caixa_w - 3.0, "end")
        return [
            f'  <rect id="connector{i}pin" connectorName="{nome}" x="{x:.1f}"'
            f' y="{y - 0.35:.2f}" width="{pino}" height="0.7" fill="#787878" stroke="none"/>',
            f'  <text x="{rx:.1f}" y="{y + tam_rotulo * 0.35:.2f}" font-family="Noto Sans"'
            f' font-size="{tam_rotulo}" fill="#000000" text-anchor="{ancora}">{nome}</text>',
        ]

    for ordem, (i, nome) in enumerate(esquerda):
        corpo += horizontal(i, nome, caixa_y + passo * (ordem + 1), True)
    for ordem, (i, nome) in enumerate(direita):
        corpo += horizontal(i, nome, caixa_y + passo * (ordem + 1), False)

    # VCC e GND com o rotulo fora da caixa, ao lado do proprio pino: dentro
    # eles disputam espaco com o titulo e o desenho fica apertado.
    if topo:
        i, nome = topo
        corpo += [
            f'  <rect id="connector{i}pin" connectorName="{nome}" x="35.65" y="0"'
            f' width="0.7" height="{pino}" fill="#787878" stroke="none"/>',
            f'  <text x="38.0" y="9.6" font-family="Noto Sans" font-size="4"'
            f' fill="#000000" text-anchor="start">{nome}</text>',
        ]
    if baixo:
        i, nome = baixo
        y = caixa_y + caixa_h
        corpo += [
            f'  <rect id="connector{i}pin" connectorName="{nome}" x="35.65" y="{y:.1f}"'
            f' width="0.7" height="{pino}" fill="#787878" stroke="none"/>',
            f'  <text x="38.0" y="{y + 7.8:.1f}" font-family="Noto Sans" font-size="4"'
            f' fill="#000000" text-anchor="start">{nome}</text>',
        ]

    # O titulo vai para o maior vao livre da caixa. Fixo no topo, ele encosta no
    # rotulo do primeiro pino quando a peca tem poucos pinos — e sobra a metade
    # de baixo da caixa vazia.
    tam = min(4.8, (caixa_w - 8) / (len(cfg["rotulo"]) * 0.62))
    ultimo = caixa_y + passo * linhas
    folga = caixa_y + caixa_h - ultimo
    if folga >= 12:
        ty = ultimo + folga / 2 + tam * 0.36
    elif topo is None:
        # Caixa cheia de pino, como placa de desenvolvimento: dentro nao ha vao
        # nenhum e o titulo cai em cima do rotulo do primeiro pino. Sobe para
        # fora, onde so ficaria o pino de alimentacao — que aqui nao existe.
        ty = caixa_y - 3.5
    else:
        ty = caixa_y + 10.0
    corpo += [
        "",
        f'  <text x="{caixa_x + caixa_w / 2:.1f}" y="{ty:.1f}"'
        f' font-family="Noto Sans" font-size="{tam:.2f}" fill="#000000"'
        f' text-anchor="middle">{cfg["rotulo"]}</text>',
    ]

    cabeca = ('<!-- 72 unidades por polegada. Pino de 14,4 u (0,2") e terminais em\n'
              '     multiplo de 7,2 u, que e a grade de 0,1" do esquema do Fritzing. -->')
    return svg(cabeca, larg, alt, "schematic", corpo)


def pcb(cfg):
    larg, alt = cfg["larg"] * MIL, cfg["alt"] * MIL
    pos = [(x * MIL, y * MIL) for x, y in cfg["furos"]]

    furos = [f'   <circle id="connector{i}pin" cx="{cx:.1f}" cy="{cy:.1f}" r="27.5"'
             f' fill="none" stroke="rgb(255, 191, 0)" stroke-width="20"/>'
             for i, (cx, cy) in enumerate(pos)]

    marca = {"baixo": (0, -75), "cima": (0, 75),
             "esquerda": (75, 0), "direita": (-75, 0)}[cfg["fileiras"][0]["lado"]]
    tam = min(70.0, (larg - 120) / (len(cfg["rotulo"]) * 0.62))

    corpo = ['  <g id="copper1">', '   <g id="copper0">'] + furos + ["   </g>", "  </g>",
             '  <g id="silkscreen">',
             f'   <rect x="5" y="5" width="{larg - 10:.1f}" height="{alt - 10:.1f}"'
             f' fill="none" stroke="#f0f0f0" stroke-width="10"/>',
             f'   <circle cx="{pos[0][0] + marca[0]:.1f}" cy="{pos[0][1] + marca[1]:.1f}"'
             f' r="14" fill="none" stroke="#f0f0f0" stroke-width="10"/>',
             f'   <text x="{larg / 2:.1f}" y="{alt / 2:.1f}"'
             f' font-family="OCR-Fritzing-mono" font-size="{tam:.0f}" fill="#f0f0f0"'
             f' text-anchor="middle">{cfg["rotulo"]}</text>',
             "  </g>"]

    cabeca = ('<!-- 1000 unidades por polegada, que e a escala das pecas THT do core.\n'
              '     Furo de 35 mil e anel de 75 mil: r 27,5 com traco de 20. -->')
    return svg(cabeca, larg, alt, None, corpo, mil=True)


def icon(cfg):
    quadro = 23.04
    proporcao = cfg["larg"] / cfg["alt"]
    larg_placa = quadro - 2 if proporcao >= 1 else (quadro - 2) * proporcao
    alt_placa = min((quadro - 2) / proporcao if proporcao >= 1 else quadro - 2,
                    quadro - 2)
    x0, y0 = (quadro - larg_placa) / 2, (quadro - alt_placa) / 2

    corpo = [f'  <rect x="{x0:.2f}" y="{y0:.2f}" width="{larg_placa:.2f}"'
             f' height="{alt_placa:.2f}" rx="1.4" fill="{cfg["placa"]}"/>']

    ocupado = []
    for fileira in cfg["fileiras"]:
        lado, n = fileira["lado"], len(fileira["nomes"])
        vertical = lado in ("esquerda", "direita")
        corrida = alt_placa if vertical else larg_placa
        r_pad = min(1.5, (larg_placa if vertical else alt_placa) / 6)
        fixo = {"baixo": y0 + alt_placa - r_pad - 1.0,
                "cima": y0 + r_pad + 1.0,
                "esquerda": x0 + r_pad + 1.0,
                "direita": x0 + larg_placa - r_pad - 1.0}[lado]
        ocupado.append((lado, fixo, r_pad))

        # Furo demais vira mancha ilegivel num icone de 32 px: vira barra.
        if n > 8:
            comp, esp = corrida - 3, r_pad * 1.5
            if vertical:
                corpo.append(f'  <rect x="{fixo - esp / 2:.2f}" y="{y0 + 1.5:.2f}"'
                             f' width="{esp:.2f}" height="{comp:.2f}" rx="{esp / 2:.2f}"'
                             f' fill="{METAL}"/>')
            else:
                corpo.append(f'  <rect x="{x0 + 1.5:.2f}" y="{fixo - esp / 2:.2f}"'
                             f' width="{comp:.2f}" height="{esp:.2f}" rx="{esp / 2:.2f}"'
                             f' fill="{METAL}"/>')
            continue

        passo = min(4.8, (corrida - 3) / max(n - 1, 1))
        inicio = (y0 if vertical else x0) + (corrida - passo * (n - 1)) / 2
        for i in range(n):
            p = inicio + i * passo
            cx, cy = (fixo, p) if vertical else (p, fixo)
            corpo.append(f'  <circle cx="{cx:.2f}" cy="{cy:.2f}" r="{r_pad:.2f}"'
                         f' fill="{METAL}"/>'
                         f'<circle cx="{cx:.2f}" cy="{cy:.2f}" r="{r_pad * 0.47:.2f}"'
                         f' fill="{FURO}"/>')

    # Placa achatada deixa pouco espaco livre, e texto de tamanho fixo vaza para
    # fora do icone. O tamanho sai do que sobrou, nos dois eixos.
    texto = cfg["icone"]
    horizontais = [(f, r) for lado, f, r in ocupado if lado in ("baixo", "cima")]
    verticais = [(f, r) for lado, f, r in ocupado if lado in ("esquerda", "direita")]
    cima = max([f + r for lado, f, r in ocupado if lado == "cima"], default=y0)
    baixo = min([f - r for lado, f, r in ocupado if lado == "baixo"],
                default=y0 + alt_placa)
    esq = max([f + r for lado, f, r in ocupado if lado == "esquerda"], default=x0)
    dir_ = min([f - r for lado, f, r in ocupado if lado == "direita"],
               default=x0 + larg_placa)
    vao_larg, vao_alt = dir_ - esq - 1.6, baixo - cima - 1.6
    tam = max(2.0, min(6.0, vao_larg / (len(texto) * 0.62), vao_alt))
    corpo.append(f'  <text x="{(esq + dir_) / 2:.2f}"'
                 f' y="{(cima + baixo) / 2 + tam * 0.36:.2f}"'
                 f' font-family="Noto Sans" font-size="{tam:.2f}" fill="{cfg["tinta"]}"'
                 f' text-anchor="middle">{texto}</text>')

    return svg("<!-- Icone do bin. Sem conector: icone nao tem. -->",
               quadro, quadro, "icon", corpo)


def svg(cabeca, larg, alt, camada, corpo, mil=False):
    div = 1000.0 if mil else 72.0
    dentro = "\n".join(corpo)
    if camada:
        dentro = f' <g id="{camada}">\n{dentro}\n </g>'
    return (f'<?xml version="1.0" encoding="UTF-8"?>\n{cabeca}\n'
            f'<svg xmlns="http://www.w3.org/2000/svg" version="1.1"\n'
            f'     width="{larg / div:.5f}in" height="{alt / div:.5f}in"'
            f' viewBox="0 0 {larg:.3f} {alt:.3f}">\n{dentro}\n</svg>\n')


# ----------------------------------------------------------------------- fzp

def fzp(cfg):
    nomes = cfg["pinos"] + (["ANT"] if cfg["ant"] else [])
    conectores = []
    for i, nome in enumerate(nomes):
        conectores.append(f"""  <connector type="male" name="{nome}" id="connector{i}">
   <description>{nome}</description>
   <views>
    <breadboardView><p svgId="connector{i}pin" layer="breadboard"/></breadboardView>
    <schematicView><p svgId="connector{i}pin" layer="schematic"/></schematicView>
    <pcbView><p svgId="connector{i}pin" layer="copper0"/><p svgId="connector{i}pin" layer="copper1"/></pcbView>
   </views>
  </connector>""")

    barras = []
    for nome, indices in cfg["barramentos"].items():
        membros = "\n".join(f'   <nodeMember connectorId="connector{i}"/>' for i in indices)
        barras.append(f'  <bus id="{nome.lower()}">\n{membros}\n  </bus>')
    buses = f"<buses>\n{chr(10).join(barras)}\n </buses>" if barras else "<buses/>"

    tags = "\n".join(f"  <tag>{t}</tag>" for t in cfg["tags"])
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<module moduleId="{cfg["module_id"]}" fritzingVersion="1.0.4">
 <version>1</version>
 <date>{cfg["data"]}</date>
 <author>hw-laboratorio</author>
 <title>{cfg["titulo"]}</title>
 <label>M</label>
 <description>{cfg["descricao"]}</description>
 <url>https://github.com/henriquemattosesilva/hw-laboratorio</url>
 <tags>
{tags}
 </tags>
 <properties>
  <property name="family">{cfg["familia"]}</property>
  <property name="variant">{cfg["id"]}</property>
  <property name="size">{cfg["larg"]:g} x {cfg["alt"]:g} mm</property>
 </properties>
 <views>
  <breadboardView>
   <layers image="breadboard/{cfg["slug"]}_breadboard.svg">
    <layer layerId="breadboard"/>
   </layers>
  </breadboardView>
  <schematicView>
   <layers image="schematic/{cfg["slug"]}_schematic.svg">
    <layer layerId="schematic"/>
   </layers>
  </schematicView>
  <pcbView>
   <layers image="pcb/{cfg["slug"]}_pcb.svg">
    <layer layerId="copper1"/>
    <layer layerId="copper0"/>
    <layer layerId="silkscreen"/>
   </layers>
  </pcbView>
  <iconView>
   <layers image="icon/{cfg["slug"]}_icon.svg">
    <layer layerId="icon"/>
   </layers>
  </iconView>
 </views>
 <connectors>
{chr(10).join(conectores)}
 </connectors>
 {buses}
</module>
"""


# --------------------------------------------------------------------- criar

def criar(ident, larg, alt, pinos, destino, titulo=None, familia=None,
          ant=False, lado="baixo", cor="verde", alinhar="inicio", vao=None,
          fileiras=None, data="2026-09-06"):
    """Escreve a peca em `destino`/<ident>. Devolve a pasta criada.

    `pinos` e uma fileira so, na borda `lado`. Para placa de duas fileiras,
    passar `fileiras` como [(lado, [nomes]), ...] e o `vao` entre elas.
    """
    if fileiras is None:
        fileiras = [(lado, pinos)]
    fileiras = [(ld, [p.strip().upper() for p in nomes if p.strip()])
                for ld, nomes in fileiras]

    if not any(nomes for _, nomes in fileiras):
        raise ValueError("a peca precisa de pelo menos um pino")
    for ld, _ in fileiras:
        if ld not in LADOS:
            raise ValueError(f"lado precisa ser um de {', '.join(LADOS)}")
    if len({ld for ld, _ in fileiras}) != len(fileiras):
        raise ValueError("duas fileiras na mesma borda")
    if cor not in CORES:
        raise ValueError(f"cor precisa ser uma de {', '.join(CORES)}")
    if alinhar not in ALINHAMENTOS:
        raise ValueError(f"alinhar precisa ser um de {', '.join(ALINHAMENTOS)}")
    if vao is not None and abs(vao / PASSO_MM - round(vao / PASSO_MM)) > 0.02:
        raise ValueError(
            f"o vao de {vao:g} mm nao e multiplo de 0,1 polegada (2,54 mm): a peca "
            "nao encaixaria na protoboard")

    brutos = [nome for _, nomes in fileiras for nome in nomes]
    nomeados = nomear(brutos)

    for ld, nomes in fileiras:
        corrida = (len(nomes) - 1) * PASSO_MM
        extensao = larg if ld in ("baixo", "cima") else alt
        if corrida + 2 * MIN_BORDA_MM > extensao:
            raise ValueError(
                f"{len(nomes)} pinos ocupam {corrida:.1f} mm e nao cabem na "
                f"borda de {ld}, que tem {extensao:g} mm")

    detalhadas, furos, base = [], [], 0
    for ld, nomes in fileiras:
        coords = posicoes(larg, alt, len(nomes), ld, alinhar, vao)
        indices = list(range(base, base + len(nomes)))
        detalhadas.append({"lado": ld, "nomes": nomeados[base:base + len(nomes)],
                           "indices": indices})
        furos += coords
        base += len(nomes)

    placa, borda, tinta = CORES[cor]
    slug = ident.replace("-", "_")
    rotulo = ident.upper()
    cfg = {
        "id": ident, "slug": slug, "larg": larg, "alt": alt,
        "pinos": nomeados, "ant": ant, "indice_ant": len(nomeados),
        "fileiras": detalhadas, "furos": furos,
        "placa": placa, "borda": borda, "tinta": tinta,
        "barramentos": barramentos(brutos, nomeados),
        "titulo": titulo or ident, "rotulo": rotulo,
        "icone": re.sub(r"[^A-Z0-9]", "", rotulo)[:4] or "?",
        "familia": familia or ident,
        "module_id": f"{ident}{pecas.SUFIXO}",
        "data": data,
        "tags": [ident] + [n.lower() for n in dict.fromkeys(brutos)][:4],
        "descricao": (f"{titulo or ident}. Placa de {larg:g} x {alt:g} mm, "
                      f"{len(nomeados)} pinos. Completar esta descricao com tensao, "
                      f"corrente e o que mais custar a lembrar na bancada."),
    }

    pasta = Path(destino) / ident
    if pasta.exists():
        raise ValueError(f"{pasta} ja existe")

    escreve(pasta / "part.fzp", fzp(cfg))
    for vista, conteudo in (("breadboard", breadboard(cfg)), ("schematic", schematic(cfg)),
                            ("pcb", pcb(cfg)), ("icon", icon(cfg))):
        escreve(pasta / "svg" / vista / f"{slug}_{vista}.svg", conteudo)
    return pasta


def escreve(caminho, texto):
    caminho.parent.mkdir(parents=True, exist_ok=True)
    caminho.write_bytes(texto.encode("utf-8"))


def main():
    ap = argparse.ArgumentParser(
        description="Cria uma peca Fritzing com a geometria ja certa.")
    ap.add_argument("id", help="identificador, tambem o nome da pasta (ex.: hc-sr04)")
    ap.add_argument("--mm", required=True, metavar="LxA",
                    help="cotas da placa em milimetros, ex.: 45x20")
    ap.add_argument("--pinos",
                    help="uma fileira so: nomes na ordem em que aparecem VISTA DE "
                         "CIMA, separados por virgula. Da esquerda para a direita "
                         "nas bordas de cima e de baixo, de cima para baixo nas "
                         "bordas curtas. Nome repetido vira barramento.")
    ap.add_argument("--fileira", action="append", metavar="LADO:NOMES",
                    help="uma fileira por vez, ex.: --fileira cima:D0,D1,D2. "
                         "Repetir para placa de duas fileiras.")
    ap.add_argument("--lado", default="baixo", choices=LADOS,
                    help="borda da fileira, quando se usa --pinos (padrao: baixo)")
    ap.add_argument("--vao", type=float, metavar="MM",
                    help="distancia entre as duas fileiras, de centro a centro. "
                         "Precisa ser multiplo de 2,54 mm, senao a peca nao encaixa.")
    ap.add_argument("--cor", default="verde", choices=sorted(CORES),
                    help="cor da placa (padrao: verde)")
    ap.add_argument("--alinhar", default="inicio", choices=ALINHAMENTOS,
                    help="onde a fileira encosta na borda (padrao: inicio). "
                         "Conector de poucos pinos na ponta costuma ser centro.")
    ap.add_argument("--titulo", help="titulo legivel, mostrado no Fritzing")
    ap.add_argument("--familia", help="family do Inspector; pecas da mesma familia "
                                      "viram variantes uma da outra")
    ap.add_argument("--ant", action="store_true",
                    help="acrescenta um conector ANT fora da fileira")
    args = ap.parse_args()

    if not re.fullmatch(r"[a-z0-9][a-z0-9.-]*", args.id):
        print("O id vai virar nome de pasta e moduleId: use minusculas, "
              "digitos, ponto e hifen.")
        return 1
    casado = re.fullmatch(r"\s*([\d.]+)\s*[xX]\s*([\d.]+)\s*", args.mm)
    if not casado:
        print(f"--mm esperava algo como 45x20, veio {args.mm!r}")
        return 1
    if not args.pinos and not args.fileira:
        print("Faltou --pinos ou --fileira.")
        return 1

    fileiras = None
    if args.fileira:
        fileiras = []
        for bruto in args.fileira:
            if ":" not in bruto:
                print(f"--fileira esperava LADO:NOMES, veio {bruto!r}")
                return 1
            ld, nomes = bruto.split(":", 1)
            fileiras.append((ld.strip(), nomes.split(",")))

    try:
        pasta = criar(args.id, float(casado[1]), float(casado[2]),
                      (args.pinos or "").split(","), pecas.PASTA,
                      titulo=args.titulo, familia=args.familia, ant=args.ant,
                      lado=args.lado, cor=args.cor, alinhar=args.alinhar,
                      vao=args.vao, fileiras=fileiras)
    except ValueError as erro:
        print(erro)
        return 1

    achados = validar.problemas(pasta)
    if achados:
        print("A peca saiu com problema, o que e defeito do gerador:")
        for achado in achados:
            print("  -", achado)
        return 1

    print(f"{pasta.relative_to(pecas.FRITZING.parent)} criada e validada.")
    print()
    print("Proximos passos:")
    print("  1. desenhar o ornamento no SVG de breadboard, onde o comentario indica")
    print("  2. completar a description e as properties do part.fzp")
    print("  3. python fritzing/ferramentas/previa.py   e olhar o desenho")
    print("  4. python fritzing/ferramentas/empacotar.py")
    print("  5. python fritzing/ferramentas/instalar.py  (com o Fritzing fechado)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
