"""Zipa cada peca no .fzpz que o Fritzing importa por Arquivo > Abrir.

O pacote fica DENTRO da pasta da peca, ao lado do part.fzp. O part.fzp sozinho
nao importa: ele cita as SVGs por caminho relativo, e quem junta tudo e o zip.

O .fzpz e um zip plano: part.<moduleid>.fzp e svg.<vista>.<nome>.svg. O FZP la dentro
continua citando 'breadboard/nome.svg'; quem faz a traducao e o Fritzing na importacao,
entao aqui so o nome do arquivo muda.

  python fritzing/ferramentas/empacotar.py     reescreve o .fzpz de cada peca
"""
import sys
import zipfile
from pathlib import Path

import pecas
import validar


def empacotar(peca, destino):
    """Zipa `peca` em `destino`. Levanta ValueError se a peca tiver problema."""
    peca = Path(peca)
    achados = validar.problemas(peca)
    if achados:
        raise ValueError(f"{peca.name} tem problema: " + "; ".join(achados))

    destino = Path(destino)
    destino.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(destino, "w", zipfile.ZIP_DEFLATED) as zip_:
        zip_.write(peca / "part.fzp", f"part.{pecas.module_id(peca)}.fzp")
        for arquivo in sorted((peca / "svg").rglob("*.svg")):
            zip_.write(arquivo, f"svg.{arquivo.parent.name}.{arquivo.name}")
    return destino


def main():
    encontradas = pecas.descobrir()
    if not encontradas:
        print(f"Nenhuma peca em {pecas.PASTA}.")
        return 1
    for peca in encontradas:
        destino = empacotar(peca, pecas.pacote(peca))
        print(destino.relative_to(pecas.FRITZING.parent))
    return 0


if __name__ == "__main__":
    sys.exit(main())
