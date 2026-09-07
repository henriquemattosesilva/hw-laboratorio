# hw-laboratorio

Inventário de componentes, backlog de projetos e lista de compras da bancada.
Os projetos ficam em repositórios próprios, com prefixo `hw-`.

> **Este arquivo é gerado.** Edite os YAML em `componentes/`, `projetos/` e
> `compras/` e rode `python ferramentas/gerar-pagina.py`.

**86 componentes distintos, 992 peças no total.**

Página com busca: <https://henriquemattosesilva.github.io/hw-laboratorio/>

## Referências

- [Placas: o que serve para quê](referencias/placas.md)

## Projetos

| Projeto | Status | Falta |
| --- | --- | --- |
| Telégrafo sem fio em morse | especificado | nada |
| Radar de ultrassom | ideia | nada |
| Fechadura por cartão RFID | ideia | nada |
| Controle universal de infravermelho | ideia | nada |
| Jogo de reflexo | ideia | nada |
| Termômetro registrador da geladeira | ideia | `resistor-4k7` |
| Estação de clima da varanda | ideia | nada |
| Sensor de porta aberta | ideia | `xiao-esp32c3`, `reed-switch`, `lipo-500mah` |
| Tomada comandada por Wi-Fi | ideia | `esp32c3-supermini`, `conversor-nivel-8ch` |
| Chaveiro que se acha | ideia | `xiao-esp32c3`, `lipo-500mah` |
| Horta monitorada | ideia | `esp32c3-supermini`, `solo-capacitivo`, `lipo-1200mah`, `tp4056-usbc`, `resistor-4k7` |
| Relógio de mesa | ideia | `esp32c3-supermini`, `matriz-max7219-4`, `ds3231` |
| Nó Matter de teste | ideia | `esp32c6-supermini` |
| Tanque de esteiras por rádio | ideia | `esp32c3-supermini`, `motor-dc-reducao`, `driver-drv8833`, `chassi-esteira`, `joystick-2eixos`, `lipo-2s-1500mah`, `oled-096` |

## Lista de compras

| Item | Qtd | Prioridade | Status | Motivo |
| --- | --- | --- | --- | --- |
| Bateria LiPo 3,7 V 500 mAh com proteção | 2 | alta | pesquisando | sensor-porta, chaveiro-achador |
| Conversor de nível lógico bidirecional 8 canais | 2 | alta | pesquisando | tomada-wifi |
| Placa ESP32-C3 SuperMini USB-C | 3 | alta | pesquisando | tomada-wifi, horta-monitorada, relogio-mesa, tanque-rc |
| Reed switch com ímã (sensor magnético de porta) | 2 | alta | pesquisando | sensor-porta |
| Resistor 4,7 kΩ | 10 | alta | pesquisando | termometro-geladeira, horta-monitorada |
| Seeed Studio XIAO ESP32C3 | 2 | alta | pesquisando | sensor-porta, chaveiro-achador |
| Sensor de umidade do solo capacitivo v1.2 | 1 | alta | pesquisando | horta-monitorada |
| Bateria LiPo 2S 7,4 V 1500 mAh | 1 | baixa | pesquisando | tanque-rc |
| Chassi com esteiras para robô | 1 | baixa | pesquisando | tanque-rc |
| Driver de motor duplo DRV8833 (ou TB6612FNG) | 1 | baixa | pesquisando | tanque-rc |
| Motor DC com caixa de redução (TT ou N20 6V) | 2 | baixa | pesquisando | tanque-rc |
| Módulo Matriz de LED MAX7219 4 em 1 (32x8) | 1 | baixa | pesquisando | relogio-mesa |
| Módulo joystick analógico 2 eixos com botão | 1 | baixa | pesquisando | tanque-rc |
| Placa ESP32-C6 SuperMini USB-C | 1 | baixa | pesquisando | no-matter |
| Bateria LiPo 3,7 V 1200 mAh com proteção | 1 | media | pesquisando | horta-monitorada |
| Display OLED 0,96" I2C SSD1306 128x64 | 2 | media | pesquisando | tanque-rc |
| Módulo carregador TP4056 USB-C com proteção | 2 | media | pesquisando | horta-monitorada |
| Real Time Clock RTC DS3231 com compensação de temperatura | 1 | media | pesquisando | relogio-mesa |

