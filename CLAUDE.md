# hw-laboratorio — a bancada

Inventário de componentes, backlog de projetos e lista de compras. Os projetos ficam em
repositórios próprios com prefixo `hw-`, dentro desta pasta e ignorados por este git.

Repositório público em `https://github.com/henriquemattosesilva/hw-laboratorio`,
página em `https://henriquemattosesilva.github.io/hw-laboratorio/`.

Este arquivo é o documento vivo. O desenho está em
`docs/superpowers/specs/2026-08-31-hw-laboratorio-design.md`.

> Para este arquivo ser carregado automaticamente, abra a sessão **dentro desta pasta**.
> Começando em `c:\HENRIQUE\Claude` ele não entra no contexto sozinho.

---

## Regra que não pode ser esquecida: README.md e index.html são gerados

**Nunca editar `README.md` nem `index.html` à mão.** Os dois saem de
`python ferramentas/gerar-pagina.py`, a partir dos YAML. Editar direto significa perder a
alteração na próxima geração.

## Regra que não pode ser esquecida: projeto novo entra no .gitignore

Repositório dentro de repositório faz o git de fora gravar um *gitlink* — um ponteiro para
um commit — que parece funcionar e some com o conteúdo. Por isso `novo-projeto.py`
acrescenta a pasta ao `.gitignore` sozinho. Criando projeto sem o script, fazer isso à mão.

## Como as três bases se ligam

O `id` é a cola. O mesmo `id` vale em `compras/desejos.yaml` e depois em `componentes/`,
o que permite um projeto pedir peça que ainda não chegou. Os quatro cruzamentos aparecem
no topo do README e da página:

- **o que falta por projeto** — conta quantidade, não presença: cinco LEDs pedidos com dois
  na gaveta é falta, ainda que o id exista;
- **id desconhecido** — projeto pedindo id que não existe em lugar nenhum, quase sempre
  erro de digitação;
- **estoque insuficiente** — dois projetos reservando a mesma peça;
- **compra órfã** — item no carrinho que nenhum projeto pede.

Reserva estoque todo status menos `ideia`. Projeto `montado` ou `publicado` continua
ocupando as peças: publicar diz respeito ao repositório, não ao hardware. Desmontar é o que
libera, e se registra voltando o status para `especificado`.

## Estrutura dos dados

`componentes/*.yaml` — um arquivo por família. Só `id`, `nome` e `qtd` são obrigatórios;
`tensao`, `interface`, `endereco`, `biblioteca`, `datasheet`, `compra` e `notas` entram
quando houver o que dizer. Resistor não tem biblioteca, e campo vazio só suja o arquivo.

**No campo `notas`, uma linha é uma afirmação completa.** A página renderiza com
`white-space: pre-line`, então quebrar linha no meio da frase para o arquivo ficar bonito
quebra a frase na tela.

Arquivo novo em `componentes/` precisa ser registrado em `TITULOS`, no `gerar-pagina.py`.
Sem isso o gerador para com erro — de propósito: silenciosamente, as peças sumiriam da
página.

## Comandos

```text
python -m pip install -r requisitos.txt   # PyYAML e pytest
python -m pytest                          # 38 testes
python ferramentas/gerar-pagina.py        # sempre, depois de mexer em qualquer YAML
python ferramentas/novo-projeto.py nome "Título"
pwsh ferramentas/previa.ps1 -Largura 390 -Destino previa-390.png
python fritzing/empacotar.py              # sempre, depois de mexer numa SVG de peca
python fritzing/instalar.py               # atualiza a peca no Fritzing (com ele fechado)
```

## Peças Fritzing

`fritzing/` guarda peças próprias do Fritzing, para módulos que o core do programa não
traz. Hoje são duas, o transmissor FS1000A e o receptor MX-05V de 433 MHz. Os `id` são os
mesmos do inventário, `rf433-tx` e `rf433-rx`.

**Reimportar o `.fzpz` não atualiza peça já instalada.** O Fritzing recusa com *"Part
module ID must be unique"*, porque o id já está na biblioteca — e o id é mantido de
propósito, senão cada correção viraria uma peça nova. Atualizar é rodar
`python fritzing/instalar.py`, com o Fritzing fechado.

**Os `.fzpz` em `fritzing/dist/` são gerados.** Saem de `python fritzing/empacotar.py`, a
partir do FZP e das SVGs. Mexer numa SVG sem reempacotar deixa o zip com o desenho antigo
dentro, em silêncio — há teste para isso, e ele já pegou o erro uma vez.

**A pinagem do receptor é espelhada entre as duas faces.** A serigrafia fica no verso,
onde se lê GND DATA DATA VCC; vista de cima, que é como o Fritzing desenha, a ordem é
**VCC DATA DATA GND**. Ler o verso sem espelhar troca alimentação com terra. As duas
ordens têm teste.

Detalhes de instalação, coordenadas e conferência em `fritzing/README.md`.

## Impressão 3D

A impressora é do irmão do Henrique, uma Bambu Lab — ele disse "X2D", que não existe na
linha; o mais próximo é o **H2D**. **Confirmar olhando na máquina.** Ele pretende comprar
uma **A1 mini**, cuja mesa é 180 × 180 × 180 mm, e esse é o teto de qualquer peça desenhada
aqui, para que nada deixe de imprimir na impressora futura.

Cada impressão custa pedir um favor, então as peças são desenhadas para acertar de
primeira. A pasta `cases/` ainda não existe: depende de OpenSCAD instalado e da peça de
calibração de folga impressa, porque sem o número de folga real desenhar caixa é chutar
tolerância. Plano próprio.

## O que ainda não foi verificado

**Se o cruzamento de estoque vai ser usado.** É a aposta central do desenho. Se depois de
três projetos ninguém tiver olhado para o "o que falta", o gerador deve encolher para só
listar componentes — e aí o CSV do Notion teria bastado.

**Os campos ricos do inventário.** Tensão, interface, endereço e biblioteca vieram de
leitura de datasheet e memória, não de medição na bancada. O campo `notas` guarda as
afirmações mais úteis e também as mais fáceis de estarem erradas.

**A quantidade do TCS34725** veio em branco no export do Notion e está anotada como 1 por
suposição. Conferir na gaveta.

**O modelo do sensor de frequência cardíaca.** O nome no Notion é genérico e não diz se é
um Pulse Sensor analógico ou um MAX30102 em I2C — são projetos completamente diferentes.
Conferir a serigrafia.

**Os preços da lista de compras** foram conferidos em 02/09/2026 e envelhecem. O raciocínio
de `referencias/placas.md` não envelhece; os números, sim. Reconferir antes de comprar.

**O XIAO ESP32C3 e o ESP32-C6 nunca foram usados aqui.** A recomendação de comprar 2 + 3 em
vez de 5 de uma só existe justamente por isso: são placas escolhidas na leitura, não no uso.

**O `arduino-cli` não está no PATH.** Só existe `~/.arduinoIDE/`. Resolver no primeiro
projeto que precisar compilar.

**OpenSCAD não está instalado.** Bloqueia exportar STL a partir de `.scad`.
