"""Gera a folha de contato das SVGs de todas as pecas.

Nenhum teste pega desenho torto, e o desenho e o produto. Esta pagina existe
para conferir a olho antes de dar a peca por pronta.

O tamanho de cada quadro sai do proprio SVG, do width e height em polegadas.
Escrever a pagina a mao significava recalcular esses pixels a cada peca nova e
a cada mudanca de cota — e errar em silencio, mostrando o desenho esticado.

  python fritzing/ferramentas/previa.py
  pwsh ferramentas/previa.ps1 -Arquivo fritzing/previa.html -Largura 1100 \
       -Altura 1400 -Destino previa-fritzing.png -Inteira
"""
import sys
from pathlib import Path
from xml.etree import ElementTree

import pecas

SAIDA = pecas.FRITZING / "previa.html"

# Placa no tamanho real fica do tamanho de uma unha na tela. O PCB e o esquema
# aguentam menos ampliacao porque ja sao desenhos grandes e vazios.
AMPLIACAO = {"breadboard": 4.0, "icon": 4.0, "schematic": 2.5, "pcb": 2.5}
ORDEM = ["breadboard", "schematic", "pcb", "icon"]
PPP = 96  # pixels por polegada do navegador

CABECA = """<!doctype html>
<html lang="pt-BR">
<meta charset="utf-8">
<title>Peças Fritzing — folha de contato</title>
<!-- GERADO por fritzing/ferramentas/previa.py. Não editar à mão. -->
<style>
  :root { color-scheme: light; }
  body {
    margin: 0; padding: 28px 32px 40px;
    background: #6f6f6f; color: #f2f2f2;
    font: 14px/1.5 "Segoe UI", system-ui, sans-serif;
  }
  h1 { font-size: 19px; font-weight: 600; margin: 0 0 4px; letter-spacing: .01em; }
  .sub { color: #d0d0d0; font-size: 13px; margin: 0 0 26px; }
  h2 {
    font-size: 15px; font-weight: 600; margin: 30px 0 12px;
    padding-bottom: 6px; border-bottom: 1px solid #8b8b8b;
  }
  h2 span { color: #cfcfcf; font-weight: 400; }
  .linha { display: flex; flex-wrap: wrap; gap: 16px; align-items: flex-start; }
  figure {
    margin: 0; background: #e8e8e8; border: 1px solid #cfcfcf;
    border-radius: 6px; padding: 12px; display: flex;
    flex-direction: column; align-items: center; gap: 10px;
  }
  /* Só o PCB fica no escuro: a serigrafia é branca e sumiria no claro. */
  figure.escuro { background: #4a4a4a; border-color: #6d6d6d; }
  figcaption {
    font-size: 11px; color: #3a3a3a; text-align: center;
    font-variant-numeric: tabular-nums;
  }
  figure.escuro figcaption { color: #efefef; }
  figcaption b { display: block; font-weight: 600; font-size: 12px; }
  img { display: block; }
</style>

<h1>Peças Fritzing — hw-laboratorio</h1>
<p class="sub">
  Fundo claro como a tela do Fritzing; só o PCB vai no escuro, porque a serigrafia é
  branca. As ampliações estão anotadas: no tamanho real cada placa tem alguns milímetros.
</p>
"""


def polegadas(valor):
    """Converte o width/height de um SVG para polegadas. Aceita in e mm."""
    valor = (valor or "").strip()
    if valor.endswith("mm"):
        return float(valor[:-2]) / 25.4
    if valor.endswith("in"):
        return float(valor[:-2])
    raise ValueError(f"tamanho sem unidade fisica: {valor!r}")


def quadro(svg, vista):
    raiz = ElementTree.parse(svg).getroot()
    larg, alt = polegadas(raiz.get("width")), polegadas(raiz.get("height"))
    escala = AMPLIACAO[vista]
    classe = ' class="escuro"' if vista == "pcb" else ""
    return (
        f'  <figure{classe}>\n'
        f'    <img src="pecas/{svg.parent.parent.parent.name}/svg/{vista}/{svg.name}"'
        f' width="{round(larg * PPP * escala)}" height="{round(alt * PPP * escala)}">\n'
        f'    <figcaption><b>{vista}</b>'
        f'{larg:.3f} × {alt:.3f} pol · {escala:g}×</figcaption>\n'
        f'  </figure>'
    )


def secao(peca):
    fzp = ElementTree.parse(peca / "part.fzp").getroot()
    titulo = fzp.findtext("title") or peca.name
    nomes = " · ".join(c.get("name") for c in fzp.iter("connector"))

    quadros = []
    for vista in ORDEM:
        achados = sorted((peca / "svg" / vista).glob("*.svg"))
        quadros += [quadro(svg, vista) for svg in achados]

    return (f'\n<h2>{titulo} <span>— {peca.name}, conectores {nomes}</span></h2>\n'
            f'<div class="linha">\n' + "\n".join(quadros) + "\n</div>\n")


def gerar(destino=SAIDA):
    encontradas = pecas.descobrir()
    if not encontradas:
        raise ValueError(f"nenhuma peca em {pecas.PASTA}")
    pagina = CABECA + "".join(secao(p) for p in encontradas) + "</html>\n"
    Path(destino).write_bytes(pagina.encode("utf-8"))
    return destino, len(encontradas)


def main():
    destino, quantas = gerar()
    print(f"{destino.relative_to(pecas.FRITZING.parent)}: {quantas} peças")
    return 0


if __name__ == "__main__":
    sys.exit(main())
