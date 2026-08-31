# hw-laboratorio — Plano de Implementação

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Transformar a pasta `c:\HENRIQUE\Claude\Arduino` no repositório `hw-laboratorio`, com o inventário de componentes em YAML ligado por `id`, um gerador que cruza inventário × backlog × compras, e um script que cria projetos novos a partir de um modelo.

**Architecture:** Três camadas com fronteiras rígidas. `ferramentas/dados.py` só faz I/O e validação — lê os YAML e devolve dataclasses. `ferramentas/analise.py` não toca em disco: recebe as listas prontas e devolve os cruzamentos, o que permite testar cada regra com três linhas de fixture. `ferramentas/gerar-pagina.py` orquestra os dois e escreve `README.md` e `index.html`, que são **gerados, nunca editados à mão**.

**Tech Stack:** Python 3.12, PyYAML, pytest 8.4, HTML/CSS/JS de arquivo único (sem framework), PowerShell + Chrome DevTools Protocol para a verificação visual.

---

## Escopo deste plano

Cobre inventário, cruzamentos, geradores e template de projeto. **Não cobre:**

- **Cases 3D** (`cases/`) — plano próprio. Está bloqueado por OpenSCAD não instalado, e a `caixa.scad` só fica útil depois que a peça de calibração for impressa e devolver o número de folga real. Fazer antes disso é chutar tolerância.
- **`referencias/placas.md` e `referencias/energia.md`** — o conteúdo nasce da pesquisa de placas, que é o trabalho seguinte e depende do backlog existir. Este plano cria o backlog; a pesquisa preenche as referências.

Cada um vira software funcionando por conta própria, que é o critério para separar.

## Estrutura de arquivos

| Arquivo | Responsabilidade |
|---|---|
| `ferramentas/dados.py` | Ler os YAML, validar, devolver dataclasses. Único ponto que toca em disco. |
| `ferramentas/analise.py` | Os quatro cruzamentos. Funções puras, sem I/O. |
| `ferramentas/gerar-pagina.py` | Orquestra e escreve `README.md` + `index.html`. |
| `ferramentas/modelo.html` | Molde da página, com marcas `{{...}}`. |
| `ferramentas/novo-projeto.py` | Cria projeto a partir de `ferramentas/modelo/`. |
| `ferramentas/modelo/` | Esqueleto de projeto `hw-*`. |
| `ferramentas/previa.ps1` | Captura a página pelo CDP para conferência visual. |
| `ferramentas/migrar-csv.py` | Script de uso único: CSV do Notion → YAML. Apagado depois. |
| `testes/test_dados.py` | Carga e validação. |
| `testes/test_analise.py` | Os cruzamentos. |

`dados.py` e `analise.py` são separados de propósito: a validação precisa de arquivos em disco para ser testada, os cruzamentos não. Juntar os dois obrigaria a criar árvore de arquivos temporários para testar aritmética de estoque.

---

## Task 1: Ambiente e esqueleto

**Files:**
- Create: `pytest.ini`
- Create: `requisitos.txt`
- Create: `testes/conftest.py`
- Create: `componentes/energia.yaml`
- Create: `projetos/backlog.yaml`
- Create: `compras/desejos.yaml`

- [ ] **Step 1: Instalar as dependências**

```bash
cd /c/HENRIQUE/Claude/Arduino
python -m pip install pyyaml
```

Esperado: `Successfully installed PyYAML-6.x` (ou `Requirement already satisfied`).

- [ ] **Step 2: Registrar as dependências**

Criar `requisitos.txt`:

```text
# python -m pip install -r requisitos.txt
PyYAML>=6.0
pytest>=8.0
```

- [ ] **Step 3: Configurar o pytest**

Criar `pytest.ini`:

```ini
[pytest]
testpaths = testes
python_files = test_*.py
addopts = -q
```

Criar `testes/conftest.py` — sem ele o `import dados` não acha o módulo, porque `ferramentas/` não está no `sys.path`:

```python
"""Poe ferramentas/ no sys.path para os testes importarem dados e analise
sem precisar transformar a pasta em pacote instalavel."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "ferramentas"))
```

- [ ] **Step 4: Criar os três arquivos de dados vazios**

`componentes/energia.yaml`:

```yaml
# Baterias, carregadores, reguladores e conectores de alimentacao.
# Vazio de proposito: e o buraco do inventario que a proxima compra preenche.
[]
```

`projetos/backlog.yaml`:

```yaml
# Ideias e projetos. Ver docs/superpowers/specs para o formato.
# status: ideia | especificado | montado | publicado
# precisa: mapa de id: quantidade
[]
```

`compras/desejos.yaml`:

```yaml
# O que comprar. O id aqui e o MESMO que a peca tera em componentes/
# quando chegar, e por isso um projeto pode pedir uma peca que ainda nao existe.
[]
```

- [ ] **Step 5: Verificar que o pytest roda sem teste nenhum**

```bash
cd /c/HENRIQUE/Claude/Arduino && python -m pytest
```

Esperado: `no tests ran` — sem erro de coleta.

- [ ] **Step 6: Commit**

```bash
git add pytest.ini requisitos.txt testes componentes projetos compras
git commit -m "Esqueleto de testes e os tres arquivos de dados vazios"
```

---

## Task 2: `dados.py` — carga e validação

**Files:**
- Create: `ferramentas/dados.py`
- Test: `testes/test_dados.py`

- [ ] **Step 1: Escrever os testes que falham**

Criar `testes/test_dados.py`:

```python
import pytest
from dados import (
    ErroDeDados, carregar_componentes, carregar_projetos,
    carregar_compras, carregar_tudo,
)


def escrever(raiz, caminho_rel, texto):
    alvo = raiz / caminho_rel
    alvo.parent.mkdir(parents=True, exist_ok=True)
    alvo.write_text(texto, encoding="utf-8")


def test_le_componente_com_campos_minimos(tmp_path):
    escrever(tmp_path, "componentes/sensores.yaml",
             "- id: bmp280\n  nome: Sensor BMP280\n  qtd: 1\n")
    itens = carregar_componentes(tmp_path)
    assert len(itens) == 1
    assert itens[0].id == "bmp280"
    assert itens[0].qtd == 1
    assert itens[0].familia == "sensores"
    assert itens[0].tensao is None


def test_arquivo_vazio_nao_e_erro(tmp_path):
    escrever(tmp_path, "componentes/energia.yaml", "[]\n")
    assert carregar_componentes(tmp_path) == []


def test_recusa_id_repetido_entre_arquivos(tmp_path):
    escrever(tmp_path, "componentes/sensores.yaml",
             "- id: ldr\n  nome: LDR\n  qtd: 1\n")
    escrever(tmp_path, "componentes/passivos.yaml",
             "- id: ldr\n  nome: LDR de novo\n  qtd: 2\n")
    with pytest.raises(ErroDeDados, match="ja usado"):
        carregar_componentes(tmp_path)


def test_recusa_id_fora_do_kebab_case(tmp_path):
    escrever(tmp_path, "componentes/sensores.yaml",
             "- id: BMP_280\n  nome: Sensor\n  qtd: 1\n")
    with pytest.raises(ErroDeDados, match="kebab-case"):
        carregar_componentes(tmp_path)


def test_recusa_campo_obrigatorio_ausente(tmp_path):
    escrever(tmp_path, "componentes/sensores.yaml",
             "- id: bmp280\n  nome: Sensor\n")
    with pytest.raises(ErroDeDados, match="qtd"):
        carregar_componentes(tmp_path)


def test_le_projeto_com_precisa_como_mapa(tmp_path):
    escrever(tmp_path, "projetos/backlog.yaml",
             "- id: estufa\n  titulo: Estufa\n  descricao: teste\n"
             "  status: especificado\n  precisa:\n    dht22: 1\n    led-vermelho: 3\n")
    projetos = carregar_projetos(tmp_path)
    assert projetos[0].precisa == {"dht22": 1, "led-vermelho": 3}


def test_recusa_status_invalido(tmp_path):
    escrever(tmp_path, "projetos/backlog.yaml",
             "- id: estufa\n  titulo: Estufa\n  descricao: teste\n"
             "  status: quase-pronto\n  precisa: {}\n")
    with pytest.raises(ErroDeDados, match="status"):
        carregar_projetos(tmp_path)


def test_recusa_precisa_como_lista(tmp_path):
    escrever(tmp_path, "projetos/backlog.yaml",
             "- id: estufa\n  titulo: Estufa\n  descricao: teste\n"
             "  status: ideia\n  precisa: [dht22]\n")
    with pytest.raises(ErroDeDados, match="mapa"):
        carregar_projetos(tmp_path)


def test_le_item_de_compra(tmp_path):
    escrever(tmp_path, "compras/desejos.yaml",
             "- id: esp32c3-supermini\n  nome: ESP32-C3 SuperMini\n  qtd: 2\n"
             "  motivo: [estufa]\n  prioridade: alta\n  status: pesquisando\n")
    itens = carregar_compras(tmp_path)
    assert itens[0].prioridade == "alta"
    assert itens[0].motivo == ["estufa"]


def test_recusa_item_que_esta_nos_dois_lugares(tmp_path):
    escrever(tmp_path, "componentes/placas.yaml",
             "- id: esp32c3\n  nome: ESP32-C3\n  qtd: 1\n")
    escrever(tmp_path, "compras/desejos.yaml",
             "- id: esp32c3\n  nome: ESP32-C3\n  qtd: 2\n")
    with pytest.raises(ErroDeDados, match="Migracao pela metade"):
        carregar_tudo(tmp_path)
```

