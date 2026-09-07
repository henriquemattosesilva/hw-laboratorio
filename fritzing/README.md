# Peças Fritzing próprias

O core do Fritzing 1.0 tem 1791 peças e mesmo assim falta módulo comum de bancada. Esta
pasta é onde as que faltam são feitas. Os `id` são os mesmos do inventário em
`componentes/`, para o nome valer nas duas bases.

```text
fritzing/
  CLAUDE.md          as regras que quebram o trabalho quando esquecidas
  CONVENCOES.md      o que o Fritzing cobra de uma peça, e as decisões desta pasta
  ferramentas/
    nova-peca.py     cria peça nova com a geometria já certa
    validar.py       confere a peça por leitura
    previa.py        gera a folha de contato das SVGs
    empacotar.py     gera os .fzpz
    instalar.py      copia para a biblioteca do Fritzing
    pecas.py         onde as peças moram; fonte única do layout
  pecas/             uma pasta por peça: os fontes e o .fzpz para importar
  previa.html        a folha de contato, gerada
```

As ferramentas **descobrem as peças sozinhas** — peça é pasta com `part.fzp` dentro. Não
existe lista para manter em lugar nenhum.

## Criar uma peça

```text
python fritzing/ferramentas/nova-peca.py hc-sr04 --mm 45x20 \
       --pinos VCC,TRIG,ECHO,GND --titulo "Sensor ultrassonico HC-SR04"
```

Sai uma peça completa e válida: as quatro vistas, os furos no passo de 0,1 polegada, o
viewBox na unidade certa de cada vista e o FZP com os conectores. Falta só o **ornamento**
— o desenho dos componentes da placa, que nenhum gerador tem como adivinhar. O SVG de
breadboard traz um comentário no lugar onde ele entra.

O gerador cuida justamente da parte que dá errado em silêncio: unidade do viewBox, passo
dos furos, ordem dos conectores, barramento. Ornamento errado se vê na prévia; passo
errado só aparece quando a peça não encaixa.

Os nomes em `--pinos` vão **da esquerda para a direita vista de cima**, que é como o
Fritzing desenha. Em placa cuja serigrafia fica no verso, é o inverso do que se lê nela —
foi o caso do MX-05V.

**Nome repetido vira barramento.** `--pinos VCC,DATA,DATA,GND` cria `DATA` e `DATA2` e os
declara ligados, porque nome repetido quer dizer o mesmo ponto na placa.

Outras opções:

| opção | para quê |
|---|---|
| `--lado baixo\|cima\|esquerda\|direita` | borda onde fica a fileira de furos. Nas bordas curtas ela corre na vertical, e aí `--pinos` vai de cima para baixo |
| `--alinhar inicio\|centro\|fim` | onde a fileira encosta na borda. Header longo costuma ser `inicio`; conector de dois pinos na ponta, `centro` |
| `--cor verde\|azul\|vermelha\|preta\|branca\|amarela` | cor da placa, com a borda e a tinta da serigrafia junto |
| `--familia` | peças da mesma família viram variantes uma da outra no Inspector |
| `--fileira LADO:NOMES` | uma fileira por vez, repetível. Placa de desenvolvimento tem duas: `--fileira cima:D0,D1 --fileira baixo:A0,G` |
| `--vao MM` | distância entre as duas fileiras, de centro a centro. **Precisa ser múltiplo de 2,54 mm**, e o gerador recusa se não for |
| `--ant` | acrescenta um conector de antena fora da fileira |

## Conferir

```text
python -m pytest                              # o validador e as peças reais
python fritzing/ferramentas/previa.py         # gera a folha de contato
pwsh ferramentas/previa.ps1 -Arquivo fritzing/previa.html -Largura 1400 \
     -Altura 1000 -Destino previa-fritzing.png -Inteira
```

**Olhar a imagem não é opcional.** Nenhum teste pega desenho torto, texto fora da placa ou
rótulo trocado, e três defeitos reais das peças de 433 MHz só apareceram assim.

E o verificador do próprio Fritzing, que descompacta o pacote e confere as SVGs de dentro:

```text
PYTHONIOENCODING=utf-8 python \
  ~/AppData/Local/Programs/Fritzing/fritzing-parts/fzp_checker.py fritzing/pecas/*/*.fzpz
```

## Publicar e instalar

```text
python fritzing/ferramentas/empacotar.py   # reescreve o .fzpz de cada peça
python fritzing/ferramentas/instalar.py    # copia para a biblioteca (Fritzing fechado)
```

**O `.fzpz` fica dentro da pasta da peça**, ao lado do `part.fzp` — é o arquivo que o
Fritzing importa. O `part.fzp` sozinho não serve: ele cita as SVGs por caminho relativo,
e quem junta tudo é o zip.

