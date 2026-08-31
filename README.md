# hw-laboratorio

Inventário de componentes, backlog de projetos e lista de compras da bancada.
Os projetos ficam em repositórios próprios, com prefixo `hw-`.

> **Este arquivo é gerado.** Edite os YAML em `componentes/`, `projetos/` e
> `compras/` e rode `python ferramentas/gerar-pagina.py`.

**85 componentes distintos, 991 peças no total.**

## Componentes

### Placas

| Componente | Qtd | Tensão | Interface | Observação |
| --- | --- | --- | --- | --- |
| Arduino Nano V3.0 ATmega328 5V | 1 | 5 V lógico | mini-USB; 14 digitais (6 com PWM), 8 analógicas | Mesmo micro do Uno, no mesmo relógio, num terço do tamanho. |
| Arduino Uno R3 | 1 | 5 V lógico; alimentação 7–12 V no jack ou pela USB | USB-B; 14 digitais (6 com PWM), 6 analógicas | ATmega328P a 16 MHz: 32 KB de flash (menos o bootloader), 2 KB de RAM. |
| Módulo ESP8266 ESP-12E CH340G NodeMCU | 1 | 3,3 V nos pinos; alimentação pela micro-USB | Wi-Fi 2,4 GHz; sem Bluetooth | Os pinos NÃO são tolerantes a 5 V. Ligar direto num sensor de 5 V queima. |

### Sensores