## Componentes

### Placas

| Componente | Qtd | Tensão | Interface | Observação |
| --- | --- | --- | --- | --- |
| Arduino Nano V3.0 ATmega328 5V | 1 | 5 V lógico | mini-USB; 14 digitais (6 com PWM), 8 analógicas | Mesmo micro do Uno, no mesmo relógio, num terço do tamanho. |
| Arduino Uno R3 | 1 | 5 V lógico; alimentação 7–12 V no jack ou pela USB | USB-B; 14 digitais (6 com PWM), 6 analógicas | ATmega328P a 16 MHz: 32 KB de flash (menos o bootloader), 2 KB de RAM. |
| Módulo ESP8266 ESP-12E CH340G NodeMCU | 1 | 3,3 V nos pinos; alimentação pela micro-USB | Wi-Fi 2,4 GHz; sem Bluetooth | Os pinos NÃO são tolerantes a 5 V. Ligar direto num sensor de 5 V queima. |
| Placa ESP32-S3 N16R8 (ESP32-S3-WROOM-1, USB-C dupla) | 1 | 3,3 V nos pinos; 5 V no 5Vin ou por qualquer uma das duas USB-C | Wi-Fi 2,4 GHz e Bluetooth LE 5; 44 pinos em duas fileiras a 0,9 polegada | Xtensa LX7 de dois núcleos a 240 MHz, 16 MB de flash e 8 MB de PSRAM: é isso que o N16R8 quer dizer. |

### Sensores

| Componente | Qtd | Tensão | Interface | Observação |
| --- | --- | --- | --- | --- |
| Módulo Sensor de Luminosidade LDR | 1 | 3,3 V a 5 V | digital com limiar por trimpot; alguns trazem AO também | O módulo responde "está claro ou escuro?", não "quanto de luz?". |
| Módulo Sensor de Presença e Movimento PIR DYP-ME003 | 1 | 4,5 V a 20 V de alimentação; saída em 3,3 V | digital, nível alto enquanto detecta | Precisa de 30 a 60 s parado depois de energizar para calibrar o fundo. |
| Sensor de Chuva | 1 | 3,3 V a 5 V | analógico (AO) e digital com limiar por trimpot (DO) | Mesma armadilha do higrômetro: a placa coletora corrói energizada. |
| Sensor de Cor RGB TCS34725 com Filtro IR | 1 | 3,3 V no chip; o módulo costuma aceitar 5 V | I2C | A quantidade veio em branco no export do Notion; anotado 1 por suposição. |
| Sensor de Distância Ultrassônico HC-SR04 | 2 | 5 V | digital: pulso de 10 µs no trigger, largura do echo é a distância | O pino echo devolve 5 V. Ligar direto num ESP8266 ou ESP32 exige divisor. |
| Sensor de Frequência Cardíaca | 1 |  | analógico, provavelmente | O nome no Notion é genérico e não identifica o modelo. CONFERIR A SERIGRAFIA na plaquinha antes de planejar projeto com ele: se for um Pulse Sensor, é fotopletismografia analógica com biblioteca própria; se for MAX30102, é I2C e outra história inteira. |
| Sensor de Luminosidade LDR 5mm | 13 |  | analógico — é um resistor, precisa de divisor | Sozinho não mede nada: entra num divisor com um resistor fixo (10 kΩ é o valor comum) e o meio do divisor vai para a entrada analógica. |
| Sensor de Pressão e Temperatura BMP280 | 1 | 3,3 V no chip; o módulo com regulador aceita 5 V | I2C (também faz SPI) | Não mede umidade. O que mede é o BME280, fisicamente quase idêntico e com o mesmo endereço — comprar um pensando no outro é o erro clássico. |
| Sensor de Som Microfone KY-038 | 1 | 3,3 V a 5 V | analógico (AO) e digital com limiar por trimpot (DO) | Detecta que houve som acima de um limiar. Não reconhece nota, palavra nem frequência — para isso seria preciso amostrar o AO rápido e fazer FFT. |
| Sensor de Temperatura a Prova D’água DS18B20 | 2 | 3,0 V a 5,5 V | 1-Wire | Precisa de pull-up de 4,7 kΩ entre dados e VCC. Sem ele o sensor não responde, e o sintoma é leitura de -127. |
| Sensor de Temperatura LM35DZ | 1 | 4 V a 30 V | analógico, 10 mV por °C | Não mede abaixo de 0 °C sem circuito extra — 0 °C é 0 V, e não há como ir mais baixo com alimentação simples. |
| Sensor de Umidade do Solo Higrômetro | 1 | 3,3 V a 5 V | analógico (AO) e digital com limiar por trimpot (DO) | Sonda resistiva: ela corrói quando fica energizada dentro da terra, e em poucas semanas o valor sai errado. Alimentar por um pino de saída e ligar só no momento da leitura resolve boa parte disso. |
| Sensor de Umidade e Temperatura AM3202 DHT22 | 1 | 3,3 V a 5 V | 1 fio proprietário (não é o 1-Wire da Dallas) | Uma leitura a cada 2 s, no máximo. Ler mais rápido devolve o valor anterior sem avisar que é velho. |
| Sensor Touch Capacitivo TTP223B | 1 | 2,0 V a 5,5 V | digital | Funciona através de acrílico ou plástico fino, o que serve bem para case fechado sem furo de botão. |