**Na primeira vez** dá para instalar pela interface: **Arquivo > Abrir** apontando para
`pecas/<peça>/<NOME>.fzpz`. A peça entra no bin *Minhas Peças*.

**Da segunda em diante** o Fritzing reclama:

```text
Part module ID must be unique.
Part load error
```

O erro engana. Ele acontece ao registrar o `moduleId`, que já está carregado na memória —
mas nesse ponto os arquivos novos **já foram copiados para o disco**. Fechar e reabrir o
Fritzing basta. O `instalar.py` faz a cópia direto, sem a caixa de erro e sem depender
desse efeito colateral; nos dois caminhos o programa precisa reiniciar para reler a
biblioteca.

**Nem isso atualiza sketch já salvo.** O Fritzing guarda uma cópia da peça dentro do
`.fzz`. No sketch antigo é preciso apagar a peça e colocar de novo.

## Depois de mexer numa SVG

```text
python fritzing/ferramentas/previa.py
python fritzing/ferramentas/empacotar.py
python fritzing/ferramentas/instalar.py
```

Esquecer de reempacotar deixa o `.fzpz` desatualizado em silêncio, com o desenho antigo
dentro do zip. Existe teste para isso justamente porque aconteceu.

## As peças de hoje

| pasta | peça | conectores, vista de cima |
|---|---|---|
| `rf433-tx` | Transmissor 433 MHz FS1000A (MX-FS-03V), 19 × 19 mm | DATA · VCC · GND · ANT |
| `rf433-rx` | Receptor 433 MHz MX-05V, 30 × 14 mm | VCC · DATA · DATA · GND · ANT |
| `buzzer-ativo` | Buzzer ativo GBK P15, 32 × 15 mm | GND · SINAL, na ponta esquerda |
| `nodemcu-lolin-v3` | NodeMCU ESP8266 LoLin v3, 59 × 31 mm | 15 + 15, fileiras a 1,1 pol |
| `esp32-s3-n16r8` | ESP32-S3-WROOM-1 N16R8, USB-C dupla, 57 × 28 mm | 22 + 22, fileiras a 0,9 pol |

O `nodemcu-lolin-v3` é a exceção à regra de o `id` ser o mesmo do inventário: lá a placa
está como `esp8266-nodemcu`, nome genérico que serve para qualquer NodeMCU. Aqui o id
precisa dizer a variante, porque a **Amica já existe no core do Fritzing** e as duas
diferem em dois pinos — na LoLin o terceiro pino de baixo é `VU`, os 5 V do USB; na Amica
é `RSV`, sem ligação nenhuma. Peça errada no desenho vira fio ligado em pino morto.

A serigrafia do receptor fica **no verso**, onde se lê GND · DATA · DATA · VCC. Ler o
verso sem espelhar troca alimentação com terra. As duas ordens têm teste.

## O que não foi conferido

**A posição da fileira de furos ao longo da borda**, nas duas peças de 433 MHz, e a
orientação do desenho do receptor. Saiu de foto de catálogo, não da placa. Não afeta a
ligação: se estiver espelhado, o conserto é no ornamento, e a ordem dos pinos não muda.

**O encaixe no passo de 0,1" dentro do Fritzing.** O teste confere o passo no SVG, mas
quem confirma que a peça senta na protoboard é o programa aberto.

**A cota de 19 × 19 mm do transmissor** veio do anúncio, não de paquímetro. Só importa na
vista de PCB.

**O vão de 0,9 polegada entre as fileiras da ESP32-S3.** Henrique mediu a placa, 57 × 28 mm,
mas não a distância entre as fileiras. 0,9 pol é o único múltiplo de 0,1" que cabe em 28 mm
com furo dentro da placa, e é o padrão da DevKitC-1 — mas é dedução, não régua. **Esta é a
cota que decide se a peça encaixa na protoboard**, e é a primeira coisa a conferir.

**O GPIO do LED RGB da ESP32-S3.** É o 48 na maioria destas placas e o 38 em algumas
DevKitC-1 v1.1. A serigrafia só diz RGB. Um blink resolve.

**A posição dos componentes miúdos da ESP32-S3** — regulador, capacitores, LED — saiu da
foto a olho. Módulo, botões, LED e as duas USB-C estão no lugar; o resto é aproximação.

**A ficha do vendedor da LoLin v3 dizia 49 × 25,5 mm**, que é de outra variante. As cotas
usadas — 59 × 31 mm, fileiras a 1,1 polegada — vieram da régua de Henrique. Com a ficha,
a peça teria saído com as fileiras a 0,9 polegada e não encaixaria.

**A polaridade de acionamento do buzzer.** Vários módulos P15 tocam com nível BAIXO, e a
deste não foi medida. Está registrado no inventário e na `description` da peça. Não muda o
desenho, muda o código de quem usar.

**As cotas do buzzer** vieram da ficha do fabricante, não de paquímetro.
