import pytest
from dados import (
    ErroDeDados, carregar_componentes, carregar_projetos,
    carregar_compras, carregar_tudo,
)


def escrever(raiz, caminho_rel, texto):
    alvo = raiz / caminho_rel
    alvo.parent.mkdir(parents=True, exist_ok=True)
    alvo.write_text(texto, encoding="utf-8")


def test_le_componente_com_campos_minimos(tmp_path):
    escrever(tmp_path, "componentes/sensores.yaml",
             "- id: bmp280\n  nome: Sensor BMP280\n  qtd: 1\n")
    itens = carregar_componentes(tmp_path)
    assert len(itens) == 1
    assert itens[0].id == "bmp280"
    assert itens[0].qtd == 1
    assert itens[0].familia == "sensores"
    assert itens[0].tensao is None


def test_arquivo_vazio_nao_e_erro(tmp_path):
    escrever(tmp_path, "componentes/energia.yaml", "[]\n")
    assert carregar_componentes(tmp_path) == []


def test_recusa_id_repetido_entre_arquivos(tmp_path):
    escrever(tmp_path, "componentes/sensores.yaml",
             "- id: ldr\n  nome: LDR\n  qtd: 1\n")
    escrever(tmp_path, "componentes/passivos.yaml",
             "- id: ldr\n  nome: LDR de novo\n  qtd: 2\n")
    with pytest.raises(ErroDeDados, match="ja usado"):
        carregar_componentes(tmp_path)


def test_recusa_id_fora_do_kebab_case(tmp_path):
    escrever(tmp_path, "componentes/sensores.yaml",
             "- id: BMP_280\n  nome: Sensor\n  qtd: 1\n")
    with pytest.raises(ErroDeDados, match="kebab-case"):
        carregar_componentes(tmp_path)


def test_recusa_campo_obrigatorio_ausente(tmp_path):
    escrever(tmp_path, "componentes/sensores.yaml",
             "- id: bmp280\n  nome: Sensor\n")
    with pytest.raises(ErroDeDados, match="qtd"):
        carregar_componentes(tmp_path)


def test_le_projeto_com_precisa_como_mapa(tmp_path):
    escrever(tmp_path, "projetos/backlog.yaml",
             "- id: estufa\n  titulo: Estufa\n  descricao: teste\n"
             "  status: especificado\n  precisa:\n    dht22: 1\n    led-vermelho: 3\n")
    projetos = carregar_projetos(tmp_path)
    assert projetos[0].precisa == {"dht22": 1, "led-vermelho": 3}


def test_recusa_status_invalido(tmp_path):
    escrever(tmp_path, "projetos/backlog.yaml",
             "- id: estufa\n  titulo: Estufa\n  descricao: teste\n"
             "  status: quase-pronto\n  precisa: {}\n")
    with pytest.raises(ErroDeDados, match="status"):
        carregar_projetos(tmp_path)


def test_recusa_precisa_como_lista(tmp_path):
    escrever(tmp_path, "projetos/backlog.yaml",
             "- id: estufa\n  titulo: Estufa\n  descricao: teste\n"
             "  status: ideia\n  precisa: [dht22]\n")
    with pytest.raises(ErroDeDados, match="mapa"):
        carregar_projetos(tmp_path)


def test_le_item_de_compra(tmp_path):
    escrever(tmp_path, "compras/desejos.yaml",
             "- id: esp32c3-supermini\n  nome: ESP32-C3 SuperMini\n  qtd: 2\n"
             "  motivo: [estufa]\n  prioridade: alta\n  status: pesquisando\n")
    itens = carregar_compras(tmp_path)
    assert itens[0].prioridade == "alta"
    assert itens[0].motivo == ["estufa"]


def test_recusa_item_que_esta_nos_dois_lugares(tmp_path):
    escrever(tmp_path, "componentes/placas.yaml",
             "- id: esp32c3\n  nome: ESP32-C3\n  qtd: 1\n")
    escrever(tmp_path, "compras/desejos.yaml",
             "- id: esp32c3\n  nome: ESP32-C3\n  qtd: 2\n")
    with pytest.raises(ErroDeDados, match="Migracao pela metade"):
        carregar_tudo(tmp_path)
