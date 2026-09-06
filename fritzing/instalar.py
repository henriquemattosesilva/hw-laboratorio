"""Instala e atualiza as pecas na biblioteca do Fritzing, copiando os arquivos.

Importar o .fzpz so funciona na primeira vez. Na segunda o Fritzing recusa com
"Part module ID must be unique", porque a peca com aquele moduleId ja esta na
biblioteca — e ele nao oferece substituir. Atualizar e trocar os arquivos em
Documentos/Fritzing/parts, que e o que este script faz.

Manter o mesmo moduleId e proposital: mudar o id a cada correcao encheria a
biblioteca de copias e faria cada uma parecer uma peca diferente.

  python fritzing/instalar.py

Com o Fritzing aberto o script para antes de copiar: o programa le a biblioteca
ao iniciar e nao veria a troca, o que daria a impressao de que nao funcionou.
"""
import shutil
import subprocess
import sys
from pathlib import Path
from xml.etree import ElementTree

import validar

PASTA = Path(__file__).resolve().parent
PECAS = ["rf433-tx", "rf433-rx"]
BIBLIOTECA = Path.home() / "Documents" / "Fritzing" / "parts"


def fritzing_aberto():
    """True se o Fritzing estiver rodando. Fora do Windows, assume que nao."""
    if sys.platform != "win32":
        return False
    saida = subprocess.run(
        ["tasklist", "/FI", "IMAGENAME eq Fritzing.exe"],
        capture_output=True, text=True, check=False,
    ).stdout
    return "Fritzing.exe" in saida


def instalar(pasta, biblioteca):
    """Copia a peca de `pasta` para `biblioteca`. Devolve os caminhos escritos."""
    pasta = Path(pasta)
    achados = validar.problemas(pasta)
    if achados:
        raise ValueError(f"{pasta.name} tem problema: " + "; ".join(achados))

    biblioteca = Path(biblioteca)
    fzp = pasta / "part.fzp"
    module_id = ElementTree.parse(fzp).getroot().get("moduleId")

    escritos = []
    destino_fzp = biblioteca / "user" / f"{module_id}.fzp"
    destino_fzp.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(fzp, destino_fzp)
    escritos.append(destino_fzp)

    for arquivo in sorted((pasta / "svg").rglob("*.svg")):
        destino = biblioteca / "svg" / "user" / arquivo.parent.name / arquivo.name
        destino.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(arquivo, destino)
        escritos.append(destino)

    return escritos


def main():
    if fritzing_aberto():
        print("O Fritzing esta aberto. Feche-o e rode de novo: ele le a biblioteca")
        print("ao iniciar, e a troca so vale no proximo start.")
        return 1

    if not BIBLIOTECA.exists():
        print(f"Nao achei a biblioteca do Fritzing em {BIBLIOTECA}.")
        print("Abra o Fritzing uma vez para ele criar a pasta.")
        return 1

    for peca in PECAS:
        escritos = instalar(PASTA / peca, BIBLIOTECA)
        print(f"{peca}: {len(escritos)} arquivos em {escritos[0].parent.parent}")

    print()
    print("Abra o Fritzing. As pecas ja atualizadas aparecem em Minhas Pecas.")
    print("Sketch salvo antes disso guarda copia propria da peca e continua com o")
    print("desenho antigo: nele, apagar a peca e colocar de novo.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
