# Peças Fritzing próprias

O Fritzing 1.0 não traz o transmissor FS1000A nem o receptor MX-05V de 433 MHz — nenhuma
das 1791 peças do core corresponde. Sem elas, qualquer projeto de rádio da bancada fica
com um retângulo genérico no lugar dos módulos.

Os `id` são os mesmos do inventário: `rf433-tx` e `rf433-rx` em
`componentes/comunicacao.yaml`.

## Instalar, na primeira vez

Abrir o Fritzing e ir em **Arquivo > Abrir**, apontando para o `.fzpz`:

```text
fritzing/dist/RF433-TX-FS1000A.fzpz
fritzing/dist/RF433-RX-MX05V.fzpz
```

A peça entra no bin **Minhas Peças** e passa a viver em
`Documentos/Fritzing/parts/user`. As duas compartilham a mesma `family`, então o Inspector
oferece trocar transmissor por receptor na lista de variantes.

## Atualizar, da segunda vez em diante

Reimportar o `.fzpz` faz o Fritzing reclamar:

```text
Part module ID must be unique.
Part load error
```

**O erro engana.** Ele acontece ao registrar o `moduleId`, que já está carregado na
memória — mas nesse ponto os arquivos novos **já foram copiados para o disco**. Fechar e
reabrir o Fritzing basta: ao iniciar ele relê a biblioteca e a peça aparece atualizada.
Verificado em 06/09/2026, comparando os arquivos instalados com os fontes.

Manter o mesmo `moduleId` é proposital: trocá-lo a cada correção encheria a biblioteca de
cópias, cada uma parecendo uma peça diferente.

O caminho limpo, sem caixa de erro e sem depender desse efeito colateral:

```text
# feche o Fritzing antes — ele lê a biblioteca ao iniciar
python fritzing/instalar.py
```

O script copia o FZP para `parts/user/<moduleid>.fzp` e as SVGs para
`parts/svg/user/<vista>/`, valida antes de copiar e se recusa a rodar com o programa
aberto. Nos dois caminhos o Fritzing precisa ser reiniciado.

**Nem isso atualiza sketch já salvo.** O Fritzing guarda uma cópia da peça dentro do
`.fzz`. No sketch antigo é preciso apagar a peça e colocar de novo.

## Regerar depois de mexer num SVG

```text
python fritzing/empacotar.py     # reescreve os dois .fzpz em fritzing/dist/
python fritzing/instalar.py      # atualiza a biblioteca do Fritzing
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

O desenho mostra **furos de encaixe, sem pino saindo da placa** — é como o NodeMCU e o
WeMos do core são desenhados, e é como o fio realmente entra. O tipo elétrico continua
`male`, então a peça também continua encaixando na protoboard se você quiser: ela senta
por cima, como qualquer placa de desenvolvimento.

Cada peça tem ainda um conector `ANT`, o furo da antena. Um fio reto de 17,3 cm é um
quarto de onda em 433,92 MHz; sem antena o alcance é de centímetros.

## Como está montado

```text
instalar.py    copia as peças para a biblioteca do Fritzing; é como se atualiza
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

**A posição da fileira de furos ao longo da borda**, nas duas peças, e a orientação do
desenho do receptor. Saiu de foto de catálogo, não da placa. Não afeta a ligação: se
estiver espelhado, o conserto é no ornamento, e a ordem dos pinos não muda.

**O encaixe no passo de 0,1" dentro do Fritzing.** O teste confere o passo no SVG, mas
quem confirma que a peça senta na protoboard é o programa aberto.

**A cota de 19 × 19 mm do transmissor** veio do anúncio, não de paquímetro. Só importa na
vista de PCB.
