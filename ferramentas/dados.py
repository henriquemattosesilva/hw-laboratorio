"""Le e valida os YAML de componentes, projetos e compras.

Este modulo e o unico ponto que toca em disco. Os cruzamentos ficam em
analise.py, que recebe as listas prontas e por isso e testavel sem fixture.

O objetivo da validacao nao e rigor por rigor: e que um id digitado errado
apareca como erro na hora de gerar a pagina, e nao como peca faltando na
bancada no dia da montagem.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path

import yaml

PADRAO_ID = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")
LIMITE_ID = 28
STATUS_VALIDOS = ("ideia", "especificado", "montado", "publicado")
# Projeto montado ou publicado continua ocupando as pecas na protoboard:
# publicar diz respeito ao repositorio, nao ao hardware. So ideia nao reserva.
STATUS_RESERVA = ("especificado", "montado", "publicado")
PRIORIDADES = ("alta", "media", "baixa")
STATUS_COMPRA = ("pesquisando", "comprado", "chegou")


class ErroDeDados(Exception):
    """Dado invalido em algum YAML. A mensagem diz o arquivo e o item."""


@dataclass
class Componente:
    id: str
    nome: str
    qtd: int
    familia: str
    tensao: str | None = None
    interface: str | None = None
    endereco: str | None = None
    biblioteca: str | None = None
    datasheet: str | None = None
    compra: dict | None = None
    notas: str | None = None


@dataclass
class Projeto:
    id: str
    titulo: str
    descricao: str
    status: str
    precisa: dict[str, int] = field(default_factory=dict)
    repositorio: str | None = None


@dataclass
class ItemCompra:
    id: str
    nome: str
    qtd: int
    motivo: list[str] = field(default_factory=list)
    prioridade: str = "media"
    status: str = "pesquisando"
    link: str | None = None
    preco: float | None = None


@dataclass
class Base:
    componentes: list[Componente]
    projetos: list[Projeto]
    compras: list[ItemCompra]


def _ler_yaml(caminho: Path) -> list[dict]:
    if not caminho.exists():
        return []
    dados = yaml.safe_load(caminho.read_text(encoding="utf-8"))
    if dados is None:
        return []  # arquivo so com comentario: valido, e como energia.yaml comeca
    if not isinstance(dados, list):
        raise ErroDeDados(f"{caminho.name}: o arquivo precisa ser uma lista de itens")
    return dados


def _exigir(bruto: dict, campos: tuple[str, ...], onde: str) -> None:
    for campo in campos:
        if bruto.get(campo) in (None, ""):
            raise ErroDeDados(f"{onde}: campo obrigatorio ausente: {campo}")


def _validar_id(valor: str, onde: str) -> str:
    if not isinstance(valor, str) or not PADRAO_ID.match(valor):
        raise ErroDeDados(
            f"{onde}: id '{valor}' precisa ser kebab-case, so [a-z0-9] e hifen")
    if len(valor) > LIMITE_ID:
        raise ErroDeDados(
            f"{onde}: id '{valor}' tem {len(valor)} caracteres, o limite e {LIMITE_ID}")
    return valor


def _validar_escolha(valor: str, opcoes: tuple[str, ...], campo: str, onde: str) -> str:
    if valor not in opcoes:
        raise ErroDeDados(
            f"{onde}: {campo} '{valor}' invalido; use um de: {', '.join(opcoes)}")
    return valor


def carregar_componentes(raiz: Path) -> list[Componente]:
    itens: list[Componente] = []
    vistos: dict[str, str] = {}
    for caminho in sorted((raiz / "componentes").glob("*.yaml")):
        onde_arquivo = f"componentes/{caminho.name}"
        for bruto in _ler_yaml(caminho):
            onde = f"{onde_arquivo} ({bruto.get('id', 'sem id')})"
            _exigir(bruto, ("id", "nome", "qtd"), onde)
            ident = _validar_id(bruto["id"], onde)
            if ident in vistos:
                raise ErroDeDados(
                    f"{onde}: id '{ident}' ja usado em {vistos[ident]}")
            vistos[ident] = onde_arquivo
            itens.append(Componente(
                id=ident,
                nome=bruto["nome"],
                qtd=int(bruto["qtd"]),
                familia=caminho.stem,
                tensao=bruto.get("tensao"),
                interface=bruto.get("interface"),
                endereco=bruto.get("endereco"),
                biblioteca=bruto.get("biblioteca"),
                datasheet=bruto.get("datasheet"),
                compra=bruto.get("compra"),
                notas=bruto.get("notas"),
            ))
    return itens


def carregar_projetos(raiz: Path) -> list[Projeto]:
    itens: list[Projeto] = []
    for bruto in _ler_yaml(raiz / "projetos" / "backlog.yaml"):
        onde = f"projetos/backlog.yaml ({bruto.get('id', 'sem id')})"
        _exigir(bruto, ("id", "titulo", "descricao", "status"), onde)
        precisa = bruto.get("precisa") or {}
        if not isinstance(precisa, dict):
            raise ErroDeDados(
                f"{onde}: precisa tem que ser um mapa de id: quantidade, "
                "nao uma lista — senao a quantidade se perde")
        for ident, qtd in precisa.items():
            _validar_id(ident, onde)
            if not isinstance(qtd, int) or qtd < 1:
                raise ErroDeDados(f"{onde}: quantidade de '{ident}' precisa ser inteiro >= 1")
        itens.append(Projeto(
            id=_validar_id(bruto["id"], onde),
            titulo=bruto["titulo"],
            descricao=bruto["descricao"],
            status=_validar_escolha(bruto["status"], STATUS_VALIDOS, "status", onde),
            precisa=precisa,
            repositorio=bruto.get("repositorio"),
        ))
    return itens


def carregar_compras(raiz: Path) -> list[ItemCompra]:
    itens: list[ItemCompra] = []
    for bruto in _ler_yaml(raiz / "compras" / "desejos.yaml"):
        onde = f"compras/desejos.yaml ({bruto.get('id', 'sem id')})"
        _exigir(bruto, ("id", "nome", "qtd"), onde)
        itens.append(ItemCompra(
            id=_validar_id(bruto["id"], onde),
            nome=bruto["nome"],
            qtd=int(bruto["qtd"]),
            motivo=list(bruto.get("motivo") or []),
            prioridade=_validar_escolha(
                bruto.get("prioridade", "media"), PRIORIDADES, "prioridade", onde),
            status=_validar_escolha(
                bruto.get("status", "pesquisando"), STATUS_COMPRA, "status", onde),
            link=bruto.get("link"),
            preco=bruto.get("preco"),
        ))
    return itens


def carregar_tudo(raiz: Path) -> Base:
    componentes = carregar_componentes(raiz)
    projetos = carregar_projetos(raiz)
    compras = carregar_compras(raiz)
    no_estoque = {c.id for c in componentes}
    for item in compras:
        if item.id in no_estoque:
            raise ErroDeDados(
                f"compras/desejos.yaml: '{item.id}' ja existe em componentes/. "
                "Migracao pela metade: quando a peca chega, ela sai de desejos.yaml.")
    return Base(componentes, projetos, compras)
