"""Confere se uma pasta de peca Fritzing vira peca que o Fritzing abre sem reclamar.

Confere so o que da para saber por leitura: arquivo citado que nao existe, conector
sem elemento no SVG, passo fora da grade de 0,1 polegada, fonte proibida, id repetido,
propriedade vazia, barramento apontando para conector que nao existe, e terminalId
declarado a mao.

As regras saem de fritzing-parts/scripts/checks/svg_checkers.py e explain_errors.md,
do proprio Fritzing. O desenho em si nao tem conferencia automatica: para isso existe
a folha de contato em previa.html.
"""
from pathlib import Path
from xml.etree import ElementTree

SVG = "{http://www.w3.org/2000/svg}"

# svg_checkers.py, VALID_FONTS. Noto Sans nas vistas de desenho, OCR na serigrafia.
FONTES = {"Noto Sans", "OCR-Fritzing-mono", "Droid Sans", "Droid Sans Mono", "OCRA"}

# 72 unidades por polegada no breadboard, entao o passo de 0,1" e 7,2.
PASSO = 7.2
FOLGA = 0.05

VISTAS = {
    "breadboardView": "breadboard",
    "schematicView": "schematic",
    "pcbView": "pcb",
    "iconView": "icon",
}


def problemas(pasta):
    """Lista de queixas, em portugues, sobre a peca em `pasta`. Vazia significa boa."""
    pasta = Path(pasta)
    fzp = pasta / "part.fzp"
    if not fzp.exists():
        return [f"{pasta.name}: nao tem part.fzp"]

    raiz = ElementTree.parse(fzp).getroot()
    achados = []
    achados += _conferir_propriedades(raiz)

    ids_declarados = {c.get("id") for c in raiz.iter("connector")}
    achados += _conferir_barramentos(raiz, ids_declarados)
    achados += _conferir_terminais(raiz)

    for tag, vista in VISTAS.items():
        no = raiz.find(f"views/{tag}/layers")
        if no is None:
            achados.append(f"{vista}: o FZP nao declara a vista")
            continue
        arquivo = pasta / "svg" / no.get("image")
        if not arquivo.exists():
            achados.append(f"{vista}: o FZP cita {no.get('image')}, que nao existe")
            continue
        achados += _conferir_svg(arquivo, vista)
        achados += _conferir_conectores(raiz, arquivo, tag, vista)

    return achados


def _conferir_propriedades(raiz):
    achados = []
    for prop in raiz.iter("property"):
        if not (prop.text or "").strip():
            achados.append(f"propriedade '{prop.get('name')}' esta vazia")
    return achados


def _conferir_barramentos(raiz, ids_declarados):
    achados = []
    for membro in raiz.iter("nodeMember"):
        alvo = membro.get("connectorId")
        if alvo not in ids_declarados:
            achados.append(f"barramento aponta para {alvo}, que nao e conector da peca")
    return achados


def _conferir_terminais(raiz):
    achados = []
    for p in raiz.iter("p"):
        if p.get("terminalId"):
            achados.append(
                f"{p.get('svgId')} declara terminalId; a 1.0.3 calcula o terminal "
                "sozinho e declarar a mao produz terminal invisivel"
            )
    return achados


def _conferir_svg(arquivo, vista):
    achados = []
    raiz = ElementTree.parse(arquivo).getroot()

    if not raiz.get("viewBox"):
        achados.append(f"{vista}: o SVG nao tem viewBox; o Fritzing adivinharia o DPI")
    for atributo in ("width", "height"):
        valor = raiz.get(atributo) or ""
        if not (valor.endswith("in") or valor.endswith("mm")):
            achados.append(
                f"{vista}: {atributo}='{valor}' nao esta em polegada nem milimetro"
            )

    vistos = set()
    for elemento in raiz.iter():
        ident = elemento.get("id")
        if not ident:
            continue
        if ident in vistos:
            achados.append(f"{vista}: id duplicado '{ident}'")
        vistos.add(ident)

    for elemento in raiz.iter():
        if elemento.tag not in (f"{SVG}text", f"{SVG}tspan"):
            continue
        familia = (elemento.get("font-family") or "").strip("\"'")
        if familia and familia not in FONTES:
            achados.append(f"{vista}: fonte '{familia}' nao esta na lista do Fritzing")

    return achados


def _conferir_conectores(raiz_fzp, arquivo, tag, vista):
    achados = []
    raiz_svg = ElementTree.parse(arquivo).getroot()
    por_id = {e.get("id"): e for e in raiz_svg.iter() if e.get("id")}

    centros = []
    for conector in raiz_fzp.iter("connector"):
        vista_no = conector.find(f"views/{tag}")
        for p in [] if vista_no is None else list(vista_no):
            alvo = p.get("svgId")
            elemento = por_id.get(alvo)
            if elemento is None:
                achados.append(f"{vista}: o FZP cita {alvo}, que nao existe no SVG")
                continue
            if _invisivel(elemento):
                achados.append(f"{vista}: {alvo} nao desenha nada; conector invisivel")
            if vista == "breadboard":
                centro = _centro(elemento)
                if centro is not None:
                    centros.append(centro)

    achados += _conferir_passo(centros, vista)
    return achados


def _invisivel(elemento):
    preenchimento = elemento.get("fill", "")
    traco = elemento.get("stroke", "")
    if preenchimento not in ("", "none"):
        return False
    if traco not in ("", "none") and float(elemento.get("stroke-width", 0) or 0) > 0:
        return False
    return True


def _centro(elemento):
    """Posicao do conector. Circulo tem cx/cy, retangulo tem x/y — o canto
    serve igual, porque a conferencia olha a distancia entre conectores."""
    x, y = _numero(elemento, "cx", "x"), _numero(elemento, "cy", "y")
    return None if x is None or y is None else (x, y)


def _numero(elemento, *atributos):
    for atributo in atributos:
        valor = elemento.get(atributo)
        if valor is not None:
            try:
                return float(valor)
            except ValueError:
                return None
    return None


def _conferir_passo(centros, vista):
    """Os conectores de cada fileira ficam num passo constante de 0,1 polegada.

    A conferencia agrupa por fileira antes de medir. Medindo a distancia entre
    conectores quaisquer, uma placa de duas fileiras teria todos os vizinhos
    longe demais — e o passo deixaria de ser conferido sem ninguem notar.

    Conector solto, como o furo de antena, fica sozinho no seu grupo e sai de
    fora, que e o comportamento certo: ele nao pertence a fileira nenhuma.
    """
    achados = []
    for eixo, fixo in ((0, 1), (1, 0)):
        grupos = {}
        for centro in centros:
            grupos.setdefault(round(centro[fixo], 1), []).append(centro[eixo])
        for _, valores in sorted(grupos.items()):
            if len(valores) < 2:
                continue
            valores.sort()
            for anterior, seguinte in zip(valores, valores[1:]):
                distancia = seguinte - anterior
                if distancia > PASSO * 1.5:
                    continue  # conector fora da fileira
                if abs(distancia - PASSO) > FOLGA:
                    achados.append(
                        f"{vista}: passo de {distancia:.2f} u entre pinos, "
                        f"esperado {PASSO}"
                    )
    return sorted(set(achados))
