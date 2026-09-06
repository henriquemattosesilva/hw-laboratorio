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

VERDE, VERDE_BORDA = "#1f7a34", "#14562a"
METAL, FURO = "#c9c9c9", "#3a3a3a"

ALIMENTACAO = {"VCC", "VDD", "V+", "5V", "3V3", "3.3V", "VIN", "VBAT"}
TERRA = {"GND", "GROUND", "VSS", "0V", "-"}
DIREITA = {"ANT", "ANTENNA", "RF"}


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
    passo, r_pad, r_furo = PASSO_MM * MM, 2.4, 1.15
    cy = alt - BORDA_MM * MM
    largura_barra = (len(cfg["pinos"]) - 1) * passo
    margem = MARGEM_MM * MM
    x0 = margem if margem * 2 + largura_barra <= larg else (larg - largura_barra) / 2

    corpo = [
        f'  <rect x="0" y="0" width="{larg:.3f}" height="{alt:.3f}" rx="1.5" fill="{VERDE}"/>',
        f'  <rect x="0.4" y="0.4" width="{larg - 0.8:.3f}" height="{alt - 0.8:.3f}" rx="1.2"',
        f'        fill="none" stroke="{VERDE_BORDA}" stroke-width="0.8"/>',
        "",
        "  <!-- O ornamento entra aqui: os componentes da placa, sem id nenhum para",
        "       nao colidir com os conectores. Ver CONVENCOES.md. -->",
        "",
    ]
    for i, nome in enumerate(cfg["pinos"]):
        cx = x0 + i * passo
        corpo += [
            f'  <text x="{cx:.3f}" y="{cy - 4.6:.3f}" font-family="Noto Sans" font-size="2.4"'
            f' fill="#ffffff" text-anchor="middle">{nome}</text>',
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
            f' font-size="2.8" fill="#ffffff" text-anchor="middle">ANT</text>',
        ]

    # A folga se mede da borda do ultimo furo, nao do centro dele: medindo do
    # centro, o rotulo encosta no furo em placa estreita.
    livre = x0 + largura_barra + r_pad + 2.5
    sobra = larg - livre - 2.0
    rotulo = cfg["rotulo"]
    if sobra >= 14:
        tam = min(3.2, sobra / (len(rotulo) * 0.62))
        corpo.append(
            f'  <text x="{livre + sobra / 2:.3f}" y="{cy + 1.0:.3f}"'
            f' font-family="Noto Sans" font-size="{tam:.2f}" fill="#ffffff"'
            f' text-anchor="middle">{rotulo}</text>')
    else:
        corpo.append(
            f'  <text x="{larg / 2:.3f}" y="{cy - 9.0:.3f}" font-family="Noto Sans"'
            f' font-size="3.0" fill="#ffffff" text-anchor="middle">{rotulo}</text>')

    cabeca = (f'<!-- {cfg["titulo"]}, vista de cima. Placa de {cfg["larg"]:g} x '
              f'{cfg["alt"]:g} mm.\n'
              f'     72 unidades por polegada: 1 mm = 2,834646 u e o passo de 0,1" = 7,2 u.\n'
              f'     Furo de encaixe, sem pino saindo: e assim que o fio entra. -->')
    return svg(cabeca, larg, alt, "breadboard", corpo)


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

    corpo += [
        "",
        f'  <text x="{caixa_x + caixa_w / 2:.1f}" y="{caixa_y + 10.0:.1f}"'
        f' font-family="Noto Sans" font-size="4.8" fill="#000000"'
        f' text-anchor="middle">{cfg["rotulo"]}</text>',
    ]

    cabeca = ('<!-- 72 unidades por polegada. Pino de 14,4 u (0,2") e terminais em\n'
              '     multiplo de 7,2 u, que e a grade de 0,1" do esquema do Fritzing. -->')
    return svg(cabeca, larg, alt, "schematic", corpo)


