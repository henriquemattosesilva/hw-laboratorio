# hw-laboratorio — base para os projetos de eletrônica

Desenho da pasta `c:\HENRIQUE\Claude\Arduino` como repositório raiz que guarda o inventário
de componentes, o backlog de projetos, a lista de compras, o template de projeto novo e a
biblioteca de cases 3D. Os projetos em si continuam repositórios separados dentro dela.

Data: 31/08/2026.

---

## Por que isto existe

O inventário de hoje é um CSV exportado do Notion com três colunas: nome, categoria e
quantidade. Ele responde *eu tenho?* e nada mais. Não responde *serve nesse projeto?*, que é
a pergunta que se faz de verdade — para isso faltam tensão, protocolo, endereço, biblioteca
e as armadilhas de cada peça.

O segundo problema é que o Henrique quer comprar placas novas (Bluetooth, Wi-Fi, USB-C,
bateria com carga pela própria placa) e não existe lugar onde a compra se ligue ao motivo da
compra. Sem esse laço, ou se compra item que fica na gaveta, ou se descobre no meio da
montagem que falta um resistor de 4,7 kΩ.

## Decisões

**Um repositório próprio, público: `hw-laboratorio`.** Segue o padrão `hw-*` já usado no
`hw-codigo-morse`, com página no GitHub Pages em
`henriquemattosesilva.github.io/hw-laboratorio/`. O motivo de ser público e ter página não é
vaidade: é poder abrir o inventário no celular dentro da loja de eletrônica, sem login.

**Os projetos continuam repositórios separados, ignorados pela raiz.** O `codigo-morse` já é
um repositório com remoto próprio. Um repositório dentro de outro faz o git de fora gravar um
*gitlink* — um ponteiro para um commit — que parece funcionar e some com o conteúdo. Por isso
cada projeto entra no `.gitignore` da raiz, e o script que cria projeto novo acrescenta a
linha sozinho. Se depender de alguém lembrar, um dia não lembra.

**O primeiro commit preserva os CSVs do Notion intactos.** A conversão para YAML vem no
segundo commit. Com a origem no histórico, apagar os CSVs depois não perde nada e dá para
conferir a migração item a item.

**Os dados são ligados por `id`.** Cada componente tem um identificador estável (`bmp280`,
`esp8266-nodemcu`). O backlog e a lista de compras referenciam esses ids, e não o nome por
extenso — nome muda, id não. É o que permite responder por script *o que falta para o
projeto X* em vez de conferir a olho.

**A pasta continua se chamando `componentes/`.** É o nome que o Henrique já usa. Renomear
para `inventario` seria troca sem ganho.

## Estrutura

```
Arduino/                              raiz do repositório hw-laboratorio
├── CLAUDE.md                         documento vivo: convenções, estado, decisões
├── README.md                         GERADO
├── index.html                        GERADO — página do Pages, busca no celular
├── .gitignore                        ignora os repositórios de projeto
├── .gitattributes                    eol=lf, igual ao morse
├── componentes/
│   ├── placas.yaml                   Uno, Nano, NodeMCU, e as que vierem
│   ├── sensores.yaml
│   ├── displays.yaml
│   ├── atuadores.yaml                servo, relé, buzzer, laser, emissor IR
│   ├── comunicacao.yaml              RF 433, RFID, IR, e o que for de rádio
│   ├── passivos.yaml                 resistores, LEDs, transistores, botões, potenciômetros
│   ├── prototipagem.yaml             protoboards, jumpers, pinos, cabos
│   ├── energia.yaml                  VAZIO hoje — é exatamente o buraco a preencher
│   └── diversos.yaml                 RTC, cartão SD
├── projetos/
│   └── backlog.yaml
├── compras/
│   └── desejos.yaml
├── referencias/
│   ├── placas.md                     comparativo das placas: o que serve para quê
│   └── energia.md                    LiPo, carga por USB-C, deep sleep, autonomia
├── cases/
│   ├── lib/
│   │   ├── calibracao-folga.scad     peça de teste — imprimir UMA vez
│   │   └── caixa.scad                caixa paramétrica
│   └── <projeto>/                    cases específicos
├── ferramentas/
│   ├── gerar-pagina.py               YAML → README.md + index.html
│   ├── novo-projeto.py               cria projeto a partir do modelo
│   └── modelo/                       esqueleto de projeto hw-*
├── docs/superpowers/specs/           specs de desenho (este arquivo)
└── codigo-morse/                     repositório separado, ignorado
```

## Modelo de dados

### Componente

```yaml
- id: bmp280                      # obrigatório, estável, kebab-case
  nome: Sensor de Pressão e Temperatura BMP280
  qtd: 1                          # obrigatório
  tensao: 3.3V (módulo com regulador aceita 5V)
  interface: I2C
  endereco: 0x76 ou 0x77
  biblioteca: Adafruit_BMP280
  datasheet: https://...
  compra:
    loja: ...
    link: https://...
    preco: 18.90
    data: 2025-03-14
  notas: |
    Não mede umidade — isso é o BME280, que é fisicamente parecido.
```

Só `id`, `nome` e `qtd` são obrigatórios. Resistor não tem biblioteca nem endereço, e forçar
campo vazio só suja o arquivo.

O campo `notas` carrega a armadilha de cada peça: qual módulo entrega digital quando o
componente solto entrega analógico, qual precisa de nível lógico de 3,3 V, qual tem
serigrafia trocada entre versões. É o campo que evita erro de montagem, e é o que o CSV atual
não tem onde guardar.

