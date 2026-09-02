# Placas: o que serve para quê

Levantamento feito em **02/09/2026** para decidir um padrão de placa nova. O que motivou:
as três placas atuais têm três conectores USB diferentes, nenhuma tem Bluetooth, e não há
placa sobrando — cada projeto novo obriga a desmontar um antigo.

> Preços conferidos em 02/09/2026. Preço envelhece; o raciocínio, não.

---

## A resposta curta

**O padrão é o ESP32-C3.** RISC-V a 160 MHz, 400 KB de RAM, 4 MB de flash, Wi-Fi e
Bluetooth 5 LE, USB-C. Substitui o ESP8266 em tudo e o Nano na maioria dos casos.

Mas a resposta real para *"não desmontar projeto"* não é qual placa: **é quantas.** A placa
custa entre R$ 35 e R$ 48. Sai mais barato deixar montada e esquecer do que desmontar.

## As duas variantes, e a diferença que decide

| | **ESP32-C3 SuperMini** | **XIAO ESP32C3** (Seeed) |
|---|---|---|
| Preço | R$ 34,60 – 47,70 | R$ 90 – 130 |
| Tamanho | 22 × 18 mm | 21 × 17,5 mm |
| USB | C | C |
| Carga de LiPo na placa | **não** | **sim**, 380 mA rápida / 40 mA gotejante |
| Antena | cerâmica, alcance fraco | conector u.FL + antena externa **na caixa** |
| Deep sleep | prejudicado pelo LED de energia sempre aceso | **44 µA** |
| I/O | ~13 | 11 digitais, 4 delas ADC |
| Estoque no Brasil | em oito lojas | faltando nas duas que consultei |

**SuperMini para o que fica na tomada. XIAO para o que roda em bateria.** Num nó
alimentado pela parede, o XIAO cobra três vezes mais por um circuito de carga que nunca
será usado.

### O XIAO funciona nos dois, e chaveia sozinho

Com o USB-C ligado ele alimenta a placa **e** carrega a bateria ao mesmo tempo. Tirando o
cabo, a bateria assume sem reset.

### O defeito do XIAO que ninguém conta

**Ele não sabe dizer quanto resta de bateria.** A Seeed não reservou canal de ADC para os
pads de bateria: o ESP32-C3 tem poucos pinos, e eles preferiram manter o mesmo número de
GPIOs do resto da família XIAO. É irônico — a placa que existe para rodar em bateria não
mede a própria bateria.

O conserto é barato e **não precisa comprar nada**: dois resistores de 100 kΩ, que já
existem no inventário (`resistor-100k`, 20 unidades), formam um divisor por dois entre o
positivo da bateria e o A0. Ler com `analogReadMilliVolts()`, que aplica a calibração
gravada de fábrica em cada chip — sem isso o fundo de escala varia ±10% de peça para peça.

A Seeed sugere 200 kΩ para consumir menos; com 100 kΩ o divisor puxa uns 18 µA
permanentes, que é da mesma ordem do deep sleep e portanto **corta a autonomia
praticamente pela metade**. Para o `sensor-porta`, que deve durar meses, vale comprar
200 kΩ ou pôr um transistor cortando o divisor quando não estiver medindo.

## Onde as três placas atuais ainda ganham

Isto não é nostalgia: são casos concretos em que trocar pelo ESP32 piora o projeto.

### Arduino Uno R3

**5 V nativo.** Boa parte do inventário atual é de 5 V e não conversa direto com 3,3 V: o
`hc-sr04` devolve 5 V no pino echo, e o `lcd-16x2`, o `matriz-max7219`, o `rtc-ds1307`, o
`display-7seg` e os relés são todos de 5 V. No Uno liga direto. No ESP32, cada um desses
precisa de divisor ou de conversor de nível — daí os dois conversores de 8 canais na lista
de compras serem item de prioridade alta.

**ADC honesto.** O conversor analógico do ESP32-C3 é não-linear nas pontas e precisa de
calibração. O do ATmega é linear e tem referência interna de 1,1 V, o que faz o `lm35` e o
`ldr-5mm` medirem melhor. Para medida analógica que importa, o Uno é a placa certa.

**Tinkercad.** O simulador só tem Arduino — nenhum ESP32, de nenhuma família. Quem quer
prototipar sem hardware na mão, como foi feito no `hw-codigo-morse`, não tem substituto.

E ele perdoa erro de fiação. Uno queimado é raro; ESP32 com 5 V num pino morre na hora.

### Arduino Nano

