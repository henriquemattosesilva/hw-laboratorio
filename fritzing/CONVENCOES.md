# O que o Fritzing cobra de uma peça

Tudo aqui foi lido em peças do core e nos verificadores do próprio programa, não de
memória. As fontes ficam em `~/AppData/Local/Programs/Fritzing/fritzing-parts/`:

- `scripts/checks/svg_checkers.py` — as regras de SVG, incluindo a lista de fontes;
- `scripts/checks/explain_errors.md` — cada erro do CI e como se conserta;
- `core/` e `svg/core/` — 1791 peças para conferir como algo é feito de verdade.

O `nova-peca.py` já nasce obedecendo a tudo isto. Este documento existe para quando for
preciso mexer à mão, e para não redescobrir na marra.

## Os três sistemas de coordenadas

**É o erro mais caro.** Errar aqui faz a peça sair com tamanho físico errado e não
encaixar no passo de 0,1 polegada — e nada acusa, o desenho parece certo.

| vista | unidade do viewBox | passo de 0,1" | 1 mm |
|---|---|---|---|
| breadboard, schematic, icon | 72 por polegada | 7,2 u | 2,834646 u |
| pcb | **1000 por polegada** | 100 u | 39,3701 u |

`width` e `height` sempre em polegada ou milímetro, no elemento `<svg>`. Sem unidade
física o Fritzing adivinha o DPI, e adivinha errado.

## Como o conector se escreve, em cada vista

O conector precisa **desenhar alguma coisa**. Elemento invisível funciona por acidente —
o Fritzing pinta o conector por cima — mas alguns parsers descartam o que não renderiza,
e nenhum editor de SVG mostra o que está fora de lugar.

**breadboard** — o anel do furo é o próprio conector:

```xml
<circle id="connector0pin" cx="9.836" cy="47.5" r="2.4" fill="#c9c9c9" stroke="none"/>
<circle cx="9.836" cy="47.5" r="1.15" fill="#3a3a3a"/>
```

**schematic** — retângulo de 0,7 u de altura fazendo as vezes da linha do pino. O pino
tem 14,4 u (0,2") e o terminal cai em múltiplo de 7,2 u, que é a grade do esquema:

```xml
<rect id="connector0pin" connectorName="DATA" x="0" y="28.45"
      width="14.4" height="0.7" fill="#787878" stroke="none"/>
```

**pcb** — furo THT com `copper0` aninhado dentro de `copper1`, para o mesmo id valer nas
duas camadas sem virar id duplicado. `r="27.5"` com traço 20 dá furo de 35 mil e anel de
75 mil, que é o padrão dos DIP do core:

```xml
<g id="copper1">
  <g id="copper0">
    <circle id="connector0pin" cx="136.6" cy="660" r="27.5"
            fill="none" stroke="rgb(255, 191, 0)" stroke-width="20"/>
  </g>
</g>
```

## Regras que reprovam a peça

**Nunca declarar `terminalId`.** É a causa mais comum de terminal invisível, o defeito
clássico de peça caseira. A 1.0.3 calcula o terminal sozinho quando ele não é declarado —
e calcula melhor. Aqui declarar é erro, e tem teste.

**Fonte só pode ser `Noto Sans`** (breadboard, esquema, ícone) **ou `OCR-Fritzing-mono`**
(serigrafia do PCB). Qualquer outra é erro, mesmo que renderize na sua máquina.

**Id único no SVG inteiro.** Ornamento não leva id nenhum: id só nos conectores e nas
camadas.

**Nenhuma propriedade com valor vazio.** O verificador reclama e o Inspector ignora.

**Pino repetido precisa de `<bus>`.** Dois pinos com o mesmo nome quase sempre são o mesmo
ponto na placa — foi o caso dos dois DATA do MX-05V. Sem o barramento declarado o Fritzing
os trata como independentes e acusa conexão faltando quando só um é usado.

## Decisões desta pasta

Não são exigência do Fritzing; são escolhas, e vale saber por quê antes de mudar.

**Furo de encaixe, sem pino saindo da placa.** O fio entra igual, a placa não invade o
espaço abaixo dela e o desenho fica mais limpo. É como o NodeMCU e o WeMos do core são
desenhados.

**Tipo elétrico `male`, mesmo com o desenho de furo.** Assim a peça continua encaixando na
protoboard, sentando por cima como qualquer placa de desenvolvimento. Trocar para `female`
deixaria o desenho igual e tiraria essa capacidade, sem ganhar nada: a ponta de fio do
Fritzing é macho e entra nos dois casos.

**Fronteira de módulo vai tracejada; fio vai em linha cheia.** Quando o esquemático
desenha o circuito interno, o contorno sólido do módulo fecha retângulo com os fios e o
desenho lê como caixa dentro de caixa. Tracejado é a convenção de sub-conjunto e desfaz a
confusão de graça.

**No esquema, VCC em cima, GND embaixo, sinal à esquerda, antena à direita** — e os
rótulos de VCC e GND **fora** da caixa, ao lado do próprio pino. Dentro eles disputam
espaço com o título e o desenho fica apertado. Enfileirar tudo de um lado só polui o
traçado de quem usa a peça.

**`moduleId` termina em `-hwlab`.** Marca a origem e evita colidir com peça de terceiro na
biblioteca. E **nunca muda** depois de publicado: trocar o id a cada correção encheria a
biblioteca de cópias, cada uma parecendo uma peça diferente.

## Rodar o verificador do próprio Fritzing

```text
PYTHONIOENCODING=utf-8 python \
  ~/AppData/Local/Programs/Fritzing/fritzing-parts/fzp_checker.py fritzing/pecas/*/*.fzpz
```

Ele descompacta o pacote e confere as SVGs de dentro: 52 verificações por peça, contra as
24 que roda num `.fzp` solto. Por isso vale apontar para o `.fzpz`, não para a pasta.

O `PYTHONIOENCODING` não é enfeite. Sem ele o script quebra ao imprimir o ✓ no console do
Windows, e a mensagem de erro que aparece é o *help* do programa, o que engana.

## O que nenhum verificador pega

Desenho torto, texto fora da placa, componente sobreposto, rótulo trocado. Para isso
existe a folha de contato — `python fritzing/ferramentas/previa.py` e olhar. Três defeitos
reais destas duas peças só apareceram assim.
