# Peças Fritzing próprias

O Fritzing 1.0 não traz o transmissor FS1000A nem o receptor MX-05V de 433 MHz — nenhuma
das 1791 peças do core corresponde. Sem elas, qualquer projeto de rádio da bancada fica
com um retângulo genérico no lugar dos módulos.

Os `id` são os mesmos do inventário: `rf433-tx` e `rf433-rx` em
`componentes/comunicacao.yaml`.

## Instalar

Abrir o Fritzing e ir em **Arquivo > Abrir**, apontando para o `.fzpz`:

```text
fritzing/dist/RF433-TX-FS1000A.fzpz
fritzing/dist/RF433-RX-MX05V.fzpz
```

A peça entra no bin **Minhas Peças** e passa a viver em
`Documentos/Fritzing/parts/user`. As duas compartilham a mesma `family`, então o Inspector
oferece trocar transmissor por receptor na lista de variantes.

**Reimportar não atualiza sketch antigo.** O Fritzing guarda uma cópia da peça dentro do
`.fzz`. Corrigido um desenho, o sketch já salvo continua com o desenho velho — é preciso
apagar a peça do sketch e colocar de novo.

## Regerar depois de mexer num SVG

```text
python fritzing/empacotar.py     # reescreve os dois .fzpz em fritzing/dist/
python -m pytest                 # entre eles, o teste que pega .fzpz velho
```

Esquecer de reempacotar deixa o `dist/` desatualizado em silêncio, com o desenho antigo
dentro do zip. Existe teste para isso justamente porque aconteceu.

## Pinagem

| peça | vista de cima, esquerda → direita |
|---|---|
| TX FS1000A | DATA · VCC · GND |
| RX MX-05V | **VCC · DATA · DATA · GND** |

A serigrafia do receptor fica **no verso**, onde se lê GND · DATA · DATA · VCC. Ler o
verso sem espelhar troca alimentação com terra. A vista breadboard do Fritzing desenha a
peça vista de cima, então é a coluna da direita que vale — e ela tem teste.

Os dois DATA do receptor são o mesmo ponto na placa e estão declarados como `<bus>` no
FZP. Sem isso o Fritzing acusaria conexão faltando ao usar só um deles.

Cada peça tem ainda um conector `ANT`, o furo da antena. Um fio reto de 17,3 cm é um
quarto de onda em 433,92 MHz; sem antena o alcance é de centímetros.

## Como está montado

```text
validar.py     confere a peça por leitura: SVG citada que não existe, conector sem
               elemento, passo fora da grade de 0,1", fonte proibida, id repetido,
               propriedade vazia, barramento órfão, terminalId declarado à mão
empacotar.py   zipa no .fzpz; roda o validador antes e se recusa a gerar peça quebrada
previa.html    folha de contato das oito SVGs, para conferir o desenho a olho
```

Conferência visual:

```text
pwsh ferramentas/previa.ps1 -Arquivo fritzing/previa.html -Largura 1100 -Altura 1400 \
     -Destino previa-fritzing.png -Inteira
```

E o conferidor do próprio Fritzing, que descompacta o pacote e checa as SVGs de dentro:

```text
PYTHONIOENCODING=utf-8 python \
  ~/AppData/Local/Programs/Fritzing/fritzing-parts/fzp_checker.py fritzing/dist/*.fzpz
```

O `PYTHONIOENCODING` não é enfeite: sem ele o script quebra ao imprimir o ✓ no console
do Windows.

## Sistemas de coordenadas

Cada vista tem o seu, copiado de peças do core. Errar isto faz a peça sair com tamanho
físico errado e não encaixar no passo de 0,1 polegada.

| vista | unidade do viewBox | passo de 0,1" | 1 mm |
|---|---|---|---|
| breadboard, schematic, icon | 72 por polegada | 7,2 u | 2,834646 u |
| pcb | 1000 por polegada | 100 u | 39,3701 u |

`width` e `height` sempre em polegadas. Sem isso o Fritzing adivinha o DPI.

## O que não foi conferido

**A posição da barra de pinos ao longo da borda**, nas duas peças, e a orientação do
desenho do receptor. Saiu de foto de catálogo, não da placa. Não afeta a ligação: se
estiver espelhado, o conserto é no ornamento, e a ordem dos pinos não muda.

**O encaixe no passo de 0,1" dentro do Fritzing.** O teste confere o passo no SVG, mas
quem confirma que a peça senta na protoboard é o programa aberto.

**A cota de 19 × 19 mm do transmissor** veio do anúncio, não de paquímetro. Só importa na
vista de PCB.
