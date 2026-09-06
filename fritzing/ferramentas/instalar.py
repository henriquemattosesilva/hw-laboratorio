"""Instala e atualiza as pecas na biblioteca do Fritzing, copiando os arquivos.

Importar o .fzpz mostra "Part module ID must be unique" quando a peca ja esta na
biblioteca. O erro engana: a essa altura o Fritzing ja copiou os arquivos novos
para o disco, e fechar e reabrir mostra a peca atualizada. Este script faz a
copia direto, sem a caixa de erro e sem depender desse efeito colateral.

Manter o mesmo moduleId e proposital: mudar o id a cada correcao encheria a
biblioteca de copias, cada uma parecendo uma peca diferente.

  python fritzing/ferramentas/instalar.py

Com o Fritzing aberto o script para antes de copiar: o programa le a biblioteca
ao iniciar e nao veria a troca, o que daria a impressao de que nao funcionou.
"""
import shutil
import subprocess
import sys
from pathlib import Path

import pecas
import validar

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


def instalar(peca, biblioteca):
    """Copia a peca para `biblioteca`. Devolve os caminhos escritos."""
    peca = Path(peca)
    achados = validar.problemas(peca)
    if achados:
        raise ValueError(f"{peca.name} tem problema: " + "; ".join(achados))

    biblioteca = Path(biblioteca)
    escritos = []

    destino_fzp = biblioteca / "user" / f"{pecas.module_id(peca)}.fzp"
    destino_fzp.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(peca / "part.fzp", destino_fzp)
    escritos.append(destino_fzp)

    for arquivo in sorted((peca / "svg").rglob("*.svg")):
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

    for peca in pecas.descobrir():
        escritos = instalar(peca, BIBLIOTECA)
        print(f"{peca.name}: {len(escritos)} arquivos")

    print()
    print(f"Instaladas em {BIBLIOTECA}. Abra o Fritzing: elas aparecem em Minhas Pecas.")
    print("Sketch salvo antes disso guarda copia propria da peca e continua com o")
    print("desenho antigo: nele, apagar a peca e colocar de novo.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
