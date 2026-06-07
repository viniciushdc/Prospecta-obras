# -*- coding: utf-8 -*-
"""Configuração central do Robô Prospecta Obras (Civil Obras)."""

# ---- Enums espelhados do app/painel (não altere os textos) ----
WORK_TYPES = [
    "Armazenagem / Silos", "Transbordo / Moega / Tombador", "Fábrica de Ração",
    "Sementeira / UBS", "Frigorífico / Granja", "Secador / Pré-limpeza",
    "Estrutura Industrial Geral", "Galpão / Logística",
    "Supermercado / Atacadão", "Agropecuária / Loja", "Centro de Distribuição",
    "Escola / Creche", "Saúde (UBS/UPA/Hospital)",
    "Segurança (Bombeiros/PM/Delegacia)", "Obra Pública / Institucional",
]
ORG_TYPES = [
    "Cooperativa", "Sementeira", "Agroindústria", "Cerealista", "Trading",
    "Produtor / Fazenda", "Indústria de Ração", "Frigorífico", "Varejo / Comércio",
    "Órgão Público / Prefeitura",
]
SOURCES = [
    "Licença Ambiental", "Plano Safra / PCA", "Notícia / Anúncio", "CONAB / Déficit",
    "Licitação (PNCP)", "Indicação", "Feira / Evento", "Prospecção Fria",
]
ROLES = [
    "Presidente", "Diretor", "Gerente de Projetos", "Gerente Industrial",
    "Engenheiro", "Comprador / Suprimentos", "Outro", "A identificar",
]
STATUSES = ["Mapeado", "Qualificado", "Contato", "Reunião", "Proposta", "Negociação", "Ganho", "Perdido"]
UFS = ["PR", "RS", "SC", "MS", "GO", "MT", "SP", "MG"]

# Cabeçalho do CSV — AGORA com a coluna 'data' (data de publicação da fonte)
CSV_HEADER = ["empresa", "org", "uf", "municipio", "local", "tipoObra", "fonte",
              "valor", "contato", "cargo", "tel", "email", "canal", "status",
              "fase", "data", "link", "notas"]

# ---- Filtro de relevância (só o que cheira a OBRA segue p/ a API) ----
KEYWORDS_OBRA = [
    "unidade armazenadora", "armazenagem", "armazém", "armazem", "silo", "silos",
    "secador", "secagem", "pré-limpeza", "pre-limpeza", "moega", "tombador",
    "transbordo", "fábrica de ração", "fabrica de racao", "fábrica de rações",
    "sementeira", "beneficiamento de sementes", "ubs", "unidade de beneficiamento",
    "granja", "aviário", "aviario", "frigorífico", "frigorifico", "abatedouro",
    "entreposto", "barracão", "barracao", "galpão", "galpao", "complexo logístico",
    "nova unidade", "ampliação", "ampliacao", "expansão", "expansao", "expandir",
    "construção", "construcao", "edificação", "obra", "planta industrial", "agroindustrial",
    "supermercado", "atacadão", "atacadao", "atacarejo", "atacado", "agropecuária", "agropecuaria",
    "centro de distribuição", "centro de distribuicao", "centro logístico", "centro logistico", "loja", "varejo",
    "escola", "escolas", "creche", "cmei", "emei", "ginásio", "ginasio", "quadra poliesportiva",
    "posto de saúde", "posto de saude", "unidade de saúde", "unidade de saude", "centro de saúde", "centro de saude",
    "upa", "unidade de pronto atendimento", "hospital", "pronto atendimento", "ambulatório", "ambulatorio",
    "quartel", "corpo de bombeiros", "bombeiros", "batalhão", "batalhao", "delegacia",
    "centro administrativo", "paço municipal", "paco municipal", "prefeitura", "terminal rodoviário", "rodoviária", "rodoviaria",
]

# ---- Consultas de notícia (Google News) — ampliadas p/ mais obras ----
CONSULTAS_NOTICIAS = [
    '"unidade armazenadora" cooperativa construção',
    '"fábrica de ração" cooperativa nova investimento',
    'cooperativa silo armazenagem ampliação Paraná',
    'cooperativa armazenagem grãos expansão "Rio Grande do Sul"',
    'agroindústria armazenagem grãos investimento "Mato Grosso do Sul"',
    'cooperativa armazém grãos nova unidade Goiás',
    'sementeira beneficiamento sementes nova unidade',
    'cooperativa frigorífico granja nova unidade investimento',
    'transbordo grãos moega tombador construção cooperativa',
    'secador grãos pré-limpeza nova unidade agro',
    'cerealista entreposto armazenagem investimento sul',
    'cooperativa inaugura amplia complexo agroindustrial',
]
# Nomes para buscar tanto a OBRA quanto o DECISOR (presidente/diretor citado em notícia)
COOPERATIVAS_ALVO = [
    "Coamo", "C.Vale", "Cooperativa Lar", "Copacol", "Cotrijal", "Cotrisal",
    "Coopatrigo", "Frísia Castrolanda Capal", "Cocamar", "Coopavel", "Integrada cooperativa",
    "Aurora coop", "Cooperalfa", "Coasul", "Auriverde cooperativa", "Coopermil",
    "Camnpal", "Cotripal", "Cooperitaipu", "Primato cooperativa", "Coagru",
    "Comigo cooperativa Goiás", "Coacal", "Cooxupé", "Coopercampos",
]
TERMO_INVESTIMENTO = "armazém OR silo OR ração OR ampliação OR investimento OR \"nova unidade\" OR obra"
# consultas específicas para descobrir o DECISOR (nome + cargo) por cooperativa
CONSULTA_DECISOR = '{coop} presidente OR diretor OR "diretor de operações" OR "gerente de obras"'

# ---- PNCP (2ª fonte: licitações públicas de obra) ----
PNCP_BASE = "https://pncp.gov.br/api/consulta/v1"
PNCP_DIAS = 45               # janela de busca (dias para trás)
PNCP_MODALIDADES = list(range(1, 15))  # tenta cada código de modalidade; inválidos são pulados
PNCP_MAX_PAGINAS = 3
PNCP_UFS = ["PR", "RS", "SC", "MS", "GO", "MT"]
UFS_ALVO = ["PR", "RS", "SC", "MS", "GO", "MT"]

# ---- Querido Diário (3ª fonte: Diários Oficiais — onde licenças e obras saem) ----
QD_BASE = "https://api.queridodiario.ok.org.br/gazettes"
QD_DIAS = 60
QD_SIZE = 15
QD_CONSULTAS = [
    "licença de instalação unidade armazenadora",
    "licença prévia armazenagem de grãos",
    "licença ambiental silos secador",
    "licença de instalação fábrica de ração",
    "licenciamento transbordo tombador grãos",
    "construção barracão armazém edital",
]

# ---- Portais de licenciamento ambiental (scaffold configurável) ----
PORTAIS_AMBIENTAIS = [
    {"nome": "IMA-SC", "uf": "SC", "url_busca": "", "item_selector": "", "ativo": False},
    {"nome": "IAT-PR", "uf": "PR", "url_busca": "", "item_selector": "", "ativo": False},
    {"nome": "FEPAM-RS", "uf": "RS", "url_busca": "", "item_selector": "", "ativo": False},
    {"nome": "IMASUL-MS", "uf": "MS", "url_busca": "", "item_selector": "", "ativo": False},
    {"nome": "SEMAD-GO", "uf": "GO", "url_busca": "", "item_selector": "", "ativo": False},
]

# ---- Modelos da API Claude ----
MODELO_BARATO = "claude-haiku-4-5"
MODELO_PRECISO = "claude-sonnet-4-6"
