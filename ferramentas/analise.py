"""Cruzamentos entre inventario, backlog e compras.

Nada aqui toca em disco: as funcoes recebem as listas ja carregadas e devolvem
relatorios. E o que permite testar aritmetica de estoque sem montar arvore de
arquivos temporaria.

Estes quatro cruzamentos sao a razao de o inventario ser YAML ligado por id em
vez de planilha. Sem eles, o CSV teria bastado.
"""
from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass

from dados import Componente, ItemCompra, Projeto, STATUS_RESERVA


@dataclass
class Conflito:
    id: str
    nome: str
    tem: int
    reservado: int
    projetos: list[str]


def faltando_por_projeto(
    componentes: list[Componente], projetos: list[Projeto]
) -> dict[str, list[str]]:
    """Por projeto, os ids que o inventario nao cobre — nao existem, ou existem
    em quantidade menor do que o projeto pede."""
    estoque = {c.id: c.qtd for c in componentes}
    return {
        p.id: [i for i, qtd in p.precisa.items() if estoque.get(i, 0) < qtd]
        for p in projetos
    }


def ids_desconhecidos(
    componentes: list[Componente],
    compras: list[ItemCompra],
    projetos: list[Projeto],
) -> list[tuple[str, str]]:
    """Ids pedidos por projeto que nao existem nem no inventario nem na lista de
    compras. Quase sempre e erro de digitacao, e sem isto ele viraria uma peca
    faltando descoberta no dia da montagem."""
    conhecidos = {c.id for c in componentes} | {i.id for i in compras}
    return [
        (p.id, ident)
        for p in projetos
        for ident in p.precisa
        if ident not in conhecidos
    ]


def compras_orfas(compras: list[ItemCompra], projetos: list[Projeto]) -> list[str]:
    """Itens no carrinho que nenhum projeto do backlog pede."""
    pedidos = {ident for p in projetos for ident in p.precisa}
    return [item.id for item in compras if item.id not in pedidos]


def conflitos_de_estoque(
    componentes: list[Componente], projetos: list[Projeto]
) -> list[Conflito]:
    """Componentes reservados por mais projetos do que a quantidade permite.

    So contam os projetos com status em STATUS_RESERVA: ideia e intencao, nao
    compromisso.
    """
    reservado: dict[str, int] = defaultdict(int)
    quem: dict[str, list[str]] = defaultdict(list)
    for p in projetos:
        if p.status not in STATUS_RESERVA:
            continue
        for ident, qtd in p.precisa.items():
            reservado[ident] += qtd
            quem[ident].append(p.id)

    return [
        Conflito(id=c.id, nome=c.nome, tem=c.qtd,
                 reservado=reservado[c.id], projetos=quem[c.id])
        for c in componentes
        if reservado.get(c.id, 0) > c.qtd
    ]