- [ ] **Step 2: Rodar e confirmar que falham**

```bash
cd /c/HENRIQUE/Claude/Arduino && python -m pytest testes/test_dados.py
```

Esperado: 10 erros de coleta com `ModuleNotFoundError: No module named 'dados'`.

- [ ] **Step 3: Escrever `ferramentas/dados.py`**

```python
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
```

- [ ] **Step 4: Rodar e confirmar que passam**

```bash
cd /c/HENRIQUE/Claude/Arduino && python -m pytest testes/test_dados.py
```

Esperado: `10 passed`.

- [ ] **Step 5: Commit**

```bash
git add ferramentas/dados.py testes/test_dados.py
git commit -m "dados.py: le e valida os YAML, com id unico e precisa como mapa"
```

---

## Task 3: `analise.py` — os quatro cruzamentos

**Files:**
- Create: `ferramentas/analise.py`
- Test: `testes/test_analise.py`

- [ ] **Step 1: Escrever os testes que falham**

Criar `testes/test_analise.py`:

```python
from analise import (
    Conflito, compras_orfas, conflitos_de_estoque,
    faltando_por_projeto, ids_desconhecidos,
)
from dados import Componente, ItemCompra, Projeto


def comp(ident, qtd=1, nome=None):
    return Componente(id=ident, nome=nome or ident, qtd=qtd, familia="teste")


def proj(ident, precisa, status="especificado"):
    return Projeto(id=ident, titulo=ident, descricao="", status=status, precisa=precisa)


def test_falta_o_que_nao_esta_no_inventario():
    componentes = [comp("dht22")]
    projetos = [proj("estufa", {"dht22": 1, "esp32c3": 1})]
    assert faltando_por_projeto(componentes, projetos) == {"estufa": ["esp32c3"]}


def test_falta_tambem_quando_a_quantidade_nao_cobre():
    componentes = [comp("led-vermelho", qtd=2)]
    projetos = [proj("painel", {"led-vermelho": 5})]
    assert faltando_por_projeto(componentes, projetos) == {"painel": ["led-vermelho"]}


def test_projeto_coberto_nao_aparece_faltando():
    componentes = [comp("led-vermelho", qtd=5)]
    projetos = [proj("painel", {"led-vermelho": 5})]
    assert faltando_por_projeto(componentes, projetos) == {"painel": []}


def test_id_que_nao_existe_em_lugar_nenhum_e_reportado():
    componentes = [comp("dht22")]
    compras = [ItemCompra(id="esp32c3", nome="ESP32", qtd=1)]
    projetos = [proj("estufa", {"dht22": 1, "esp32c3": 1, "dht-22": 1})]
    assert ids_desconhecidos(componentes, compras, projetos) == [("estufa", "dht-22")]


def test_compra_que_nenhum_projeto_pede_e_orfa():
    compras = [ItemCompra(id="esp32c3", nome="ESP32", qtd=1),
               ItemCompra(id="oled", nome="OLED", qtd=1)]
    projetos = [proj("estufa", {"esp32c3": 1})]
    assert compras_orfas(compras, projetos) == ["oled"]


def test_conflito_quando_dois_projetos_pedem_mais_do_que_existe():
    componentes = [comp("servo-sg90", qtd=2, nome="Micro Servo SG90")]
    projetos = [proj("braco", {"servo-sg90": 2}), proj("porta", {"servo-sg90": 1})]
    assert conflitos_de_estoque(componentes, projetos) == [
        Conflito(id="servo-sg90", nome="Micro Servo SG90", tem=2,
                 reservado=3, projetos=["braco", "porta"])
    ]


def test_ideia_nao_reserva_estoque():
    componentes = [comp("servo-sg90", qtd=2)]
    projetos = [proj("braco", {"servo-sg90": 2}),
                proj("porta", {"servo-sg90": 1}, status="ideia")]
    assert conflitos_de_estoque(componentes, projetos) == []


def test_publicado_continua_reservando():
    componentes = [comp("servo-sg90", qtd=1)]
    projetos = [proj("braco", {"servo-sg90": 1}, status="publicado"),
                proj("porta", {"servo-sg90": 1}, status="especificado")]
    assert len(conflitos_de_estoque(componentes, projetos)) == 1
```

- [ ] **Step 2: Rodar e confirmar que falham**

```bash
cd /c/HENRIQUE/Claude/Arduino && python -m pytest testes/test_analise.py
```

Esperado: erro de coleta `ModuleNotFoundError: No module named 'analise'`.

- [ ] **Step 3: Escrever `ferramentas/analise.py`**

```python
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
```

- [ ] **Step 4: Rodar e confirmar que passam**

```bash
cd /c/HENRIQUE/Claude/Arduino && python -m pytest
```

Esperado: `18 passed`.

- [ ] **Step 5: Commit**

```bash
git add ferramentas/analise.py testes/test_analise.py
git commit -m "analise.py: falta por projeto, ids desconhecidos, orfas e conflito"
```

---

## Task 4: Migrar o CSV do Notion para YAML

O CSV tem 85 linhas. A migração é mecânica; o que **não** é mecânico é o `id`, porque
`sensor-de-pressao-e-temperatura-bmp280` é inútil. O script gera um id derivado do nome e a
curadoria vem no passo seguinte, ainda dentro desta task. Como o backlog está vazio, mudar id
agora não quebra nada — depois quebraria.

**Files:**
- Create: `ferramentas/migrar-csv.py`
- Create: `componentes/*.yaml` (8 arquivos, saída do script)
- Delete: os dois CSV e o `.md` do Notion (só no fim da task)

- [ ] **Step 1: Escrever o script de migração**

Criar `ferramentas/migrar-csv.py`:

