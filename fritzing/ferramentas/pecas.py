"""Onde as pecas moram e como acha-las.

Fonte unica do layout da pasta. Sem isto, cada ferramenta guardaria a sua lista
de pecas e criar peca nova exigiria lembrar de editar todas.
"""
from pathlib import Path
from xml.etree import ElementTree

FRITZING = Path(__file__).resolve().parent.parent
PASTA = FRITZING / "pecas"

# Sufixo do moduleId, para as pecas daqui nao colidirem com as de outra origem
# na biblioteca do Fritzing.
SUFIXO = "-hwlab"


def descobrir(pasta=None):
    """Todas as pecas, em ordem. Peca e pasta que tem part.fzp dentro."""
    return sorted((p.parent for p in Path(pasta or PASTA).glob("*/part.fzp")),
                  key=lambda p: p.name)


def module_id(peca):
    return ElementTree.parse(Path(peca) / "part.fzp").getroot().get("moduleId")


def nome_do_pacote(peca):
    """RF433-TX-FS1000A.fzpz a partir de rf433-tx-fs1000a-hwlab."""
    ident = module_id(peca)
    if ident.endswith(SUFIXO):
        ident = ident[: -len(SUFIXO)]
    return f"{ident.upper()}.fzpz"


def pacote(peca):
    """O .fzpz mora DENTRO da pasta da peca, ao lado do part.fzp.

    E o arquivo que o Fritzing importa por Arquivo > Abrir — o part.fzp sozinho
    nao serve, porque cita as SVGs por caminho relativo que o programa nao
    resolve de uma pasta qualquer. Guardar os dois juntos e o que faz a pasta
    da peca ser autossuficiente: quem abre ela acha o que precisa sem saber
    que existe uma pasta de distribuicao em outro lugar.
    """
    peca = Path(peca)
    return peca / nome_do_pacote(peca)
