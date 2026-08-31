from analise import (
    Conflito, compras_orfas, conflitos_de_estoque,
    faltando_por_projeto, ids_desconhecidos,
)
from dados import Componente, ItemCompra, Projeto


def comp(ident, qtd=1, nome=None):
    return Componente(id=ident, nome=nome or ident, qtd=qtd, familia="teste")


def proj(ident, precisa, status="especificado"):
    return Projeto(id=ident, titulo=ident, descricao="", status=status, precisa=precisa)


def test_falta_o_que_nao_esta_no_inventario():
    componentes = [comp("dht22")]
    projetos = [proj("estufa", {"dht22": 1, "esp32c3": 1})]
    assert faltando_por_projeto(componentes, projetos) == {"estufa": ["esp32c3"]}


def test_falta_tambem_quando_a_quantidade_nao_cobre():
    componentes = [comp("led-vermelho", qtd=2)]
    projetos = [proj("painel", {"led-vermelho": 5})]
    assert faltando_por_projeto(componentes, projetos) == {"painel": ["led-vermelho"]}


def test_projeto_coberto_nao_aparece_faltando():
    componentes = [comp("led-vermelho", qtd=5)]
    projetos = [proj("painel", {"led-vermelho": 5})]
    assert faltando_por_projeto(componentes, projetos) == {"painel": []}


def test_id_que_nao_existe_em_lugar_nenhum_e_reportado():
    componentes = [comp("dht22")]
    compras = [ItemCompra(id="esp32c3", nome="ESP32", qtd=1)]
    projetos = [proj("estufa", {"dht22": 1, "esp32c3": 1, "dht-22": 1})]
    assert ids_desconhecidos(componentes, compras, projetos) == [("estufa", "dht-22")]


def test_compra_que_nenhum_projeto_pede_e_orfa():
    compras = [ItemCompra(id="esp32c3", nome="ESP32", qtd=1),
               ItemCompra(id="oled", nome="OLED", qtd=1)]
    projetos = [proj("estufa", {"esp32c3": 1})]
    assert compras_orfas(compras, projetos) == ["oled"]


def test_conflito_quando_dois_projetos_pedem_mais_do_que_existe():
    componentes = [comp("servo-sg90", qtd=2, nome="Micro Servo SG90")]
    projetos = [proj("braco", {"servo-sg90": 2}), proj("porta", {"servo-sg90": 1})]
    assert conflitos_de_estoque(componentes, projetos) == [
        Conflito(id="servo-sg90", nome="Micro Servo SG90", tem=2,
                 reservado=3, projetos=["braco", "porta"])
    ]


def test_ideia_nao_reserva_estoque():
    componentes = [comp("servo-sg90", qtd=2)]
    projetos = [proj("braco", {"servo-sg90": 2}),
                proj("porta", {"servo-sg90": 1}, status="ideia")]
    assert conflitos_de_estoque(componentes, projetos) == []


def test_publicado_continua_reservando():
    componentes = [comp("servo-sg90", qtd=1)]
    projetos = [proj("braco", {"servo-sg90": 1}, status="publicado"),
                proj("porta", {"servo-sg90": 1}, status="especificado")]
    assert len(conflitos_de_estoque(componentes, projetos)) == 1