```python
"""Uso unico: converte o CSV exportado do Notion nos YAML de componentes.

    python ferramentas/migrar-csv.py

Mapeia a categoria do Notion para a familia (arquivo de destino) e gera um id
provisorio a partir do nome. Os ids provisorios sao longos e feios de proposito:
eles precisam ser revisados a mao logo depois, e id feio chama atencao.

Este arquivo e apagado assim que a migracao for conferida.
"""
from __future__ import annotations

import csv
import re
import unicodedata
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
ORIGEM = BASE / "componentes" / "Componentes Arduino fa27f0eb0625482f8e40d345f5015ced.csv"
DESTINO = BASE / "componentes"

# Categoria do Notion -> arquivo de destino. A primeira categoria que casar vence,
# por isso a ordem importa: "Placa, Wireless e IoT" tem que cair em placas.
REGRAS = [
    ("Placa", "placas"),
    ("Prototipagem", "prototipagem"),
    ("Jumpers", "prototipagem"),
    ("Cabos", "prototipagem"),
    ("Partes", "prototipagem"),
    ("Display", "displays"),
    ("Radio Frequência", "comunicacao"),
    ("RFID", "comunicacao"),
    ("Wireless e IoT", "comunicacao"),
    ("Infravermelho", "comunicacao"),
    ("Sensores", "sensores"),
    ("Motor", "atuadores"),
    ("Relé", "atuadores"),
    ("Som", "atuadores"),
    ("Iluminação", "passivos"),
    ("Resistor", "passivos"),
    ("Transistor", "passivos"),
    ("Botões", "passivos"),
    ("Potenciômetro", "passivos"),
    ("Armazenamento de Dados", "diversos"),
    ("Outros", "diversos"),
]


def familia(categoria: str) -> str:
    for chave, destino in REGRAS:
        if chave in categoria:
            return destino
    raise SystemExit(f"categoria sem regra: {categoria!r}")


def id_provisorio(nome: str) -> str:
    sem_acento = unicodedata.normalize("NFKD", nome).encode("ascii", "ignore").decode()
    return re.sub(r"-+", "-", re.sub(r"[^a-z0-9]+", "-", sem_acento.lower())).strip("-")


def escapar(valor: str) -> str:
    return valor.replace("\\", "\\\\").replace('"', '\\"')


def main() -> int:
    grupos: dict[str, list[tuple[str, str, int]]] = {}
    with open(ORIGEM, encoding="utf-8-sig", newline="") as f:
        for linha in csv.DictReader(f):
            nome = linha["Componente"].strip()
            if not nome:
                continue
            # "Sensor de Cor RGB" veio do Notion sem quantidade preenchida.
            qtd = int(linha["Qntd"]) if linha["Qntd"].strip() else 1
            grupos.setdefault(familia(linha["Categoria"]), []).append(
                (id_provisorio(nome), nome, qtd))

    for arquivo, itens in sorted(grupos.items()):
        alvo = DESTINO / f"{arquivo}.yaml"
        with open(alvo, "w", encoding="utf-8", newline="\n") as f:
            f.write(f"# {arquivo.capitalize()} — migrado do export do Notion.\n")
            for ident, nome, qtd in sorted(itens, key=lambda t: t[1]):
                f.write(f'- id: {ident}\n  nome: "{escapar(nome)}"\n  qtd: {qtd}\n')
        print(f"{alvo.name}: {len(itens)} itens")

    total = sum(len(v) for v in grupos.values())
    print(f"total: {total} itens")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

- [ ] **Step 2: Rodar a migração**

```bash
cd /c/HENRIQUE/Claude/Arduino && python ferramentas/migrar-csv.py
```

Esperado: oito linhas de arquivo e `total: 85 itens`. Se aparecer `categoria sem regra`,
acrescentar a regra e rodar de novo.

- [ ] **Step 3: Conferir a migração contra a origem**

Este passo existe porque migração silenciosa é onde item some sem ninguém notar. O comando
compara nome a nome e quantidade a quantidade:

```bash
cd /c/HENRIQUE/Claude/Arduino && python - <<'PY'
import csv, sys
from pathlib import Path
sys.path.insert(0, "ferramentas")
from dados import carregar_componentes

origem = Path("componentes/Componentes Arduino fa27f0eb0625482f8e40d345f5015ced.csv")
esperado = {}
with open(origem, encoding="utf-8-sig", newline="") as f:
    for l in csv.DictReader(f):
        if l["Componente"].strip():
            esperado[l["Componente"].strip()] = int(l["Qntd"]) if l["Qntd"].strip() else 1