### Displays

| Componente | Qtd | Tensão | Interface | Observação |
| --- | --- | --- | --- | --- |
| Display 7 Segmentos 1 Dígito Vermelho Cátodo Comum CD4511 | 2 | 5 V | 4 pinos via CD4511 (BCD), ou 7 pinos direto | O CD4511 traduz 4 bits em dígito, economizando três pinos por display. |
| Display LCD 16x2 | 1 | 5 V | paralelo HD44780; 6 pinos no modo de 4 bits | Precisa de um potenciômetro de 10 kΩ no pino V0 para o contraste. Sem ele a tela fica toda preta ou toda apagada, e parece defeito. |
| Display LCD Nokia 5110 | 1 | 3,3 V — NÃO é tolerante a 5 V | SPI (PCD8544), 84 × 48 pixels | Ligar num Uno de 5 V sem divisor de tensão nos sinais mata o controlador. |
| Display LED Matriz de LED 8x8 Bicolor (Verde/Vermelho) | 1 |  | matriz crua de 24 pinos — sem driver | Esta é a matriz nua, sem MAX7219. Acender tudo ao mesmo tempo é impossível: precisa de multiplexação por software e de resistor em cada coluna. |
| Módulo Matriz de LED 8×8 com MAX7219 | 1 | 5 V | SPI | O MAX7219 faz a multiplexação sozinho: o micro só manda o que mostrar. |

### Atuadores