### Projeto no backlog

```yaml
- id: estufa
  titulo: Monitor de estufa
  descricao: Umidade do solo e temperatura, envio por Wi-Fi
  status: ideia                   # ideia | especificado | montado | publicado
  precisa: [esp32c3-supermini, dht22, higrometro-solo, lipo-500mah]
  repositorio: null               # preenchido quando o projeto nascer
```

### Item de compra

```yaml
- id: esp32c3-supermini
  nome: ESP32-C3 SuperMini
  qtd: 2
  motivo: [estufa, sensor-porta]  # ids do backlog que pedem o item
  prioridade: alta                # alta | media | baixa
  status: pesquisando             # pesquisando | comprado | chegou
  link: https://...
  preco: 24.00
```

Quando um item chega, ele migra de `compras/desejos.yaml` para o arquivo de componentes da
família certa, levando junto o bloco `compra`.

## Geradores

### `ferramentas/gerar-pagina.py`

Lê todos os YAML e escreve `README.md` e `index.html`. A página é um arquivo único, sem
dependência externa, com busca por texto e filtro por família — feita para o celular, porque
é lá que ela é consultada.

Além da listagem, calcula e mostra:

- **o que falta por projeto** — `precisa` menos o que existe em `componentes/`;
- **compras órfãs** — item em `desejos.yaml` que nenhum projeto do backlog pede;
- **conflito de estoque** — componente com quantidade menor que a soma dos projetos que o
  reservam.

Esses três cruzamentos são a razão de ter YAML com id em vez de planilha. Sem eles, a opção
honesta seria manter o CSV.

O `README.md` e o `index.html` **nunca são editados à mão**, pela mesma razão registrada no
`hw-codigo-morse`: a edição se perde na próxima geração.

### `ferramentas/novo-projeto.py NOME`

Cria `NOME/` a partir de `ferramentas/modelo/`, com `CLAUDE.md`, `README.md`, `MONTAGEM.md`,
pasta de sketch, `.gitignore`, `.gitattributes` e gerador de página próprio — o esqueleto que
já se provou no morse. Roda `git init` e **acrescenta `NOME/` ao `.gitignore` da raiz**.

Não cria o repositório no GitHub. Publicar é decisão de quem está trabalhando, não efeito
colateral de criar pasta.

## Cases 3D

A impressora é do irmão do Henrique — uma Bambu Lab. Ele pretende comprar uma **A1 mini**
para si. Isso muda o desenho de duas formas:

**Toda peça cabe em 180 × 180 × 180 mm**, que é a mesa da A1 mini. Assim nada desenhado hoje
deixa de imprimir na impressora futura.

**Cada impressão custa pedir um favor.** Não dá para iterar barato. Por isso a primeira peça
a existir é a `calibracao-folga.scad`: um bloco com pinos e furos em folga de 0,1 / 0,2 / 0,3
/ 0,4 mm. Imprime-se **uma vez**, vê-se qual encaixa, e o número vira a constante de folga de
todos os cases seguintes. Sem esse número, cada case vira tentativa e erro com custo social.

A `caixa.scad` é paramétrica: dimensões internas, espessura de parede, lista de recortes
(cada um com face, posição e tamanho), postes de fixação pelo padrão de furos da placa, e
tampa. O resto da biblioteca — snap-fit, dobradiça, suporte de bateria — só entra quando
existir um case real pedindo. Desenhar encaixe antes de ter caixa é inventar problema.

## Dependências

Verificado nesta máquina em 31/08/2026:

| Ferramenta | Situação | Ação |
|---|---|---|
| git 2.54 | presente | — |
| gh 2.96 | presente | — |
| Python 3.12.10 | presente | — |
| PyYAML | **ausente** | `pip install pyyaml` |
| OpenSCAD | **ausente** | instalar para exportar STL a partir dos `.scad` |
| arduino-cli | **ausente do PATH** | só existe `~/.arduinoIDE/`; resolver quando um projeto precisar compilar |

## Fora de escopo

**Preço e disponibilidade automáticos de loja.** Scraping de loja brasileira quebra sozinho,
e manter o scraper viraria o projeto.

**Banco de dados.** Dezenas a poucas centenas de itens cabem em YAML. SQLite aqui é peso sem
retorno.

**Interface de edição.** O inventário é editado no editor de texto, como qualquer arquivo do
repositório.

**Biblioteca 3D completa.** Só calibração e caixa. O resto nasce da necessidade.

## O que ainda não está confirmado

**O modelo da impressora do irmão.** O Henrique disse "Bambu Lab X2D"; esse nome não existe
na linha da Bambu — o mais próximo é o **H2D**. Como o teto adotado é o da A1 mini, isso não
bloqueia nada, mas o valor precisa ser corrigido no `CLAUDE.md` quando ele conferir na
máquina.

**Se o cruzamento de estoque vai ser usado.** É a aposta central do desenho. Se depois de
três projetos o Henrique nunca tiver olhado para o "o que falta", o gerador deve encolher
para só listar componentes — e aí o CSV teria bastado.

**Quais placas comprar.** Deliberadamente fora desta spec. A pesquisa de placas com BLE,
USB-C e carga de LiPo é o próximo trabalho, e ela depende do backlog existir primeiro.
