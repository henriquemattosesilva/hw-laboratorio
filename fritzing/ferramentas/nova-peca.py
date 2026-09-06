"""Cria uma peca Fritzing nova, com a geometria ja certa.

  python fritzing/ferramentas/nova-peca.py hc-sr04 --mm 45x20 \
         --pinos VCC,TRIG,ECHO,GND --titulo "Sensor ultrassonico HC-SR04"

Sai uma peca completa e valida: as quatro vistas, os furos no passo de 0,1
polegada, o viewBox na unidade certa de cada vista e o FZP com os conectores.
Falta so o ornamento — o desenho dos componentes da placa, que nenhum gerador
tem como adivinhar. Cada SVG diz onde ele entra.

O que o gerador resolve e justamente a parte que da errado em silencio: unidade
do viewBox, passo dos furos, ordem dos conectores e o barramento de pinos
repetidos. Ornamento errado se ve na previa; passo errado so aparece quando a
peca nao encaixa.

**Pino repetido vira barramento.** `--pinos VCC,DATA,DATA,GND` cria DATA e
DATA2 e os declara ligados, porque nome repetido quer dizer o mesmo ponto na
placa. Sem isso o Fritzing acusaria conexao faltando ao usar so um deles.
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
BORDA_MM = 2.2   # do centro do furo ate a borda da placa
MARGEM_MM = 3.2  # da borda esquerda ate o primeiro furo

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

ALIMENTACAO = {"VCC", "VDD", "V+", "5V", "3V3", "3.3V", "VIN", "VBAT"}
TERRA = {"GND", "GROUND", "VSS", "0V", "-"}
DIREITA = {"ANT", "ANTENNA", "RF"}


def posicoes(larg, alt, n, lado, alinhar="inicio"):
    """Centro de cada furo em milimetros, na ordem em que os pinos foram dados.

    Fileira em cima ou embaixo corre da esquerda para a direita; nas bordas
    curtas corre de cima para baixo. E a ordem em que se le a serigrafia.

    `alinhar` decide onde a fileira encosta na borda. Header longo em borda
    longa costuma ficar encostado no comeco, que e o padrao; conector de dois
    pinos na ponta da placa costuma ficar centrado.
    """
    corrida = (n - 1) * PASSO_MM
    if lado in ("baixo", "cima"):
        livre, fixo = larg, (alt - BORDA_MM if lado == "baixo" else BORDA_MM)
    else:
        livre, fixo = alt, (BORDA_MM if lado == "esquerda" else larg - BORDA_MM)

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

def breadboard(cfg):
    larg, alt = cfg["larg"] * MM, cfg["alt"] * MM
    r_pad, r_furo, tam_rotulo = 2.4, 1.15, 2.4
    lado, tinta = cfg["lado"], cfg["tinta"]
    furos = [(x * MM, y * MM) for x, y in cfg["furos"]]

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

    # O rotulo do pino sai para o lado de dentro da placa, seja qual for a
    # borda em que a fileira esta.
    desloca = {"baixo": (0, -4.6, "middle"), "cima": (0, 6.6, "middle"),
               "esquerda": (r_pad + 1.2, 1.0, "start"),
               "direita": (-r_pad - 1.2, 1.0, "end")}[lado]

    for i, (nome, (cx, cy)) in enumerate(zip(cfg["pinos"], furos)):
        dx, dy, ancora = desloca
        corpo += [
            f'  <text x="{cx + dx:.3f}" y="{cy + dy:.3f}" font-family="Noto Sans"'
            f' font-size="{tam_rotulo}" fill="{tinta}"'
            f' text-anchor="{ancora}">{nome}</text>',
            f'  <circle id="connector{i}pin" cx="{cx:.3f}" cy="{cy:.3f}" r="{r_pad}"'
            f' fill="{METAL}" stroke="none"/>',
            f'  <circle cx="{cx:.3f}" cy="{cy:.3f}" r="{r_furo}" fill="{FURO}"/>',
        ]

    if cfg["ant"]:
        i, cx, cy_ant = len(cfg["pinos"]), larg - 4.0 * MM, 4.0 * MM
        corpo += [
            f'  <circle id="connector{i}pin" cx="{cx:.3f}" cy="{cy_ant:.3f}" r="{r_pad}"'
            f' fill="{METAL}" stroke="none"/>',
            f'  <circle cx="{cx:.3f}" cy="{cy_ant:.3f}" r="{r_furo}" fill="{FURO}"/>',
            f'  <text x="{cx:.3f}" y="{cy_ant + 7.2:.3f}" font-family="Noto Sans"'
            f' font-size="2.8" fill="{tinta}" text-anchor="middle">ANT</text>',
        ]

    corpo += rotulo_da_placa(cfg, larg, alt, furos, r_pad, tam_rotulo)

    cabeca = (f'<!-- {cfg["titulo"]}, vista de cima. Placa de {cfg["larg"]:g} x '
              f'{cfg["alt"]:g} mm, conectores na borda de {lado}.\n'
              f'     72 unidades por polegada: 1 mm = 2,834646 u e o passo de 0,1" = 7,2 u.\n'
              f'     Furo de encaixe, sem pino saindo: e assim que o fio entra. -->')
    return svg(cabeca, larg, alt, "breadboard", corpo)


def rotulo_da_placa(cfg, larg, alt, furos, r_pad, tam_rotulo):
    """Poe o nome da peca no espaco que a fileira de furos deixou livre.

    A folga se mede da borda do furo e do fim do rotulo do pino, nao do centro
    do furo: medindo do centro, o nome encosta nos furos em placa estreita.
    """
    nome = cfg["rotulo"]
    largo_rotulos = max(len(p) for p in cfg["pinos"]) * 0.62 * tam_rotulo
    xs = [x for x, _ in furos]

    if cfg["lado"] in ("baixo", "cima"):
        x0, x1 = max(xs) + r_pad + 2.5, larg - 2.0
        cy = furos[0][1] + 1.0
    elif cfg["lado"] == "esquerda":
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
    """Reparte os conectores entre os quatro lados da caixa do esquema."""
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
        direita.append((len(cfg["pinos"]), "ANT"))
    return topo, baixo, esquerda, direita


def schematic(cfg):
    passo, pino = 14.4, 14.4
    topo, baixo, esquerda, direita = _fatia_schematic(cfg)
    linhas = max(len(esquerda), len(direita))
    caixa_h = max(43.2, passo * (linhas + 1))
    caixa_x, caixa_y, caixa_w = 14.4, 14.4, 50.4
    larg, alt = caixa_x + caixa_w + pino, caixa_y + caixa_h + pino

    corpo = [
        f'  <rect x="{caixa_x}" y="{caixa_y}" width="{caixa_w}" height="{caixa_h:.1f}"',
        '        fill="none" stroke="#000000" stroke-width="0.9"',
        '        stroke-linecap="round" stroke-linejoin="round"/>',
        "",
    ]

    def horizontal(i, nome, y, esq):
        x = 0 if esq else caixa_x + caixa_w
        rx, ancora = (caixa_x + 3.0, "start") if esq else (caixa_x + caixa_w - 3.0, "end")
        return [
            f'  <rect id="connector{i}pin" connectorName="{nome}" x="{x:.1f}"'
            f' y="{y - 0.35:.2f}" width="{pino}" height="0.7" fill="#787878" stroke="none"/>',
            f'  <text x="{rx:.1f}" y="{y + 1.4:.2f}" font-family="Noto Sans" font-size="4"'
            f' fill="#000000" text-anchor="{ancora}">{nome}</text>',
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
    ty = (ultimo + folga / 2 + tam * 0.36) if folga >= 12 else caixa_y + 10.0
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
    if cfg["ant"]:
        furos.append(f'   <circle id="connector{len(cfg["pinos"])}pin"'
                     f' cx="{larg - 4.0 * MIL:.1f}" cy="{4.0 * MIL:.1f}" r="27.5"'
                     f' fill="none" stroke="rgb(255, 191, 0)" stroke-width="20"/>')

    # Marca do pino 1, deslocada para dentro da placa.
    marca = {"baixo": (0, -75), "cima": (0, 75),
             "esquerda": (75, 0), "direita": (-75, 0)}[cfg["lado"]]
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

    n = len(cfg["pinos"])
    vertical = cfg["lado"] in ("esquerda", "direita")
    corrida = alt_placa if vertical else larg_placa
    r_pad = min(1.5, (larg_placa if vertical else alt_placa) / 6)
    passo = min(4.8, (corrida - 3) / max(n - 1, 1))
    inicio = (y0 if vertical else x0) + (corrida - passo * (n - 1)) / 2
    fixo = {"baixo": y0 + alt_placa - r_pad - 1.0,
            "cima": y0 + r_pad + 1.0,
            "esquerda": x0 + r_pad + 1.0,
            "direita": x0 + larg_placa - r_pad - 1.0}[cfg["lado"]]

    corpo = [f'  <rect x="{x0:.2f}" y="{y0:.2f}" width="{larg_placa:.2f}"'
             f' height="{alt_placa:.2f}" rx="1.4" fill="{cfg["placa"]}"/>']
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
    if vertical:
        borda = fixo + r_pad if cfg["lado"] == "esquerda" else fixo - r_pad
        tx0, tx1 = ((borda + 0.6, x0 + larg_placa - 0.6) if cfg["lado"] == "esquerda"
                    else (x0 + 0.6, borda - 0.6))
        vao_larg, vao_alt = tx1 - tx0, alt_placa - 2.0
        cx_texto, cy_centro = (tx0 + tx1) / 2, y0 + alt_placa / 2
    else:
        topo = fixo - r_pad if cfg["lado"] == "baixo" else fixo + r_pad
        vao_larg = larg_placa - 2.0
        vao_alt = (topo - y0 - 1.0) if cfg["lado"] == "baixo" else (y0 + alt_placa - topo - 1.0)
        cx_texto = quadro / 2
        cy_centro = (y0 + topo) / 2 if cfg["lado"] == "baixo" else (topo + y0 + alt_placa) / 2

    tam = max(2.0, min(6.0, vao_larg / (len(texto) * 0.62), vao_alt))
    corpo.append(f'  <text x="{cx_texto:.2f}" y="{cy_centro + tam * 0.36:.2f}"'
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
          ant=False, lado="baixo", cor="verde", alinhar="inicio",
          data="2026-09-06"):
    """Escreve a peca em `destino`/<ident>. Devolve a pasta criada."""
    brutos = [p.strip().upper() for p in pinos if p.strip()]
    if not brutos:
        raise ValueError("a peca precisa de pelo menos um pino")
    if lado not in LADOS:
        raise ValueError(f"lado precisa ser um de {', '.join(LADOS)}")
    if cor not in CORES:
        raise ValueError(f"cor precisa ser uma de {', '.join(CORES)}")
    if alinhar not in ALINHAMENTOS:
        raise ValueError(f"alinhar precisa ser um de {', '.join(ALINHAMENTOS)}")
    nomeados = nomear(brutos)

    passo_total = (len(nomeados) - 1) * PASSO_MM
    extensao = larg if lado in ("baixo", "cima") else alt
    if passo_total + 2 * BORDA_MM > extensao:
        raise ValueError(
            f"{len(nomeados)} pinos ocupam {passo_total:.1f} mm e nao cabem na "
            f"borda de {lado}, que tem {extensao:g} mm")

    placa, borda, tinta = CORES[cor]
    slug = ident.replace("-", "_")
    rotulo = ident.upper()
    cfg = {
        "id": ident, "slug": slug, "larg": larg, "alt": alt,
        "pinos": nomeados, "ant": ant, "lado": lado,
        "furos": posicoes(larg, alt, len(nomeados), lado, alinhar),
        "placa": placa, "borda": borda, "tinta": tinta,
        "barramentos": barramentos(brutos, nomeados),
        "titulo": titulo or ident, "rotulo": rotulo,
        "icone": re.sub(r"[^A-Z0-9]", "", rotulo)[:4] or "?",
        "familia": familia or ident,
        "module_id": f"{ident}{pecas.SUFIXO}",
        "data": data,
        "tags": [ident] + [n.lower() for n in dict.fromkeys(brutos)][:4],
        "descricao": (f"{titulo or ident}. Placa de {larg:g} x {alt:g} mm, "
                      f"pinos {' '.join(nomeados)} da esquerda para a direita vista "
                      f"de cima. Completar esta descricao com tensao, corrente e o "
                      f"que mais custar a lembrar na bancada."),
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
    ap.add_argument("--pinos", required=True,
                    help="nomes na ordem em que aparecem VISTA DE CIMA, separados "
                         "por virgula: da esquerda para a direita nas bordas de "
                         "cima e de baixo, de cima para baixo nas bordas curtas. "
                         "Nome repetido vira barramento.")
    ap.add_argument("--lado", default="baixo", choices=LADOS,
                    help="borda onde fica a fileira de furos (padrao: baixo)")
    ap.add_argument("--cor", default="verde", choices=sorted(CORES),
                    help="cor da placa (padrao: verde)")
    ap.add_argument("--alinhar", default="inicio", choices=ALINHAMENTOS,
                    help="onde a fileira encosta na borda (padrao: inicio). "
                         "Conector de poucos pinos na ponta costuma ser centro.")
    ap.add_argument("--titulo", help="titulo legivel, mostrado no Fritzing")
    ap.add_argument("--familia", help="family do Inspector; pecas da mesma familia "
                                      "viram variantes uma da outra")
    ap.add_argument("--ant", action="store_true",
                    help="acrescenta um conector ANT fora da barra")
    args = ap.parse_args()

    if not re.fullmatch(r"[a-z0-9][a-z0-9.-]*", args.id):
        print("O id vai virar nome de pasta e moduleId: use minusculas, "
              "digitos, ponto e hifen.")
        return 1
    casado = re.fullmatch(r"\s*([\d.]+)\s*[xX]\s*([\d.]+)\s*", args.mm)
    if not casado:
        print(f"--mm esperava algo como 45x20, veio {args.mm!r}")
        return 1

    try:
        pasta = criar(args.id, float(casado[1]), float(casado[2]),
                      args.pinos.split(","), pecas.PASTA,
                      titulo=args.titulo, familia=args.familia, ant=args.ant,
                      lado=args.lado, cor=args.cor, alinhar=args.alinhar)
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