Ganha pelos mesmos 5 V e pelo mesmo Tinkercad. Fora isso perde em tudo: o C3 SuperMini tem
22 × 18 mm contra 45 × 18 mm do Nano, custa parecido e tem Wi-Fi e Bluetooth.

### ESP8266 NodeMCU

Sinceramente, em quase nada. Sem Bluetooth, um único pino analógico, micro-USB, e os mesmos
3,3 V do C3. O C3 faz tudo que ele faz e mais, por preço parecido.

Ele continua útil como **reserva** e como a placa do `estacao-varanda`, que não precisa de
Bluetooth nem de bateria — usar o que já está pago é melhor que comprar.

## O que não comprar agora

**ESP32-S3.** Ganha em câmera, áudio, USB nativo e mais RAM. Não há projeto no backlog que
peça isso. Quando houver — reconhecimento de imagem, gravação de som — ele entra.

**Placas com ESP32 clássico (dual core, Xtensa).** Maiores, mais caras, quase sempre
micro-USB, e a vantagem de dois núcleos não aparece em nenhum projeto do backlog.

## A aposta de futuro: ESP32-C6

Mesmo formato SuperMini, ~R$ 59,90, e o que ele acrescenta é **Zigbee, Thread e Matter**
além de Wi-Fi 6. Matter é o padrão que faz um sensor aparecer sozinho no Home Assistant e
na Alexa, sem servidor no meio. Está no backlog como `no-matter`, com **uma** unidade, para
experimentar antes de apostar.

Vale conferir também o **XIAO ESP32C6**, que junta as duas coisas — carga de bateria e
Matter — num formato só. Se o preço no Brasil for próximo do XIAO C3, ele colapsa as duas
necessidades numa placa única e o padrão fica mais simples. **Não foi levantado ainda.**

## Recomendação de compra

**Não comprar cinco de nenhuma das duas de saída.** Nenhuma delas foi usada aqui ainda, e
comprar cinco de uma placa desconhecida é como se acaba com cinco da errada.

**Primeira compra: 2 XIAO + 3 SuperMini**, algo em torno de R$ 340. Monta-se um projeto em
cada e descobrem-se as duas coisas que só o uso responde: se a antena cerâmica da SuperMini
alcança o roteador de onde o sensor precisa ficar, e se o LED sempre aceso dela atrapalha
de verdade num projeto a bateria. **Depois** compra-se em volume da que ganhou.

Contra isso pesa um argumento legítimo: padronizar numa placa só tem valor real — um pinout
para decorar, um conjunto de manias, e qualquer projeto pode virar portátil depois sem
recomprar. Se essa simplicidade valer mais que o dinheiro, padronizar no XIAO é defensável.
Só é preciso saber que se está pagando pela uniformidade, não por desempenho.

## Infraestrutura que não entra na lista de compras

Cabo USB-C não é peça de projeto: nenhum projeto o "consome", então ele apareceria como
compra órfã no gerador. Fica registrado aqui — **comprar dois cabos USB-C de dados**, e
conferir que são de dados e não só de carga, porque cabo de carga não grava a placa e o
sintoma é a porta COM não aparecer.

---

## Fontes

- [Placa Super Mini ESP32-C3 — Curto Circuito](https://curtocircuito.com.br/placa-super-mini-esp32-c3.html) — R$ 34,60 promocional, esgotado em 02/09/2026
- [Placa Super Mini ESP32-C3 USB-C — RL Eletrônica](https://rleletronica.com.br/produto/placa-super-mini-esp32-c3-usb-c/) — R$ 47,70
- [Seeed Studio XIAO ESP32C3 — RoboCore](https://www.robocore.net/seeed-studio/seeed-studio-xiao-esp32c3)
- [XIAO ESP32C3 Getting Started — Seeed Studio Wiki](https://wiki.seeedstudio.com/XIAO_ESP32C3_Getting_Started/) — 380 mA de carga, 44 µA em deep sleep, 11 I/O
- [How to check the battery voltage — Seeed Studio Wiki](https://wiki.seeedstudio.com/check_battery_voltage/) — divisor externo, `analogReadMilliVolts()`
- [Placa ESP32-C6 Super Mini Zigbee — Smart Kits](https://www.smartkits.com.br/placa-esp32-c6-super-mini-zigbee) — R$ 59,90
- [ESP32-C6 Super Mini USB-C — Usinainfo](https://www.usinainfo.com.br/esp32/esp32-c6-super-mini-com-wifi-e-bluetooth-com-usb-c-9162.html)