def pcb(cfg):
    larg, alt = cfg["larg"] * MIL, cfg["alt"] * MIL
    passo, cy = PASSO_MM * MIL, alt - BORDA_MM * MIL
    largura_barra = (len(cfg["pinos"]) - 1) * passo
    margem = MARGEM_MM * MIL
    x0 = margem if margem * 2 + largura_barra <= larg else (larg - largura_barra) / 2

    furos = []
    for i in range(len(cfg["pinos"])):
        furos.append(f'   <circle id="connector{i}pin" cx="{x0 + i * passo:.1f}"'
                     f' cy="{cy:.1f}" r="27.5" fill="none" stroke="rgb(255, 191, 0)"'
                     f' stroke-width="20"/>')
    if cfg["ant"]:
        furos.append(f'   <circle id="connector{len(cfg["pinos"])}pin"'
                     f' cx="{larg - 4.0 * MIL:.1f}" cy="{4.0 * MIL:.1f}" r="27.5"'
                     f' fill="none" stroke="rgb(255, 191, 0)" stroke-width="20"/>')

    corpo = ['  <g id="copper1">', '   <g id="copper0">'] + furos + ["   </g>", "  </g>",
             '  <g id="silkscreen">',
             f'   <rect x="5" y="5" width="{larg - 10:.1f}" height="{alt - 10:.1f}"'
             f' fill="none" stroke="#f0f0f0" stroke-width="10"/>',
             f'   <circle cx="{x0:.1f}" cy="{cy - 75:.1f}" r="14" fill="none"'
             f' stroke="#f0f0f0" stroke-width="10"/>',
             f'   <text x="{larg / 2:.1f}" y="{alt / 2:.1f}"'
             f' font-family="OCR-Fritzing-mono" font-size="70" fill="#f0f0f0"'
             f' text-anchor="middle">{cfg["rotulo"]}</text>',
             "  </g>"]

    cabeca = ('<!-- 1000 unidades por polegada, que e a escala das pecas THT do core.\n'
              '     Furo de 35 mil e anel de 75 mil: r 27,5 com traco de 20. -->')
    return svg(cabeca, larg, alt, None, corpo, mil=True)


def icon(cfg):
    lado = 23.04
    proporcao = cfg["larg"] / cfg["alt"]
    larg_placa = lado - 2 if proporcao >= 1 else (lado - 2) * proporcao
    alt_placa = (lado - 2) / proporcao if proporcao >= 1 else lado - 2
    alt_placa = min(alt_placa, lado - 2)
    x0, y0 = (lado - larg_placa) / 2, (lado - alt_placa) / 2

    n = len(cfg["pinos"])
    passo = min(4.8, (larg_placa - 4) / max(n - 1, 1))
    inicio = x0 + (larg_placa - passo * (n - 1)) / 2
    r_pad = min(1.5, alt_placa / 6)
    cy = y0 + alt_placa - r_pad - 1.0

    corpo = [f'  <rect x="{x0:.2f}" y="{y0:.2f}" width="{larg_placa:.2f}"'
             f' height="{alt_placa:.2f}" rx="1.4" fill="{VERDE}"/>']
    for i in range(n):
        cx = inicio + i * passo
        corpo.append(f'  <circle cx="{cx:.2f}" cy="{cy:.2f}" r="{r_pad:.2f}"'
                     f' fill="{METAL}"/>'
                     f'<circle cx="{cx:.2f}" cy="{cy:.2f}" r="{r_pad * 0.47:.2f}"'
                     f' fill="{FURO}"/>')

    # Placa achatada deixa pouca altura acima dos furos, e texto de tamanho fixo
    # vaza para fora do icone. O tamanho sai do espaco que sobrou, nos dois eixos.
    texto = cfg["icone"]
    topo_furos = cy - r_pad
    espaco = topo_furos - y0 - 1.0
    tam = max(2.0, min(6.0, (larg_placa - 2) / (len(texto) * 0.62), espaco))
    corpo.append(f'  <text x="{lado / 2:.2f}"'
                 f' y="{(y0 + topo_furos) / 2 + tam * 0.36:.2f}"'
                 f' font-family="Noto Sans" font-size="{tam:.2f}" fill="#ffffff"'
                 f' text-anchor="middle">{texto}</text>')

    return svg("<!-- Icone do bin. Sem conector: icone nao tem. -->",
               lado, lado, "icon", corpo)


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
          ant=False, data="2026-09-06"):
    """Escreve a peca em `destino`/<ident>. Devolve a pasta criada."""
    brutos = [p.strip().upper() for p in pinos if p.strip()]
    if not brutos:
        raise ValueError("a peca precisa de pelo menos um pino")
    nomeados = nomear(brutos)

    passo_total = (len(nomeados) - 1) * PASSO_MM
    if passo_total + 2 * BORDA_MM > larg:
        raise ValueError(
            f"{len(nomeados)} pinos ocupam {passo_total:.1f} mm e nao cabem numa "
            f"placa de {larg:g} mm")

    slug = ident.replace("-", "_")
    rotulo = ident.upper()
    cfg = {
        "id": ident, "slug": slug, "larg": larg, "alt": alt,
        "pinos": nomeados, "ant": ant,
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
                    help="nomes da esquerda para a direita VISTA DE CIMA, "
                         "separados por virgula. Nome repetido vira barramento.")
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
                      titulo=args.titulo, familia=args.familia, ant=args.ant)
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
