"""Cria um projeto novo a partir de ferramentas/modelo/.

    python ferramentas/novo-projeto.py sensor-porta "Sensor de porta aberta"

Faz tres coisas que sempre esquecem de fazer a mao: substitui as marcas do
modelo, roda git init, e acrescenta a pasta ao .gitignore da raiz. Essa ultima
e a que mais importa: sem ela o git do hw-laboratorio grava um gitlink e o
conteudo do projeto some sem aviso.

Nao cria o repositorio no GitHub. Publicar e decisao de quem esta trabalhando,
nao efeito colateral de criar pasta.
"""
from __future__ import annotations

import re
import subprocess
import sys
from datetime import date
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
MODELO = BASE / "ferramentas" / "modelo"
PADRAO_NOME = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")


def main(argv: list[str]) -> int:
    if not argv:
        print('uso: python ferramentas/novo-projeto.py <nome-kebab> ["Titulo"]',
              file=sys.stderr)
        return 2

    nome = argv[0]
    titulo = argv[1] if len(argv) > 1 else nome.replace("-", " ").capitalize()
    if not PADRAO_NOME.match(nome):
        print(f"ERRO: '{nome}' precisa ser kebab-case, so [a-z0-9] e hifen",
              file=sys.stderr)
        return 1

    destino = BASE / nome
    if destino.exists():
        print(f"ERRO: {destino} ja existe", file=sys.stderr)
        return 1

    marcas = {
        "{{NOME}}": nome,
        "{{TITULO}}": titulo,
        "{{DESCRICAO}}": "Descrever em uma frase o que o projeto faz.",
        "{{DATA}}": date.today().strftime("%d/%m/%Y"),
    }

    destino.mkdir()
    for origem in sorted(MODELO.iterdir()):
        alvo = destino / origem.name.replace(".modelo", "")
        texto = origem.read_text(encoding="utf-8")
        for marca, valor in marcas.items():
            texto = texto.replace(marca, valor)
        alvo.write_text(texto, encoding="utf-8", newline="\n")

    # O Arduino exige que o .ino more numa pasta com o mesmo nome dele.
    (destino / nome).mkdir()

    subprocess.run(["git", "init", "-q", "-b", "main"], cwd=destino, check=True)

    ignore = BASE / ".gitignore"
    linhas = ignore.read_text(encoding="utf-8").splitlines()
    if f"{nome}/" not in linhas:
        with open(ignore, "a", encoding="utf-8", newline="\n") as f:
            f.write(f"{nome}/\n")

    print(f"{nome}/ criado, git init feito, e {nome}/ acrescentado ao .gitignore da raiz")
    print(f"proximo passo: escrever o sketch em {nome}/{nome}/{nome}.ino")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