| Componente | Qtd | Tensão | Interface | Observação |
| --- | --- | --- | --- | --- |
| Diodo Laser 5mW 5V | 1 | 5 V | digital | O componente solto, sem plaquinha. Diodo laser precisa de corrente controlada — ligar direto na fonte queima. Usar com resistor limitador, ou preferir o módulo. |
| Micro Servo 9g SG90 | 2 | 4,8 V a 6 V | PWM de 50 Hz; pulso de 1 a 2 ms define o ângulo | O pico de corrente ao começar a girar derruba o 5 V da USB e reinicia a placa. Com dois servos isso é praticamente certo: fonte separada, terra em comum com o Arduino. |
| Módulo Buzzer Ativo P15 | 1 | 3,3 V a 5 V | digital — nível liga, não precisa de tone() | Ativo quer dizer que o oscilador está dentro: toca uma nota só, e o código apenas liga e desliga. Para tocar melodia seria preciso um passivo, que não temos. |
| Módulo Diodo Laser 5mW 5V 650nm 6mm | 1 | 5 V | digital | Já vem com o resistor limitador na plaquinha: é ligar e acender. |
| Módulo Relé 5V 1 canal | 2 | bobina de 5 V; entrada de sinal aceita 3,3 V na maioria | digital — quase sempre acionado em nível BAIXO | A maioria destes módulos liga com LOW e desliga com HIGH. O sintoma de ter assumido errado é o relé fechar sozinho ao ligar a placa, antes de o código rodar. |
| Módulo Relé 5V 2 canais | 1 | bobina de 5 V | dois pinos digitais — quase sempre acionados em nível BAIXO | Duas bobinas ligadas ao mesmo tempo puxam mais do que a USB do Arduino entrega com folga. Alimentar o módulo por fora e usar o jumper de separação, quando ele existe. |

### Comunicação

| Componente | Qtd | Tensão | Interface | Observação |
| --- | --- | --- | --- | --- |
| Cartão RFID Programável Mifare 13,56MHz | 8 |  | 13,56 MHz Mifare Classic 1K | 1 KB dividido em 16 setores. Cada setor tem duas chaves; a de fábrica é FF FF FF FF FF FF. |
| Controle Remoto Infravermelho 38KHz | 1 |  | infravermelho 38 kHz, protocolo NEC na maioria | Cada tecla manda um código de 32 bits. O jeito de descobrir é rodar o exemplo de dump da IRremote e anotar o que sai — não existe tabela confiável para os controles genéricos. |
| Módulo Emissor Infravermelho | 1 | 3,3 V a 5 V | digital, modulado em 38 kHz por software | O LED emite; quem gera os 38 kHz é a biblioteca, chaveando o pino. |
| Módulo Leitor Rfid MFRC522 Mifare 13,56MHz | 1 | 3,3 V — os pinos não são para 5 V | SPI | Lê 13,56 MHz (Mifare). NÃO lê tag de 125 kHz, que é a de portaria e crachá antigo, e é fisicamente parecida. |
| Módulo Receptor Infravermelho KY-022 38KHz | 1 | 3,3 V a 5 V | digital, saída ativa em nível BAIXO | É o mesmo receptor do VS1838B já numa plaquinha com os pinos marcados, o que evita o risco de inverter a alimentação. |
| Módulo Receptor Rádio Frequência 433MHz AM | 1 | 5 V | digital, um pino de dados | Os receptores baratos são superregenerativos: pegam ruído o tempo todo e o alcance decepciona. O superheteródino custa pouco mais e é outro mundo. |
| Módulo Transmissor Rádio Frequência 433MHz AM | 1 | 3 V a 12 V — quanto mais tensão, mais alcance | digital, um pino de dados (ASK/OOK) | Sem antena o alcance é de centímetros. Um fio reto de 17,3 cm é um quarto de onda em 433,92 MHz e resolve, sem custo. |
| Receptor Infravermelho VS1838B 38Khz | 1 | 2,7 V a 5,5 V | digital, saída ativa em nível BAIXO | Em repouso a saída fica em nível alto e cai quando chega portadora. Quem espera o contrário acha que está quebrado. |
| Sensor de Obstáculo Infravermelho | 2 | 3,3 V a 5 V | digital, nível BAIXO quando detecta | Emissor e receptor no mesmo módulo: mede reflexão, não distância. A distância de disparo é ajustada no trimpot, de 2 a 30 cm. |
| Tag Chaveiro RFID Programável Mifare 13,56MHz | 1 |  | 13,56 MHz Mifare Classic 1K | Mesma coisa do cartão, em formato de chaveiro. |

