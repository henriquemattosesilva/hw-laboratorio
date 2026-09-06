# Peças Fritzing para os módulos RF 433 MHz — desenho

06/09/2026

O Fritzing 1.0 não traz o transmissor FS1000A nem o receptor MX-05V: nenhuma das 1791
peças do core corresponde, conferido por busca em `fritzing-parts/core`. Sem elas o
desenho de qualquer projeto de rádio da bancada fica com um retângulo genérico no lugar
dos módulos. Este documento desenha as duas peças.

Os dois módulos já estão no inventário como `rf433-tx` e `rf433-rx` em
`componentes/comunicacao.yaml`. As peças reaproveitam esses `id` como prefixo, para o
mesmo nome valer nas duas bases.

## Decisões

**Arte fiel à foto, não retângulo genérico.** Ressonador SAW, bobina de cobre, trimpot e
serigrafia desenhados. É o padrão das peças do core, e é o que faz reconhecer o módulo na
protoboard sem ler o rótulo.

**FZP e SVG escritos à mão, empacotados por script.** O editor de peças do Fritzing é uma
janela Qt que não se automatiza e que gera SVG com resíduo de Illustrator. Clonar peça
parecida do core herdaria `moduleId` e sujeira de outra peça. Texto puro versiona, revisa
em diff e valida no `fzp_checker.py` que já vem instalado com o Fritzing.

**Fontes em `Arduino/fritzing/`, dentro do hw-laboratorio.** Não são projeto de hardware,
são ferramenta de bancada — mesma categoria de `ferramentas/`. Repositório próprio com
prefixo `hw-` seria cerimônia demais para duas peças.

## Pinagem

Confirmada por Henrique na plaquinha, 06/09/2026. É o ponto de maior risco do desenho:
a serigrafia do receptor fica no verso, e ler o verso sem espelhar inverte alimentação
com terra.

| peça | vista de cima (esquerda → direita) | vista de baixo |
|---|---|---|
| TX FS1000A | DATA · VCC · GND | — serigrafia fica no lado dos componentes, sem espelhamento |
| RX MX-05V | VCC · DATA · DATA · GND | GND · DATA · DATA · VCC |

A vista breadboard do Fritzing desenha a peça vista de cima. É a coluna da esquerda que
vai para o SVG.

**Os dois DATA do receptor são um `<bus>` no FZP.** Estão ligados internamente na placa.
Sem o barramento declarado o Fritzing os trata como pinos independentes e acusa conexão
faltando quando só um é usado.

## Convenções que o Fritzing 1.0 cobre

Lidas em `fritzing-parts/scripts/checks/svg_checkers.py` e `explain_errors.md`, não de
memória.

- `viewBox` obrigatório, com `width` e `height` em polegadas. Sem viewBox o Fritzing
  adivinha o DPI e a peça sai com tamanho físico errado.
- Unidade do viewBox: ponto, 72 por polegada. 1 mm = 2,834646 u; o passo de 0,1" = 7,2 u.
- Fonte `Noto Sans` no breadboard, esquema e ícone; `OCR-Fritzing-mono` na serigrafia do
  PCB. Qualquer outra é erro.
- **Sem `terminalId` no FZP.** Terminal invisível é o erro mais comum de peça caseira, e
  a 1.0.3 calcula o terminal sozinho quando ele não é declarado.
- IDs únicos no SVG inteiro. No PCB, `copper0` aninhado dentro de `copper1` para o mesmo
  pad servir às duas camadas sem duplicar id.
- Nenhuma propriedade com valor vazio: o checker reclama e o Inspector ignora.

## As peças

### Transmissor — 19 × 19 mm, 3 pinos

Breadboard: placa verde, ressonador SAW prateado deitado, bobina de cobre, SOT-23,
passivos SMD, pad de antena com o pino `ANT`, serigrafia `FS1000A` e `DATA VCC GND`.
Barra de pinos macho na borda inferior, passo 2,54 mm.

### Receptor — 30 × 14 mm, 4 pinos

Breadboard: placa verde, SOIC-8, trimpot azul-claro, bobina de cobre, passivos SMD,
serigrafia `MX-05V`. Barra de pinos na borda inferior.

A posição da barra ao longo da borda — extremidade da bobina ou a oposta — sai das fotos,
que são de catálogo e de baixa resolução. Não afeta a ligação elétrica, só o desenho.
Fica para conferência visual contra a placa real; espelhar a arte depois é troca de um
sinal.

### Esquemático, as duas

Caixa com VCC em cima, GND embaixo, DATA à esquerda e símbolo de antena à direita. Três
ou quatro pinos enfileirados de um lado só polui o traçado de quem usa a peça.

### PCB, as duas

Furos THT no passo 0,1" e contorno de serigrafia no tamanho real, para a peça poder ir
para uma placa de verdade e não só para o desenho de protoboard.

## Estrutura

```
fritzing/
  README.md
  rf433-tx/  part.fzp + svg/{breadboard,schematic,pcb,icon}/*.svg
  rf433-rx/  idem
  empacotar.py     gera dist/*.fzpz — zip com prefixos svg.breadboard. etc.
  previa.html      folha de contato das oito SVGs
  dist/            RF433-TX-FS1000A.fzpz, RF433-RX-MX05V.fzpz
```

O `.fzpz` é um zip de arquivo plano: `part.<moduleid>.fzp` e
`svg.<vista>.<nome>.svg`. O `empacotar.py` reescreve os caminhos das imagens do FZP para
esse formato na hora de zipar, para a árvore de fontes poder ficar em pastas.

## Verificação

1. `python fzp_checker.py` do Fritzing sobre as duas peças, até zerar erro.
2. `previa.ps1 -Arquivo fritzing/previa.html` renderiza as oito SVGs numa folha de
   contato. Henrique olha o desenho antes de a peça ser dada por pronta.
3. Encaixe no passo de 0,1" só o Fritzing aberto confirma, e isso fica com Henrique: é
   aplicativo Qt, fora do alcance da conferência por CDP.

## O que não foi verificado

**A posição da barra de pinos ao longo da borda**, nas duas peças, e a orientação do
desenho do receptor. Vem de foto de catálogo.

**Se o desenho de PCB é usado alguma vez.** Entra porque uma peça sem PCB trava quem
quiser levar o projeto para placa, mas até hoje nenhum projeto da bancada saiu da
protoboard. Se em três projetos ninguém abrir a vista de PCB, futuras peças podem sair
sem ela.

**A cota de 19 × 19 mm do transmissor** veio do anúncio, não de paquímetro. O tamanho
físico só importa na vista de PCB.