| Componente | Qtd | Tensão | Interface | Observação |
| --- | --- | --- | --- | --- |
| Módulo Sensor de Luminosidade LDR | 1 | 3,3 V a 5 V | digital com limiar por trimpot; alguns trazem AO também | O módulo responde "está claro ou escuro?", não "quanto de luz?". |
| Módulo Sensor de Presença e Movimento PIR DYP-ME003 | 1 | 4,5 V a 20 V de alimentação; saída em 3,3 V | digital, nível alto enquanto detecta | Precisa de 30 a 60 s parado depois de energizar para calibrar o fundo. |
| Sensor de Chuva | 1 | 3,3 V a 5 V | analógico (AO) e digital com limiar por trimpot (DO) | Mesma armadilha do higrômetro: a placa coletora corrói energizada. |
| Sensor de Cor RGB TCS34725 com Filtro IR | 1 | 3,3 V no chip; o módulo costuma aceitar 5 V | I2C | A quantidade veio em branco no export do Notion; anotado 1 por suposição. |
| Sensor de Distância Ultrassônico HC-SR04 | 2 | 5 V | digital: pulso de 10 µs no trigger, largura do echo é a distância | O pino echo devolve 5 V. Ligar direto num ESP8266 ou ESP32 exige divisor. |
| Sensor de Frequência Cardíaca | 1 |  | analógico, provavelmente | O nome no Notion é genérico e não identifica o modelo. CONFERIR A |
| Sensor de Luminosidade LDR 5mm | 13 |  | analógico — é um resistor, precisa de divisor | Sozinho não mede nada: entra num divisor com um resistor fixo (10 kΩ é o |
| Sensor de Pressão e Temperatura BMP280 | 1 | 3,3 V no chip; o módulo com regulador aceita 5 V | I2C (também faz SPI) | Não mede umidade. O que mede é o BME280, fisicamente quase idêntico e com |
| Sensor de Som Microfone KY-038 | 1 | 3,3 V a 5 V | analógico (AO) e digital com limiar por trimpot (DO) | Detecta que houve som acima de um limiar. Não reconhece nota, palavra nem |
| Sensor de Temperatura a Prova D’água DS18B20 | 2 | 3,0 V a 5,5 V | 1-Wire | Precisa de pull-up de 4,7 kΩ entre dados e VCC. Sem ele o sensor não |
| Sensor de Temperatura LM35DZ | 1 | 4 V a 30 V | analógico, 10 mV por °C | Não mede abaixo de 0 °C sem circuito extra — 0 °C é 0 V, e não há como |
| Sensor de Umidade do Solo Higrômetro | 1 | 3,3 V a 5 V | analógico (AO) e digital com limiar por trimpot (DO) | Sonda resistiva: ela corrói quando fica energizada dentro da terra, e em |
| Sensor de Umidade e Temperatura AM3202 DHT22 | 1 | 3,3 V a 5 V | 1 fio proprietário (não é o 1-Wire da Dallas) | Uma leitura a cada 2 s, no máximo. Ler mais rápido devolve o valor anterior |
| Sensor Touch Capacitivo TTP223B | 1 | 2,0 V a 5,5 V | digital | Funciona através de acrílico ou plástico fino, o que serve bem para case |

### Displays

| Componente | Qtd | Tensão | Interface | Observação |
| --- | --- | --- | --- | --- |
| Display 7 Segmentos 1 Dígito Vermelho Cátodo Comum CD4511 | 2 | 5 V | 4 pinos via CD4511 (BCD), ou 7 pinos direto | O CD4511 traduz 4 bits em dígito, economizando três pinos por display. |
| Display LCD 16x2 | 1 | 5 V | paralelo HD44780; 6 pinos no modo de 4 bits | Precisa de um potenciômetro de 10 kΩ no pino V0 para o contraste. Sem ele |
| Display LCD Nokia 5110 | 1 | 3,3 V — NÃO é tolerante a 5 V | SPI (PCD8544), 84 × 48 pixels | Ligar num Uno de 5 V sem divisor de tensão nos sinais mata o controlador. |
| Display LED Matriz de LED 8x8 Bicolor (Verde/Vermelho) | 1 |  | matriz crua de 24 pinos — sem driver | Esta é a matriz nua, sem MAX7219. Acender tudo ao mesmo tempo é impossível: |
| Módulo Matriz de LED 8×8 com MAX7219 | 1 | 5 V | SPI | O MAX7219 faz a multiplexação sozinho: o micro só manda o que mostrar. |

### Atuadores

| Componente | Qtd | Tensão | Interface | Observação |
| --- | --- | --- | --- | --- |
| Diodo Laser 5mW 5V | 1 | 5 V | digital | O componente solto, sem plaquinha. Diodo laser precisa de corrente |
| Micro Servo 9g SG90 | 2 | 4,8 V a 6 V | PWM de 50 Hz; pulso de 1 a 2 ms define o ângulo | O pico de corrente ao começar a girar derruba o 5 V da USB e reinicia a |
| Módulo Buzzer Ativo P15 | 1 | 3,3 V a 5 V | digital — nível liga, não precisa de tone() | Ativo quer dizer que o oscilador está dentro: toca uma nota só, e o |
| Módulo Diodo Laser 5mW 5V 650nm 6mm | 1 | 5 V | digital | Já vem com o resistor limitador na plaquinha: é ligar e acender. |
| Módulo Relé 5V 1 canal | 2 | bobina de 5 V; entrada de sinal aceita 3,3 V na maioria | digital — quase sempre acionado em nível BAIXO | A maioria destes módulos liga com LOW e desliga com HIGH. O sintoma de |
| Módulo Relé 5V 2 canais | 1 | bobina de 5 V | dois pinos digitais — quase sempre acionados em nível BAIXO | Duas bobinas ligadas ao mesmo tempo puxam mais do que a USB do Arduino |

### Comunicação

| Componente | Qtd | Tensão | Interface | Observação |
| --- | --- | --- | --- | --- |
| Cartão RFID Programável Mifare 13,56MHz | 8 |  | 13,56 MHz Mifare Classic 1K | 1 KB dividido em 16 setores. Cada setor tem duas chaves; a de fábrica é |
| Controle Remoto Infravermelho 38KHz | 1 |  | infravermelho 38 kHz, protocolo NEC na maioria | Cada tecla manda um código de 32 bits. O jeito de descobrir é rodar o |
| Módulo Emissor Infravermelho | 1 | 3,3 V a 5 V | digital, modulado em 38 kHz por software | O LED emite; quem gera os 38 kHz é a biblioteca, chaveando o pino. |
| Módulo Leitor Rfid MFRC522 Mifare 13,56MHz | 1 | 3,3 V — os pinos não são para 5 V | SPI | Lê 13,56 MHz (Mifare). NÃO lê tag de 125 kHz, que é a de portaria e |
| Módulo Receptor Infravermelho KY-022 38KHz | 1 | 3,3 V a 5 V | digital, saída ativa em nível BAIXO | É o mesmo receptor do VS1838B já numa plaquinha com os pinos marcados, |
| Módulo Receptor Rádio Frequência 433MHz AM | 1 | 5 V | digital, um pino de dados | Os receptores baratos são superregenerativos: pegam ruído o tempo todo e |
| Módulo Transmissor Rádio Frequência 433MHz AM | 1 | 3 V a 12 V — quanto mais tensão, mais alcance | digital, um pino de dados (ASK/OOK) | Sem antena o alcance é de centímetros. Um fio reto de 17,3 cm é um quarto |
| Receptor Infravermelho VS1838B 38Khz | 1 | 2,7 V a 5,5 V | digital, saída ativa em nível BAIXO | Em repouso a saída fica em nível alto e cai quando chega portadora. Quem |
| Sensor de Obstáculo Infravermelho | 2 | 3,3 V a 5 V | digital, nível BAIXO quando detecta | Emissor e receptor no mesmo módulo: mede reflexão, não distância. A |
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
| Módulo Cartão SD | 1 | 5 V no módulo com regulador; o cartão em si é 3,3 V | SPI | Conferir se o módulo tem regulador e conversor de nível. Os que só têm |
| Real Time Clock RTC DS1307 | 1 | 5 V — o DS1307 não funciona confiável em 3,3 V | I2C | Erra na casa de minutos por mês: o cristal não é compensado por |
