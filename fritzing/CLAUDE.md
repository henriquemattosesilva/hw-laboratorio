# fritzing — as peças que o programa não traz

Oficina de peças Fritzing do `hw-laboratorio`. O core do Fritzing 1.0 tem 1791 peças e
mesmo assim falta módulo comum de bancada; aqui as que faltam são feitas.

**Este arquivo tem só o que quebra o trabalho quando esquecido.** O como-fazer está no
`README.md` da pasta; o que o Fritzing cobra e por quê, no `CONVENCOES.md`. Nenhum dos
três repete o outro.

> Para este arquivo carregar sozinho, a sessão precisa abrir **dentro desta pasta**.
> Começando em `Arduino/` ou em `c:\HENRIQUE\Claude`, ele não entra no contexto —
> a seção "Peças Fritzing" do `Arduino/CLAUDE.md` é o que aponta para cá.

---

## Regra que não pode ser esquecida: peça nova sai do gerador

```text
python fritzing/ferramentas/nova-peca.py <id> --mm LxA --pinos NOME,NOME [--lado ...]
```

**Não copiar uma pasta de peça existente.** Copiar herda `moduleId`, nome de arquivo e
coordenadas da outra peça, e as três coisas dão erro silencioso: a peça parece certa e o
Fritzing recusa importar, ou pior, importa e não encaixa.

O gerador resolve unidade do viewBox, passo dos furos, ordem dos conectores e barramento.
O que ele **não** faz é o desenho: o ornamento do breadboard, e o esquemático além de uma
caixa vazia com o nome dentro. Peça cujo símbolo diz o que ela faz — buzzer, LED, sensor —
merece o esquemático refeito à mão, com o circuito de verdade entre os pinos. O
`buzzer-ativo` é assim: nasceu do gerador e teve as quatro vistas reescritas.

Cada SVG de breadboard traz um comentário no ponto onde o ornamento entra.

## Regra que não pode ser esquecida: o .fzpz e a previa.html são gerados

Como o `README.md` e o `index.html` da raiz do repositório. O `.fzpz` de cada peça sai de
`empacotar.py` e a folha de contato sai de `previa.py`. Editar à mão significa perder na
próxima geração — e no caso do `.fzpz`, significa um zip com desenho diferente do fonte.

**O `.fzpz` mora dentro da pasta da peça**, ao lado do `part.fzp`. É ele que o Fritzing
importa; o `part.fzp` sozinho não serve, porque cita as SVGs por caminho relativo. Os dois
juntos fazem a pasta da peça ser autossuficiente.

Existe teste para isso (`test_os_fzpz_publicados_estao_em_dia_com_os_fontes`), e ele já
pegou o erro de verdade duas vezes.

## Regra que não pode ser esquecida: o moduleId nunca muda

Depois que uma peça foi publicada, o `moduleId` é dela para sempre. Trocar a cada correção
encheria a biblioteca do Fritzing de cópias, cada uma parecendo peça diferente.

Isso faz o Fritzing reclamar ao reimportar o `.fzpz`:

```text
Part module ID must be unique.   /   Part load error
```

**O erro engana.** A essa altura os arquivos novos já foram copiados para o disco: fechar
e reabrir o programa mostra a peça atualizada. O caminho limpo é `instalar.py`.

E nada disso atualiza sketch já salvo — o `.fzz` guarda cópia própria da peça.

## Regra que não pode ser esquecida: olhar o desenho

Nenhum teste pega desenho torto, texto fora da placa ou rótulo trocado. **Todo defeito
visual que esta pasta já teve apareceu só na folha de contato** — inclusive dois no
próprio gerador, que produzia peça aprovada em todas as verificações e com o texto
vazando para fora da placa:

```text
python fritzing/ferramentas/previa.py
pwsh ferramentas/previa.ps1 -Arquivo fritzing/previa.html -Largura 1400 -Altura 1000 \
     -Destino previa-fritzing.png -Inteira
```

## Comandos

```text
python -m pytest                              # 53 testes, 35 deles desta pasta
python fritzing/ferramentas/nova-peca.py ...  # peça nova
python fritzing/ferramentas/previa.py         # folha de contato
python fritzing/ferramentas/empacotar.py      # os .fzpz
python fritzing/ferramentas/instalar.py       # biblioteca do Fritzing (fechado)

PYTHONIOENCODING=utf-8 python \
  ~/AppData/Local/Programs/Fritzing/fritzing-parts/fzp_checker.py fritzing/pecas/*/*.fzpz
```

O `PYTHONIOENCODING` não é enfeite: sem ele o verificador quebra ao imprimir o ✓ no
console do Windows, e o que aparece é o *help* do programa, o que engana.

## As peças

| pasta | conectores, vista de cima |
|---|---|
| `rf433-tx` | DATA · VCC · GND · ANT |
| `rf433-rx` | **VCC · DATA · DATA · GND** · ANT — espelhado da serigrafia, que fica no verso |
| `buzzer-ativo` | GND · SINAL, empilhados na ponta esquerda |

As três com `id` igual ao do inventário em `componentes/`.

## O que ainda não foi verificado

**O encaixe no passo de 0,1" dentro do Fritzing.** O teste confere o passo no SVG, mas
quem confirma que a peça senta na protoboard é o programa aberto. Nenhuma das três foi
conferida assim.

**A orientação do desenho do receptor MX-05V** e a posição da fileira de furos ao longo
da borda, nas duas peças de 433 MHz. Saiu de foto de catálogo. Não afeta a ligação.

**A polaridade de acionamento do buzzer P15.** Vários tocam com nível BAIXO. Está dito na
`description` da peça, que é onde tem chance de ser lido na hora de ligar.

**As cotas** do FS1000A e do P15 vieram de anúncio e de ficha do fabricante, não de
paquímetro. Só importam na vista de PCB.