### Passivos

| Componente | Qtd | Tensão | Interface | Observação |
| --- | --- | --- | --- | --- |
| Chave SS 2 Posições SK22G50 | 3 |  |  |  |
| Chave Táctil | 19 |  |  |  |
| Chave Táctil Emborrachada | 4 |  |  |  |
| Chave Táctil Vermelha | 10 |  |  |  |
| LED Amarelo 5mm Cristalino | 10 |  |  |  |
| LED Amarelo 5mm Difuso | 9 |  |  |  |
| LED Azul 5mm Cristalino | 10 |  |  |  |
| LED Azul 5mm Difuso | 10 |  |  |  |
| LED Branco 5mm Cristalino | 10 |  |  |  |
| LED Branco 5mm Difuso | 10 |  |  |  |
| LED Laranja 5mm Cristalino | 10 |  |  |  |
| LED RGB 5mm Difuso | 2 |  |  |  |
| LED Rosa 5mm Cristalino | 10 |  |  |  |
| LED Ultra Violeta 5mm Cristalino | 10 |  |  |  |
| LED Verde 5mm Cristalino | 10 |  |  |  |
| LED Verde 5mm Difuso | 10 |  |  |  |
| LED Vermelho 5mm Cristalino | 10 |  |  |  |
| LED Vermelho 5mm Difuso | 6 |  |  |  |
| Potenciômetro Linear 100K | 2 |  |  |  |
| Potenciômetro Linear 10K | 3 |  |  |  |
| Resistor 100KΩ | 20 |  |  |  |
| Resistor 100Ω | 100 |  |  |  |
| Resistor 10KΩ | 19 |  |  |  |
| Resistor 150Ω | 100 |  |  |  |
| Resistor 220Ω | 18 |  |  |  |
| Resistor 330Ω | 20 |  |  |  |
| Resistor 47Ω | 15 |  |  |  |
| Transistor C945 NPN | 10 |  |  |  |

### Prototipagem

| Componente | Qtd | Tensão | Interface | Observação |
| --- | --- | --- | --- | --- |
| Cabo USB 2.0 AM para BM 180cm | 1 |  |  |  |
| Cabo USB 2.0 AM para BM 50cm | 1 |  |  |  |
| Cabo USB Mini | 1 |  |  |  |
| Jumper fêmea fêmea 20cm | 50 |  |  |  |
| Jumper macho fêmea 21cm | 80 |  |  |  |
| Jumper macho macho 12cm | 31 |  |  |  |
| Jumper macho macho 16cm | 7 |  |  |  |
| Jumper macho macho 20cm | 4 |  |  |  |
| Jumper macho macho 22cm | 34 |  |  |  |
| Jumper macho macho 25cm | 4 |  |  |  |
| Knob Azul para Potenciômetro | 2 |  |  |  |
| Knob Laranja para Potenciômetro | 3 |  |  |  |
| Knob Verde para Potenciômetro | 3 |  |  |  |
| Pinos 180° macho macho | 104 |  |  |  |
| Pinos 90° macho macho | 128 |  |  |  |
| Protoboard 400 Pontos | 1 |  |  |  |
| Protoboard 830 Pontos | 2 |  |  |  |

### Diversos

| Componente | Qtd | Tensão | Interface | Observação |
| --- | --- | --- | --- | --- |
| Módulo Cartão SD | 1 | 5 V no módulo com regulador; o cartão em si é 3,3 V | SPI | Conferir se o módulo tem regulador e conversor de nível. Os que só têm soquete e nada mais precisam de 3,3 V em tudo, inclusive nos sinais. |
| Real Time Clock RTC DS1307 | 1 | 5 V — o DS1307 não funciona confiável em 3,3 V | I2C | Erra na casa de minutos por mês: o cristal não é compensado por temperatura. Para relógio que precisa acertar, o DS3231 é o substituto, e ele ainda funciona em 3,3 V. |
