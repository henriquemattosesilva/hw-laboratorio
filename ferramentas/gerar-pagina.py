"""Gera o README.md e o index.html a partir dos YAML.

    python ferramentas/gerar-pagina.py

Os dois arquivos sao GERADOS. Editar qualquer um deles a mao perde a alteracao
na proxima geracao — a mesma regra que vale no hw-codigo-morse.
"""
from __future__ import annotations

import sys
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE / "ferramentas"))

from analise import (  # noqa: E402
    compras_orfas, conflitos_de_estoque, faltando_por_projeto, ids_desconhecidos,
)
from dados import Base, ErroDeDados, carregar_tudo  # noqa: E402

TITULOS = {
    "placas": "Placas",
    "sensores": "Sensores",
    "displays": "Displays",
    "atuadores": "Atuadores",
    "comunicacao": "Comunicação",
    "energia": "Energia",
    "passivos": "Passivos",
    "prototipagem": "Prototipagem",
    "diversos": "Diversos",
}
ORDEM = list(TITULOS)


def por_familia(base: Base) -> dict[str, list]:
    """Agrupa por familia, na ordem de ORDEM.

    Familia sem titulo e erro, nao um caso a ignorar: a peca sumiria da pagina
    sem aviso, porque tanto o HTML quanto o JS iteram sobre os titulos conhecidos.
    Um arquivo componentes/ novo tem que ser registrado em TITULOS.
    """
    desconhecidas = sorted({c.familia for c in base.componentes} - set(TITULOS))
    if desconhecidas:
        raise ErroDeDados(
            f"familia sem titulo: {', '.join(desconhecidas)} — acrescente em "
            "TITULOS no gerar-pagina.py, ou renomeie o arquivo em componentes/")
    grupos: dict[str, list] = {f: [] for f in ORDEM}
    for c in base.componentes:
        grupos[c.familia].append(c)
    for itens in grupos.values():
        itens.sort(key=lambda c: c.nome.lower())
    return grupos


def alertas(base: Base) -> list[str]:
    """As tres coisas que o inventario sabe e a cabeca esquece.

    Emite <b> e <code> porque a pagina consome direto; para_markdown converte.
    """
    linhas: list[str] = []
    for projeto, ident in ids_desconhecidos(base.componentes, base.compras, base.projetos):
        linhas.append(f"<b>Id desconhecido</b> — o projeto <code>{projeto}</code> pede "
                      f"<code>{ident}</code>, que não existe no inventário nem na lista "
                      "de compras.")
    for c in conflitos_de_estoque(base.componentes, base.projetos):
        linhas.append(f"<b>Estoque insuficiente</b> — <code>{c.id}</code> ({c.nome}): você "
                      f"tem {c.tem}, e {c.reservado} estão reservados por "
                      f"{', '.join(c.projetos)}.")
    for ident in compras_orfas(base.compras, base.projetos):
        linhas.append(f"<b>Compra órfã</b> — <code>{ident}</code> está na lista de compras "
                      "e nenhum projeto do backlog pede.")
    return linhas


def para_markdown(linha: str) -> str:
    return (linha.replace("<b>", "**").replace("</b>", "**")
                 .replace("<code>", "`").replace("</code>", "`"))


def montar_readme(base: Base) -> str:
    grupos = por_familia(base)
    p: list[str] = []
    p.append("# hw-laboratorio\n")
    p.append("Inventário de componentes, backlog de projetos e lista de compras da bancada.")
    p.append("Os projetos ficam em repositórios próprios, com prefixo `hw-`.\n")
    p.append("> **Este arquivo é gerado.** Edite os YAML em `componentes/`, `projetos/` e")
    p.append("> `compras/` e rode `python ferramentas/gerar-pagina.py`.\n")

    total = sum(c.qtd for c in base.componentes)
    p.append(f"**{len(base.componentes)} componentes distintos, {total} peças no total.**\n")

    problemas = alertas(base)
    if problemas:
        p.append("## Atenção\n")
        p.extend(f"- {para_markdown(linha)}" for linha in problemas)
        p.append("")

    if base.projetos:
        p.append("## Projetos\n")
        p.append("| Projeto | Status | Falta |")
        p.append("| --- | --- | --- |")
        faltas = faltando_por_projeto(base.componentes, base.projetos)
        for proj in base.projetos:
            falta = ", ".join(f"`{i}`" for i in faltas[proj.id]) or "nada"
            p.append(f"| {proj.titulo} | {proj.status} | {falta} |")
        p.append("")

    if base.compras:
        p.append("## Lista de compras\n")
        p.append("| Item | Qtd | Prioridade | Status | Motivo |")
        p.append("| --- | --- | --- | --- | --- |")
        for item in sorted(base.compras, key=lambda i: (i.prioridade, i.nome)):
            motivo = ", ".join(item.motivo) or "—"
            p.append(f"| {item.nome} | {item.qtd} | {item.prioridade} | "
                     f"{item.status} | {motivo} |")
        p.append("")

    p.append("## Componentes\n")
    for familia in ORDEM:
        itens = grupos.get(familia) or []
        if not itens:
            continue
        p.append(f"### {TITULOS[familia]}\n")
        p.append("| Componente | Qtd | Tensão | Interface | Observação |")
        p.append("| --- | --- | --- | --- | --- |")
        for c in itens:
            nota = (c.notas or "").strip().splitlines()
            resumo = nota[0] if nota else ""
            p.append(f"| {c.nome} | {c.qtd} | {c.tensao or ''} | "
                     f"{c.interface or ''} | {resumo} |")
        p.append("")

    return "\n".join(p).rstrip() + "\n"


def main() -> int:
    # O console do Windows nao entra em UTF-8 sozinho, e os avisos saem com
    # caractere trocado justamente onde eles precisam ser lidos.
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")

    try:
        base = carregar_tudo(BASE)
        readme = montar_readme(base)
    except ErroDeDados as erro:
        print(f"ERRO: {erro}", file=sys.stderr)
        return 1

    (BASE / "README.md").write_text(readme, encoding="utf-8", newline="\n")
    print(f"README.md gerado: {len(base.componentes)} componentes")
    for linha in alertas(base):
        print("  aviso: " + para_markdown(linha).replace("**", "").replace("`", ""))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