achado = {c.nome: c.qtd for c in carregar_componentes(Path("."))}
faltam = sorted(set(esperado) - set(achado))
sobram = sorted(set(achado) - set(esperado))
difs = sorted(n for n in set(esperado) & set(achado) if esperado[n] != achado[n])
print("faltam:", faltam or "nenhum")
print("sobram:", sobram or "nenhum")
print("quantidade divergente:", difs or "nenhuma")
print("OK" if not (faltam or sobram or difs) else "DIVERGENTE")
PY
```

Esperado: `faltam: nenhum`, `sobram: nenhum`, `quantidade divergente: nenhuma`, `OK`.

- [ ] **Step 4: Encurtar os ids à mão**

Abrir cada `componentes/*.yaml` e trocar os ids provisórios por ids curtos e estáveis.
A regra: **o id é como você chama a peça em voz alta**, não a descrição da loja.

Exemplos concretos do que trocar:

```yaml
# antes                                          # depois
- id: sensor-de-pressao-e-temperatura-bmp280   → id: bmp280
- id: modulo-esp8266-esp-12e-ch340g-nodemcu    → id: esp8266-nodemcu
- id: arduino-nano-v3-0-atmega328-5v           → id: arduino-nano
- id: sensor-de-distancia-ultrassonico-hc-sr04 → id: hc-sr04
- id: micro-servo-9g-sg90                      → id: servo-sg90
- id: resistor-220                             → id: resistor-220r
- id: resistor-10k                             → id: resistor-10k     (ja bom)
- id: led-vermelho-5mm-difuso                  → id: led-vermelho-dif
- id: jumper-macho-macho-22cm                  → id: jumper-mm-22
```

O limite de 28 caracteres em `dados.py` reprova o que ficou longo demais, então o próprio
teste do passo seguinte cobra a curadoria.

- [ ] **Step 5: Confirmar que os dados continuam válidos e íntegros**

```bash
cd /c/HENRIQUE/Claude/Arduino && python -c "
import sys; sys.path.insert(0,'ferramentas')
from pathlib import Path
from dados import carregar_tudo
b = carregar_tudo(Path('.'))
print(f'{len(b.componentes)} componentes, {len(b.projetos)} projetos, {len(b.compras)} compras')
maiores = sorted(b.componentes, key=lambda c: -len(c.id))[:5]
print('ids mais longos:', [(c.id, len(c.id)) for c in maiores])
"
```

Esperado: `85 componentes, 0 projetos, 0 compras` e nenhum id acima de 28 caracteres.
Se `ErroDeDados` aparecer, ele diz o arquivo e o item.

- [ ] **Step 6: Apagar a origem e o script de uso único**

Os CSVs estão no primeiro commit; apagar aqui não perde nada e a conferência do Step 3 já
provou que a migração está completa.

```bash
cd /c/HENRIQUE/Claude/Arduino
git rm -q "componentes/Componentes Arduino fa27f0eb0625482f8e40d345f5015ced.csv" \
          "componentes/Componentes Arduino fa27f0eb0625482f8e40d345f5015ced_all.csv" \
          "componentes/Lista de Componentes a57d7ddacd8e40d6af0134cc78e0caf5.md"
rm ferramentas/migrar-csv.py
```

- [ ] **Step 7: Commit**

```bash
git add -A
git commit -m "Inventario em YAML: 85 componentes migrados do Notion e conferidos"
```

---

## Task 5: Curadoria dos campos que evitam erro de montagem

A migração trouxe só nome e quantidade. O valor do inventário está nos campos que respondem
*serve nesse projeto?* — e principalmente no `notas`, que guarda a armadilha de cada peça.

**Não preencher tudo.** Resistor e jumper não têm o que dizer. Preencher os módulos e
sensores, que são onde o erro acontece.

**Files:**
- Modify: `componentes/sensores.yaml`, `componentes/placas.yaml`, `componentes/displays.yaml`, `componentes/comunicacao.yaml`, `componentes/atuadores.yaml`, `componentes/diversos.yaml`

- [ ] **Step 1: Preencher os campos ricos dos módulos e sensores**

Para cada item dessas seis famílias, acrescentar o que for verdade. Modelo do formato final:

```yaml
- id: bmp280
  nome: "Sensor de Pressão e Temperatura BMP280"
  qtd: 1
  tensao: "3,3 V no chip; o módulo com regulador aceita 5 V"
  interface: I2C
  endereco: "0x76 (algumas placas 0x77)"
  biblioteca: Adafruit_BMP280
  datasheet: https://www.bosch-sensortec.com/products/environmental-sensors/pressure-sensors/bmp280/
  notas: |
    Não mede umidade. O que mede é o BME280, fisicamente quase idêntico e com o
    mesmo endereço — comprar um pensando no outro é o erro comum.

- id: dht22
  nome: "Sensor de Umidade e Temperatura AM3202 DHT22"
  qtd: 1
  tensao: "3,3 V a 5 V"
  interface: "1 fio proprietário (não é 1-Wire da Dallas)"
  biblioteca: DHT sensor library (Adafruit)
  notas: |
    Leitura no máximo a cada 2 s; ler mais rápido devolve o valor anterior sem avisar.
    Precisa de pull-up de 10 kΩ no pino de dados se o módulo não tiver.

- id: ds18b20
  nome: "Sensor de Temperatura a Prova D'água DS18B20"
  qtd: 2
  tensao: "3,0 V a 5,5 V"
  interface: 1-Wire
  biblioteca: OneWire + DallasTemperature
  notas: |
    Precisa de pull-up de 4,7 kΩ entre dados e VCC — sem ele não responde.
    Vários sensores compartilham o mesmo pino, cada um com endereço de 64 bits.

- id: esp8266-nodemcu
  nome: "Módulo ESP8266 ESP-12E CH340G NodeMCU"
  qtd: 1
  tensao: "3,3 V nos pinos; alimentação pela USB (micro-USB)"
  interface: "Wi-Fi 2,4 GHz; sem Bluetooth"
  notas: |
    Os pinos NÃO são tolerantes a 5 V. Ligar sensor de 5 V direto queima.
    Um único pino analógico (A0), e ele lê no máximo 1,0 V no chip — a placa
    tem divisor para 3,3 V.
```

Campos que se aplicam a poucos itens (`endereco`, `datasheet`) ficam de fora quando não
houver. Campo vazio só suja o arquivo.

- [ ] **Step 2: Validar depois de cada arquivo editado**

YAML quebra fácil com indentação e com dois-pontos dentro de texto. Rodar após cada arquivo:

```bash
cd /c/HENRIQUE/Claude/Arduino && python -c "
import sys; sys.path.insert(0,'ferramentas')
from pathlib import Path
from dados import carregar_tudo
b = carregar_tudo(Path('.'))
com_notas = sum(1 for c in b.componentes if c.notas)
print(f'{len(b.componentes)} componentes, {com_notas} com notas')
"
```

Esperado: 85 componentes e nenhum erro. Ao final da task, `com notas` acima de 25.

- [ ] **Step 3: Commit**

```bash
git add componentes
git commit -m "Campos ricos nos modulos e sensores, com as armadilhas em notas"
```

---

## Task 6: `gerar-pagina.py` — o `README.md`

**Files:**
- Create: `ferramentas/gerar-pagina.py`
- Create: `README.md` (saída)

- [ ] **Step 1: Escrever o gerador do README**

Criar `ferramentas/gerar-pagina.py`:

```python
"""Gera o README.md e o index.html a partir dos YAML.

    python ferramentas/gerar-pagina.py

Os dois arquivos sao GERADOS. Editar qualquer um deles a mao perde a alteracao
na proxima geracao — a mesma regra que vale no hw-codigo-morse.
"""
from __future__ import annotations

import json
import sys
from dataclasses import asdict
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
    """As tres coisas que o inventario sabe e a cabeca esquece."""
    linhas: list[str] = []
    for projeto, ident in ids_desconhecidos(base.componentes, base.compras, base.projetos):
        linhas.append(f"**Id desconhecido** — o projeto `{projeto}` pede `{ident}`, "
                      "que não existe no inventário nem na lista de compras.")
    for c in conflitos_de_estoque(base.componentes, base.projetos):
        linhas.append(f"**Estoque insuficiente** — `{c.id}` ({c.nome}): você tem {c.tem}, "
                      f"e {c.reservado} estão reservados por {', '.join(c.projetos)}.")
    for ident in compras_orfas(base.compras, base.projetos):
        linhas.append(f"**Compra órfã** — `{ident}` está na lista de compras e nenhum "
                      "projeto do backlog pede.")
    return linhas


def montar_readme(base: Base) -> str:
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
        p.extend(f"- {linha}" for linha in problemas)
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
            p.append(f"| {item.nome} | {item.qtd} | {item.prioridade} | {item.status} | {motivo} |")
        p.append("")

    p.append("## Componentes\n")
    grupos = por_familia(base)
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
    try:
        base = carregar_tudo(BASE)
    except ErroDeDados as erro:
        print(f"ERRO: {erro}", file=sys.stderr)
        return 1

    destino = BASE / "README.md"
    destino.write_text(montar_readme(base), encoding="utf-8", newline="\n")
    print(f"README.md gerado: {len(base.componentes)} componentes")
    for linha in alertas(base):
        print("  aviso: " + linha.replace("**", ""))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

- [ ] **Step 2: Gerar e conferir**

```bash
cd /c/HENRIQUE/Claude/Arduino && python ferramentas/gerar-pagina.py && head -30 README.md
```

Esperado: `README.md gerado: 85 componentes`, nenhum aviso (backlog e compras ainda vazios),
e um README com as tabelas por família.

- [ ] **Step 3: Provar que os alertas aparecem**

Criar um projeto de teste no backlog para ver os três cruzamentos funcionando de verdade —
gerador que nunca alertou é gerador não testado:

```bash
cd /c/HENRIQUE/Claude/Arduino && cat > projetos/backlog.yaml <<'YAML'
- id: teste-descartavel
  titulo: Teste descartável
  descricao: Existe só para provar que os alertas aparecem
  status: especificado
  precisa:
    servo-sg90: 5
    id-que-nao-existe: 1
YAML
python ferramentas/gerar-pagina.py
```

Esperado: dois avisos — `Id desconhecido` para `id-que-nao-existe`, e `Estoque insuficiente`
para `servo-sg90` (tem 2, reservados 5).

- [ ] **Step 4: Desfazer o backlog de teste**

```bash
cd /c/HENRIQUE/Claude/Arduino && git checkout projetos/backlog.yaml && python ferramentas/gerar-pagina.py
```

Esperado: nenhum aviso.

- [ ] **Step 5: Commit**

```bash
git add ferramentas/gerar-pagina.py README.md
git commit -m "gerar-pagina.py: README com inventario, projetos, compras e alertas"
```

---

## Task 7: `modelo.html` e o `index.html`

A página existe para ser aberta no celular dentro da loja. O que importa é a busca funcionar
e a tabela caber em 390 px. Segue a linguagem visual do `hw-codigo-morse`: fundo escuro, IBM
Plex Mono nos títulos e nos dados, Public Sans no texto corrido.

**Files:**
- Create: `ferramentas/modelo.html`
- Modify: `ferramentas/gerar-pagina.py`
- Create: `index.html` (saída)

- [ ] **Step 1: Criar `ferramentas/modelo.html`**

```html
<!doctype html>
<html lang="pt-BR">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>hw-laboratorio — inventário da bancada</title>
<meta name="description" content="Componentes, projetos e lista de compras da bancada de eletrônica.">
<meta name="color-scheme" content="dark">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;500;600;700&family=Public+Sans:wght@400;500;600;700&display=swap" rel="stylesheet">
<link rel="icon" href="data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 32 32'><rect width='32' height='32' rx='6' fill='%231554B8'/><rect x='7' y='9' width='18' height='3' rx='1.5' fill='%23CFE6FF'/><rect x='7' y='15' width='18' height='3' rx='1.5' fill='%2345D964'/><rect x='7' y='21' width='11' height='3' rx='1.5' fill='%23FFC24B'/></svg>">
<style>
:root{
  --tinta:#060911; --painel:#0E1526; --painel2:#131C31; --borda:#22304E;
  --texto:#D6E2F2; --fraco:#8296B4; --apagado:#465873;
  --azul:#2C7BE5; --verde:#45D964; --ambar:#FFC24B; --vermelho:#FF5B52;
  --mono:'IBM Plex Mono','SFMono-Regular',ui-monospace,monospace;
  --sans:'Public Sans',-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;
  --larg:1120px;
}
*{box-sizing:border-box}
html{-webkit-text-size-adjust:100%}
body{margin:0;background:var(--tinta);color:var(--texto);
  font-family:var(--sans);font-size:16px;line-height:1.6;-webkit-font-smoothing:antialiased}
.env{max-width:var(--larg);margin:0 auto;padding:0 18px}
a{color:var(--azul)}
:focus-visible{outline:2px solid var(--ambar);outline-offset:3px;border-radius:4px}

header{padding:40px 0 26px;border-bottom:1px solid var(--borda)}
.olho{font-family:var(--mono);font-size:12px;letter-spacing:.14em;color:var(--fraco);
  text-transform:uppercase;margin:0 0 12px}
h1{font-family:var(--mono);font-weight:700;letter-spacing:-.03em;line-height:1.05;
  font-size:clamp(2rem,7vw,3.2rem);margin:0 0 10px;text-transform:uppercase}
.resumo{color:var(--fraco);margin:0}

.barra{position:sticky;top:0;z-index:10;background:rgba(6,9,17,.94);
  backdrop-filter:blur(10px);border-bottom:1px solid var(--borda);padding:12px 0}
.busca{width:100%;padding:12px 14px;font-family:var(--mono);font-size:16px;
  color:var(--texto);background:var(--painel);border:1px solid var(--borda);border-radius:8px}
.busca::placeholder{color:var(--apagado)}
.filtros{display:flex;gap:8px;overflow-x:auto;scrollbar-width:none;margin-top:10px}
.filtros::-webkit-scrollbar{display:none}
.filtros button{font-family:var(--mono);font-size:12px;white-space:nowrap;cursor:pointer;
  color:var(--fraco);background:var(--painel);border:1px solid var(--borda);
  border-radius:999px;padding:7px 13px}
.filtros button[aria-pressed="true"]{color:var(--tinta);background:var(--azul);
  border-color:var(--azul);font-weight:600}

.aviso{background:var(--painel2);border-left:3px solid var(--ambar);
  padding:12px 14px;margin:14px 0;border-radius:0 8px 8px 0;font-size:14.5px}
.aviso b{color:var(--ambar)}

section{padding:26px 0 4px}
h2{font-family:var(--mono);font-size:13px;letter-spacing:.12em;text-transform:uppercase;
  color:var(--fraco);margin:0 0 12px;padding-bottom:8px;border-bottom:1px solid var(--borda)}

.peca{background:var(--painel);border:1px solid var(--borda);border-radius:10px;
  padding:13px 15px;margin-bottom:9px}
.peca-topo{display:flex;gap:12px;align-items:baseline;justify-content:space-between}
.peca-nome{font-weight:600;line-height:1.3}
.peca-qtd{font-family:var(--mono);font-size:13px;color:var(--verde);white-space:nowrap}
.peca-id{font-family:var(--mono);font-size:11.5px;color:var(--apagado);margin-top:3px}
.peca-campos{display:flex;flex-wrap:wrap;gap:6px;margin-top:9px}
.campo{font-family:var(--mono);font-size:11.5px;color:var(--fraco);
  background:var(--painel2);border:1px solid var(--borda);border-radius:5px;padding:3px 8px}
.peca-notas{margin-top:9px;font-size:14px;color:var(--fraco);
  border-top:1px solid var(--borda);padding-top:9px;white-space:pre-line}
.vazio{color:var(--apagado);font-family:var(--mono);font-size:13px;padding:26px 0}

footer{border-top:1px solid var(--borda);margin-top:36px;padding:22px 0 40px;
  font-family:var(--mono);font-size:12px;color:var(--apagado)}
</style>
</head>
<body>
<header class="env">
  <p class="olho">bancada de eletrônica</p>
  <h1>hw-laboratorio</h1>
  <p class="resumo">{{RESUMO}}</p>
</header>

<div class="barra">
  <div class="env">
    <input class="busca" id="busca" type="search" autocomplete="off"
           placeholder="buscar por nome, id, interface ou nota…"
           aria-label="Buscar componente">
    <div class="filtros" id="filtros"></div>
  </div>
</div>

<main class="env" id="lista"></main>

<footer class="env">
  gerado por ferramentas/gerar-pagina.py — não editar à mão
</footer>

<script type="application/json" id="dados">{{DADOS}}</script>
<script>
const DADOS = JSON.parse(document.getElementById('dados').textContent);
const lista = document.getElementById('lista');
const busca = document.getElementById('busca');
const filtros = document.getElementById('filtros');
let familiaAtiva = 'tudo';

const familias = ['tudo', ...new Set(DADOS.componentes.map(c => c.familia))];
for (const f of familias) {
  const b = document.createElement('button');
  b.textContent = DADOS.titulos[f] || 'Tudo';
  b.setAttribute('aria-pressed', String(f === 'tudo'));
  b.onclick = () => {
    familiaAtiva = f;
    [...filtros.children].forEach((o, i) => o.setAttribute('aria-pressed', String(familias[i] === f)));
    desenhar();
  };
  filtros.appendChild(b);
}

function combina(c, termo) {
  if (!termo) return true;
  const alvo = [c.nome, c.id, c.interface, c.tensao, c.biblioteca, c.notas]
    .filter(Boolean).join(' ').toLowerCase();
  return termo.split(/\s+/).every(p => alvo.includes(p));
}

function cartao(c) {
  const el = document.createElement('article');
  el.className = 'peca';
  const campos = [c.tensao, c.interface, c.endereco, c.biblioteca]
    .filter(Boolean).map(v => `<span class="campo">${esc(v)}</span>`).join('');
  el.innerHTML =
    `<div class="peca-topo"><div><div class="peca-nome">${esc(c.nome)}</div>` +
    `<div class="peca-id">${esc(c.id)}</div></div>` +
    `<div class="peca-qtd">${c.qtd}×</div></div>` +
    (campos ? `<div class="peca-campos">${campos}</div>` : '') +
    (c.notas ? `<div class="peca-notas">${esc(c.notas.trim())}</div>` : '');
  return el;
}

function esc(s) {
  return String(s).replace(/[&<>"]/g, m => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[m]));
}

function desenhar() {
  const termo = busca.value.trim().toLowerCase();
  lista.textContent = '';

  for (const a of DADOS.alertas) {
    const el = document.createElement('div');
    el.className = 'aviso';
    el.innerHTML = a;
    lista.appendChild(el);
  }

  let mostrados = 0;
  for (const familia of Object.keys(DADOS.titulos)) {
    if (familiaAtiva !== 'tudo' && familiaAtiva !== familia) continue;
    const itens = DADOS.componentes.filter(c => c.familia === familia && combina(c, termo));
    if (!itens.length) continue;
    const sec = document.createElement('section');
    sec.innerHTML = `<h2>${DADOS.titulos[familia]} — ${itens.length}</h2>`;
    itens.forEach(c => sec.appendChild(cartao(c)));
    lista.appendChild(sec);
    mostrados += itens.length;
  }

  if (!mostrados) {
    const v = document.createElement('p');
    v.className = 'vazio';
    v.textContent = 'nada encontrado';
    lista.appendChild(v);
  }
}

busca.addEventListener('input', desenhar);
desenhar();
</script>
</body>
</html>
```

- [ ] **Step 2: Acrescentar a geração do HTML ao `gerar-pagina.py`**

Substituir a função `main()` por esta versão, e acrescentar `montar_html()` logo acima dela:

```python
def montar_html(base: Base) -> str:
    molde = (BASE / "ferramentas" / "modelo.html").read_text(encoding="utf-8")

    grupos = por_familia(base)
    componentes = [asdict(c) for familia in ORDEM for c in grupos[familia]]

    dados = {
        "titulos": TITULOS,
        "componentes": componentes,
        "alertas": alertas(base),
    }
    # </script> dentro do JSON encerraria a tag e quebraria a pagina inteira sem aviso.
    bruto = json.dumps(dados, ensure_ascii=False).replace("</", "<\\/")

    total = sum(c.qtd for c in base.componentes)
    resumo = f"{len(base.componentes)} componentes distintos, {total} peças no total."

    pagina = molde.replace("{{DADOS}}", bruto).replace("{{RESUMO}}", resumo)
    sobrou = [m for m in ("{{DADOS}}", "{{RESUMO}}") if m in pagina]
    if sobrou:
        raise ErroDeDados(f"marcas nao substituidas no modelo: {', '.join(sobrou)}")
    return pagina


def main() -> int:
    # Os dois sao montados antes de qualquer escrita: se um falhar, o par nao
    # fica meio gerado, com um README novo e uma pagina velha.
    try:
        base = carregar_tudo(BASE)
        readme = montar_readme(base)
        html = montar_html(base)
    except ErroDeDados as erro:
        print(f"ERRO: {erro}", file=sys.stderr)
        return 1

    (BASE / "README.md").write_text(readme, encoding="utf-8", newline="\n")
    (BASE / "index.html").write_text(html, encoding="utf-8", newline="\n")
    print(f"README.md e index.html gerados: {len(base.componentes)} componentes, "
          f"{len(html):,} bytes de pagina".replace(",", "."))
    for linha in alertas(base):
        print("  aviso: " + linha.replace("**", ""))
    return 0
```

Os alertas precisam servir aos dois formatos. `alertas()` passa a emitir `<b>`, que é o que a
página consome, e o README converte para `**` na hora de escrever. Substituir `alertas()` por
esta versão:

```python
def alertas(base: Base) -> list[str]:
    """As tres coisas que o inventario sabe e a cabeca esquece.

    Emite <b> porque a pagina consome direto; montar_readme() converte para **.
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
```

E trocar as duas linhas que consomem `alertas()` fora da página:

```python
# em montar_readme(), dentro do bloco `if problemas:`
        p.extend(f"- {para_markdown(linha)}" for linha in problemas)

# em main(), no laco final
    for linha in alertas(base):
        print("  aviso: " + para_markdown(linha).replace("**", "").replace("`", ""))
```

- [ ] **Step 3: Gerar e checar a estrutura do arquivo**

```bash
cd /c/HENRIQUE/Claude/Arduino && python ferramentas/gerar-pagina.py
python -c "
import json,re
h=open('index.html',encoding='utf-8').read()
d=json.loads(re.search(r'id=\"dados\">(.*?)</script>',h,re.S).group(1).replace('<\\\\/','</'))
print('componentes no JSON:', len(d['componentes']))
print('familias:', sorted({c['familia'] for c in d['componentes']}))
print('marcas sobrando:', re.findall(r'\{\{\w+\}\}', h) or 'nenhuma')
"
```

Esperado: 85 componentes, as famílias povoadas, `marcas sobrando: nenhuma`.

- [ ] **Step 4: Commit**

```bash
git add ferramentas/modelo.html ferramentas/gerar-pagina.py index.html README.md
git commit -m "index.html: pagina de arquivo unico com busca e filtro por familia"
```

---

## Task 8: Verificação visual pelo Chrome DevTools Protocol

Conferir que a página renderiza de verdade, e não que ela *deveria* renderizar. Chrome
headless com `--window-size` mente sobre a largura no Windows; a única medida confiável é
dirigir o Chrome pelo DevTools Protocol e sobrescrever as métricas do dispositivo.

**Files:**
- Create: `ferramentas/previa.ps1`

- [ ] **Step 1: Escrever `ferramentas/previa.ps1`**

```powershell
# Captura o index.html pelo Chrome DevTools Protocol e reporta erros de console.
#
#   pwsh ferramentas/previa.ps1 -Largura 390 -Destino previa-390.png
#
# Nao usa --headless --screenshot: no Windows o --window-size nao vale para o
# viewport, e a captura sai com largura diferente da pedida. Emulation.
# setDeviceMetricsOverride vale.
param(
  [int]$Largura = 390,
  [int]$Altura = 900,
  [string]$Destino = "previa.png",
  [string]$Arquivo = "index.html"
)
$ErrorActionPreference = "Stop"

$raiz = Split-Path -Parent $PSScriptRoot
$alvo = "file:///" + ((Join-Path $raiz $Arquivo) -replace '\\', '/')
$perfil = Join-Path $env:TEMP ("cdp-" + [System.Guid]::NewGuid().ToString("N"))
$chrome = "C:\Program Files\Google\Chrome\Application\chrome.exe"
if (-not (Test-Path $chrome)) { throw "Chrome nao encontrado em $chrome" }

$porta = 9222
$proc = Start-Process $chrome -PassThru -ArgumentList @(
  "--remote-debugging-port=$porta", "--user-data-dir=$perfil",
  "--headless=new", "--disable-gpu", "--no-first-run", "--no-default-browser-check",
  "about:blank"
)

function Conectar($porta) {
  foreach ($i in 1..40) {
    try {
      $alvos = Invoke-RestMethod "http://127.0.0.1:$porta/json" -TimeoutSec 2
      $pagina = $alvos | Where-Object { $_.type -eq "page" } | Select-Object -First 1
      if ($pagina) { return $pagina.webSocketDebuggerUrl }
    } catch { }
    Start-Sleep -Milliseconds 250
  }
  throw "o Chrome nao abriu a porta de depuracao $porta"
}

$ws = New-Object System.Net.WebSockets.ClientWebSocket
$ws.ConnectAsync([Uri](Conectar $porta), [Threading.CancellationToken]::None).Wait()

$script:seq = 0
function Enviar($metodo, $params) {
  $script:seq++
  $corpo = @{ id = $script:seq; method = $metodo; params = $params } | ConvertTo-Json -Depth 10 -Compress
  $bytes = [Text.Encoding]::UTF8.GetBytes($corpo)
  $ws.SendAsync([ArraySegment[byte]]::new($bytes), 'Text', $true,
                [Threading.CancellationToken]::None).Wait()
  # Le ate chegar a resposta com o id pedido; eventos vem no meio e sao guardados.
  while ($true) {
    $buf = [ArraySegment[byte]]::new((New-Object byte[] 262144))
    $texto = ""
    do {
      $r = $ws.ReceiveAsync($buf, [Threading.CancellationToken]::None).GetAwaiter().GetResult()
      $texto += [Text.Encoding]::UTF8.GetString($buf.Array, 0, $r.Count)
    } while (-not $r.EndOfMessage)
    $msg = $texto | ConvertFrom-Json
    if ($msg.id -eq $script:seq) { return $msg.result }
    if ($msg.method -eq "Runtime.consoleAPICalled" -and $msg.params.type -eq "error") {
      $script:erros += ($msg.params.args | ForEach-Object { $_.value }) -join " "
    }
    if ($msg.method -eq "Runtime.exceptionThrown") {
      $script:erros += $msg.params.exceptionDetails.text
    }
  }
}

$script:erros = @()
Enviar "Runtime.enable" @{} | Out-Null
Enviar "Page.enable" @{} | Out-Null
Enviar "Emulation.setDeviceMetricsOverride" @{
  width = $Largura; height = $Altura; deviceScaleFactor = 2; mobile = ($Largura -lt 700)
} | Out-Null
Enviar "Page.navigate" @{ url = $alvo } | Out-Null
Start-Sleep -Milliseconds 1200

$medida = Enviar "Runtime.evaluate" @{
  expression = "JSON.stringify({larg: innerWidth, rolagem: document.documentElement.scrollWidth, pecas: document.querySelectorAll('.peca').length})"
  returnByValue = $true
}
$m = $medida.result.value | ConvertFrom-Json

$tiro = Enviar "Page.captureScreenshot" @{ format = "png"; captureBeyondViewport = $true }
$destAbs = if ([IO.Path]::IsPathRooted($Destino)) { $Destino } else { Join-Path (Get-Location) $Destino }
[IO.File]::WriteAllBytes($destAbs, [Convert]::FromBase64String($tiro.data))

Write-Output "viewport: $($m.larg) px | scrollWidth: $($m.rolagem) px | cartoes: $($m.pecas)"
if ($m.rolagem -gt $m.larg) { Write-Output "FALHA: a pagina estoura horizontalmente" }
if ($script:erros.Count) { Write-Output "FALHA: $($script:erros.Count) erro(s) de console:"; $script:erros | ForEach-Object { Write-Output "  $_" } }
else { Write-Output "console limpo" }
Write-Output "$destAbs gerado"

$ws.Dispose()
Stop-Process -Id $proc.Id -Force
Remove-Item $perfil -Recurse -Force -ErrorAction SilentlyContinue
```

- [ ] **Step 2: Capturar no celular (390 px)**

```bash
cd /c/HENRIQUE/Claude/Arduino && pwsh ferramentas/previa.ps1 -Largura 390 -Altura 900 -Destino previa-390.png
```

Esperado: `viewport: 390 px`, `scrollWidth: 390 px`, `cartoes: 85`, `console limpo`, e
**nenhuma** linha começando com `FALHA`.

- [ ] **Step 3: Capturar no desktop (1440 px)**

```bash
cd /c/HENRIQUE/Claude/Arduino && pwsh ferramentas/previa.ps1 -Largura 1440 -Altura 900 -Destino previa-1440.png
```

Esperado: o mesmo, com `viewport: 1440 px`.

- [ ] **Step 4: Olhar as duas imagens**

Abrir `previa-390.png` e `previa-1440.png`. Conferir: o nome do componente não é cortado, a
quantidade fica visível à direita, as etiquetas de campo quebram linha em vez de vazar, e a
barra de busca continua grudada no topo ao rolar.

**Mostrar as duas imagens ao Henrique antes de publicar.** Ele quer ver a renderização real,
não a garantia por escrito de que está certa.

- [ ] **Step 5: Ignorar as prévias e commitar o script**

```bash
cd /c/HENRIQUE/Claude/Arduino
printf '\n# previas de conferencia visual\nprevia-*.png\n' >> .gitignore
git add ferramentas/previa.ps1 .gitignore
git commit -m "previa.ps1: captura pelo CDP, que e a unica medida confiavel de largura"
```

---

## Task 9: `novo-projeto.py` e o modelo de projeto

**Files:**
- Create: `ferramentas/modelo/CLAUDE.md`, `ferramentas/modelo/README.md`, `ferramentas/modelo/MONTAGEM.md`, `ferramentas/modelo/.gitignore.modelo`, `ferramentas/modelo/.gitattributes.modelo`
- Create: `ferramentas/novo-projeto.py`

Os dois arquivos de ponto vão com sufixo `.modelo` porque um `.gitignore` dentro de
`ferramentas/modelo/` valeria para a própria pasta e esconderia os arquivos do modelo.

- [ ] **Step 1: Criar os arquivos do modelo**

`ferramentas/modelo/CLAUDE.md`:

```markdown
# hw-{{NOME}} — {{TITULO}}

{{DESCRICAO}}

Este arquivo é o documento vivo do projeto. O `README.md` e o `MONTAGEM.md` explicam o
projeto para quem vai montar; aqui ficam as decisões, o estado e o que ainda não foi
verificado.

> Para este arquivo ser carregado automaticamente, abra a sessão **dentro desta pasta**.

---

## Estado em {{DATA}}

Nada montado ainda. O projeto acabou de nascer.

| Item | Situação |
|---|---|
| Sketch | não escrito |
| Montagem física | não feita |

---

## O que ainda não foi testado, e pode estar errado

Nada foi verificado ainda. Esta seção é a mais importante do arquivo: cada decisão tomada
por leitura de datasheet, e não por medição, entra aqui até ser comprovada no hardware.

---

## Componentes

Registrar em `projetos/backlog.yaml` do `hw-laboratorio`, no campo `precisa`, com os ids do
inventário. O que faltar aparece sozinho no README de lá.
```

`ferramentas/modelo/README.md`:

```markdown
# hw-{{NOME}} — {{TITULO}}

{{DESCRICAO}}

## Montagem

Ver [MONTAGEM.md](MONTAGEM.md).

## Licença

Uso livre.
```

`ferramentas/modelo/MONTAGEM.md`:

```markdown
# Montagem — hw-{{NOME}}

## Componentes

| Componente | Qtd |
|---|---|
| — | — |

## Ligações

| De | Para | Observação |
|---|---|---|
| — | — | — |

## Ordem de montagem

1. Montar com a placa desligada.
2. Conferir alimentação e terra antes de energizar.
3. Energizar e testar uma parte de cada vez.

## Problemas comuns

Preencher conforme aparecerem.
```

`ferramentas/modelo/.gitignore.modelo`:

```text
# saidas de compilacao do arduino-cli / IDE
build/
*.hex
*.elf

# sistema
Thumbs.db
desktop.ini
.DS_Store
```

`ferramentas/modelo/.gitattributes.modelo`:

```text
# Arquivos gerados por script saem sempre em LF. Sem isto, numa maquina com
# outra configuracao de core.autocrlf o arquivo inteiro apareceria alterado.
* text=auto eol=lf
*.png binary
```

- [ ] **Step 2: Escrever `ferramentas/novo-projeto.py`**

```python
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
    if len(argv) < 2:
        print("uso: python ferramentas/novo-projeto.py <nome-kebab> [\"Titulo\"]",
              file=sys.stderr)
        return 2

    nome = argv[0]
    titulo = argv[1] if len(argv) > 1 else nome.replace("-", " ").capitalize()
    if not PADRAO_NOME.match(nome):
        print(f"ERRO: '{nome}' precisa ser kebab-case, so [a-z0-9] e hifen", file=sys.stderr)
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

    (destino / nome).mkdir()  # pasta do sketch: o Arduino exige pasta com o nome do .ino

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
```

- [ ] **Step 3: Provar que funciona, e limpar**

```bash
cd /c/HENRIQUE/Claude/Arduino
python ferramentas/novo-projeto.py teste-descartavel "Projeto de teste"
ls -a teste-descartavel
grep 'teste-descartavel' .gitignore
git status --short   # a pasta NAO pode aparecer aqui
head -3 teste-descartavel/CLAUDE.md
```

Esperado: a pasta com `CLAUDE.md`, `README.md`, `MONTAGEM.md`, `.gitignore`,
`.gitattributes`, `.git/` e `teste-descartavel/`; a linha no `.gitignore` da raiz; **nada**
sobre `teste-descartavel/` no `git status` além da alteração do próprio `.gitignore`; e o
título já substituído no `CLAUDE.md`.

```bash
cd /c/HENRIQUE/Claude/Arduino
rm -rf teste-descartavel
git checkout .gitignore
```

- [ ] **Step 4: Commit**

```bash
git add ferramentas/modelo ferramentas/novo-projeto.py
git commit -m "novo-projeto.py: esqueleto do morse virou modelo, com o .gitignore da raiz"
```

---

## Task 10: `CLAUDE.md` da raiz e publicação

**Files:**
- Create: `CLAUDE.md`

- [ ] **Step 1: Escrever o `CLAUDE.md` da raiz**

```markdown
# hw-laboratorio — a bancada

Inventário de componentes, backlog de projetos e lista de compras. Os projetos ficam em
repositórios próprios com prefixo `hw-`, dentro desta pasta e ignorados por este git.

Repositório público em `https://github.com/henriquemattosesilva/hw-laboratorio`,
página em `https://henriquemattosesilva.github.io/hw-laboratorio/`.

Este arquivo é o documento vivo. O desenho está em
`docs/superpowers/specs/2026-08-31-hw-laboratorio-design.md`.

---

## Regra que não pode ser esquecida: README.md e index.html são gerados

**Nunca editar `README.md` nem `index.html` à mão.** Os dois saem de
`python ferramentas/gerar-pagina.py`, a partir dos YAML. Editar direto significa perder a
alteração na próxima geração.

## Regra que não pode ser esquecida: projeto novo entra no .gitignore

Repositório dentro de repositório faz o git de fora gravar um *gitlink* — um ponteiro para
um commit — que parece funcionar e some com o conteúdo. Por isso `novo-projeto.py`
acrescenta a pasta ao `.gitignore` sozinho. Ao criar projeto sem o script, fazer isso à mão.

## Como as três bases se ligam

O `id` é a cola. O mesmo `id` vale em `compras/desejos.yaml` e depois em `componentes/`,
o que permite um projeto pedir peça que ainda não chegou. Os cruzamentos aparecem no topo
do README e da página:

- **o que falta por projeto** — inclui quantidade insuficiente, não só peça ausente;
- **id desconhecido** — quase sempre erro de digitação;
- **estoque insuficiente** — dois projetos reservando a mesma peça;
- **compra órfã** — item no carrinho que nenhum projeto pede.

Reserva estoque todo status menos `ideia`. Projeto `montado` ou `publicado` continua
ocupando as peças: publicar diz respeito ao repositório, não ao hardware.

## Comandos

```
python -m pip install -r requisitos.txt   # PyYAML e pytest
python -m pytest                          # 18 testes
python ferramentas/gerar-pagina.py        # sempre, depois de mexer em qualquer YAML
python ferramentas/novo-projeto.py nome "Título"
pwsh ferramentas/previa.ps1 -Largura 390 -Destino previa-390.png
```

## Impressão 3D

A impressora é do irmão do Henrique, uma Bambu Lab — ele disse "X2D", que não existe na
linha; provavelmente **H2D**. **Confirmar olhando na máquina.** Ele pretende comprar uma
**A1 mini**, cuja mesa é 180 × 180 × 180 mm — e esse é o teto de qualquer peça desenhada
aqui, para que nada deixe de imprimir na impressora futura.

Cada impressão custa pedir um favor, então as peças são desenhadas para acertar de primeira.
A pasta `cases/` ainda não existe: ela depende de OpenSCAD instalado e da peça de calibração
de folga impressa. Plano próprio.

## O que ainda não foi verificado

**Se o cruzamento de estoque vai ser usado.** É a aposta central do desenho. Se depois de
três projetos ninguém tiver olhado para o "o que falta", o gerador deve encolher para só
listar componentes — e aí o CSV do Notion teria bastado.

**Os campos ricos do inventário.** Tensão, interface, endereço e biblioteca foram
preenchidos por leitura de datasheet e memória, não por medição na bancada. O campo `notas`
é onde estão as afirmações mais úteis e também as mais fáceis de estarem erradas.

**O `arduino-cli` não está no PATH.** Só existe `~/.arduinoIDE/`. Resolver no primeiro
projeto que precisar compilar.
```

- [ ] **Step 2: Rodar a bateria inteira antes de publicar**

```bash
cd /c/HENRIQUE/Claude/Arduino
python -m pytest && python ferramentas/gerar-pagina.py && git status --short
```

Esperado: `18 passed`, a geração sem aviso, e nenhuma alteração pendente além do `CLAUDE.md`.

- [ ] **Step 3: Commit**

```bash
git add CLAUDE.md
git commit -m "CLAUDE.md da raiz: as duas regras que quebram tudo e o que nao foi verificado"
```

- [ ] **Step 4: Publicar**

```bash
cd /c/HENRIQUE/Claude/Arduino
gh repo create henriquemattosesilva/hw-laboratorio --public --source=. --remote=origin --push
gh api -X POST repos/henriquemattosesilva/hw-laboratorio/pages \
  -f 'source[branch]=main' -f 'source[path]=/'
```

Esperado: o repositório criado, o push feito, e o Pages ativado. A página leva um ou dois
minutos para subir em `https://henriquemattosesilva.github.io/hw-laboratorio/`.

- [ ] **Step 5: Conferir o que subiu**

```bash
cd /c/HENRIQUE/Claude/Arduino
git ls-files | head -30
git ls-files | grep -c . 
gh repo view henriquemattosesilva/hw-laboratorio --json visibility,homepageUrl
```

Esperado: nenhum arquivo de `codigo-morse/` na lista, e `"visibility": "PUBLIC"`.

---

## Depois deste plano

O passo seguinte é o que o Henrique quer de verdade: **escolher as placas para comprar**.
Ele agora tem onde registrar — `projetos/backlog.yaml` recebe as ideias, `compras/desejos.yaml`
recebe os itens com o motivo apontando para elas, e o gerador acusa compra órfã e peça
faltando. A pesquisa preenche `referencias/placas.md` e `referencias/energia.md`.

O plano dos cases 3D vem depois disso, quando houver um projeto com forma definida para
caber numa caixa.
