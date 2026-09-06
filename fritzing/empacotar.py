"""Zipa uma pasta de peca no .fzpz que o Fritzing importa por Arquivo > Abrir.

O .fzpz e um zip plano: part.<moduleid>.fzp e svg.<vista>.<nome>.svg. O FZP la dentro
continua citando 'breadboard/nome.svg'; quem faz a traducao e o Fritzing na importacao,
entao aqui so o nome do arquivo muda.

  python fritzing/empacotar.py          empacota as duas pecas em fritzing/dist/
"""
import sys
import zipfile
from pathlib import Path
from xml.etree import ElementTree

import validar

PASTA = Path(__file__).resolve().parent

PECAS = {
    "rf433-tx": "RF433-TX-FS1000A.fzpz",
    "rf433-rx": "RF433-RX-MX05V.fzpz",
}


def empacotar(pasta, destino):
    """Zipa `pasta` em `destino`. Levanta ValueError se a peca tiver problema."""
    pasta = Path(pasta)
    achados = validar.problemas(pasta)
    if achados:
        raise ValueError(f"{pasta.name} tem problema: " + "; ".join(achados))

    fzp = pasta / "part.fzp"
    module_id = ElementTree.parse(fzp).getroot().get("moduleId")

    destino = Path(destino)
    destino.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(destino, "w", zipfile.ZIP_DEFLATED) as zip_:
        zip_.write(fzp, f"part.{module_id}.fzp")
        for arquivo in sorted((pasta / "svg").rglob("*.svg")):
            vista = arquivo.parent.name
            zip_.write(arquivo, f"svg.{vista}.{arquivo.name}")
    return destino


def main():
    for pasta, nome in PECAS.items():
        destino = empacotar(PASTA / pasta, PASTA / "dist" / nome)
        print(destino.relative_to(PASTA.parent))


if __name__ == "__main__":
    sys.exit(main())
