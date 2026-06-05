# -*- coding: utf-8 -*-
"""
Fontes de coleta de sinais de obra.
1) buscar_noticias()  -> Google News RSS (funciona já), com DATA de publicação.
2) buscar_pncp()      -> API pública do PNCP (licitações/editais de obra), com DATA.
3) buscar_portal_ambiental() -> adaptador genérico p/ portais de licenciamento.
"""
import time
import datetime
import urllib.parse
import requests
import feedparser
from bs4 import BeautifulSoup

import config

UA = {"User-Agent": "Mozilla/5.0 (compatible; ProspectaObras/1.1; +civilobras)"}
GNEWS = "https://news.google.com/rss/search?q={q}&hl=pt-BR&gl=BR&ceid=BR:pt-419"


def _item(titulo, resumo, link, origem, uf="", data=""):
    return {
        "titulo": (titulo or "").strip(),
        "resumo": BeautifulSoup(resumo or "", "html.parser").get_text(" ", strip=True)[:1400],
        "link": link or "",
        "origem": origem,
        "uf_hint": uf,
        "data": data,
    }


def _fmt_data(s):
    """Converte 'aaaa-mm-dd...' em 'dd/mm/aaaa'. Devolve '' se não der."""
    if not s:
        return ""
    try:
        return datetime.datetime.fromisoformat(s[:10]).strftime("%d/%m/%Y")
    except Exception:
        return s[:10]


# ---------------- 1) NOTÍCIAS ----------------
def buscar_noticias(consultas=None, cooperativas=None, max_por_consulta=12, buscar_decisor=True):
    consultas = consultas or config.CONSULTAS_NOTICIAS
    cooperativas = cooperativas if cooperativas is not None else config.COOPERATIVAS_ALVO

    queries = list(consultas)
    for coop in cooperativas:
        queries.append(f'"{coop}" ({config.TERMO_INVESTIMENTO})')
        if buscar_decisor:  # consulta que tende a trazer nome+cargo do decisor
            queries.append(config.CONSULTA_DECISOR.format(coop=f'"{coop}"'))

    itens, vistos = [], set()
    for q in queries:
        url = GNEWS.format(q=urllib.parse.quote(q))
        try:
            feed = feedparser.parse(url, request_headers=UA)
        except Exception as e:
            print(f"  ! consulta falhou: {e}")
            continue
        for e in feed.entries[:max_por_consulta]:
            link = getattr(e, "link", "")
            if link in vistos:
                continue
            vistos.add(link)
            data = ""
            if getattr(e, "published_parsed", None):
                data = time.strftime("%d/%m/%Y", e.published_parsed)
            itens.append(_item(getattr(e, "title", ""), getattr(e, "summary", ""),
                               link, "Notícia / Anúncio", data=data))
        time.sleep(0.4)
    return itens


# ---------------- 2) PNCP (licitações) ----------------
def buscar_pncp(dias=None, modalidades=None, max_paginas=None, ufs=None):
    dias = dias or config.PNCP_DIAS
    modalidades = modalidades or config.PNCP_MODALIDADES
    max_paginas = max_paginas or config.PNCP_MAX_PAGINAS
    ufs = ufs if ufs is not None else config.PNCP_UFS

    fim = datetime.date.today()
    ini = fim - datetime.timedelta(days=dias)
    di, df = ini.strftime("%Y%m%d"), fim.strftime("%Y%m%d")
    url = f"{config.PNCP_BASE}/contratacoes/publicacao"

    itens, vistos = [], set()
    for cod in modalidades:
        for pag in range(1, max_paginas + 1):
            params = {"dataInicial": di, "dataFinal": df,
                      "codigoModalidadeContratacao": cod, "pagina": pag}
            try:
                r = requests.get(url, params=params, headers=UA, timeout=30)
                if r.status_code != 200:
                    break
                regs = (r.json() or {}).get("data") or []
            except Exception:
                break
            if not regs:
                break
            for c in regs:
                uo = c.get("unidadeOrgao") or {}
                uf = uo.get("ufSigla") or ""
                if ufs and uf not in ufs:
                    continue
                objeto = c.get("objetoCompra") or ""
                ctrl = c.get("numeroControlePNCP") or objeto[:60]
                if ctrl in vistos:
                    continue
                vistos.add(ctrl)
                orgao = uo.get("nomeUnidade") or (c.get("orgaoEntidade") or {}).get("razaoSocial") or "Órgão público"
                muni = uo.get("municipioNome") or ""
                valor = c.get("valorTotalEstimado") or 0
                data = _fmt_data(c.get("dataPublicacaoPncp") or c.get("dataInclusao") or "")
                link = c.get("linkSistemaOrigem") or "https://pncp.gov.br"
                resumo = f"{objeto} | Órgão: {orgao} | Local: {muni}/{uf} | Valor estimado: R$ {valor}"
                itens.append(_item(orgao, resumo, link, "Licitação (PNCP)", uf=uf, data=data))
            time.sleep(0.3)
    return itens


# ---------------- 3) QUERIDO DIÁRIO (Diários Oficiais) ----------------
def buscar_diario_oficial(consultas=None, dias=None, size=None, ufs=None):
    consultas = consultas or config.QD_CONSULTAS
    dias = dias or config.QD_DIAS
    size = size or config.QD_SIZE
    ufs = ufs if ufs is not None else config.UFS_ALVO
    desde = (datetime.date.today() - datetime.timedelta(days=dias)).isoformat()

    itens, vistos = [], set()
    for q in consultas:
        params = {"querystring": q, "excerpt_size": 500, "number_of_excerpts": 1,
                  "size": size, "published_since": desde, "sort_by": "descending_date"}
        try:
            r = requests.get(config.QD_BASE, params=params, headers=UA, timeout=30)
            if r.status_code != 200:
                continue
            regs = (r.json() or {}).get("gazettes") or []
        except Exception as e:
            print(f"  ! Querido Diário: {e}")
            continue
        for g in regs:
            uf = g.get("state_code") or ""
            if ufs and uf not in ufs:
                continue
            muni = g.get("territory_name") or ""
            link = g.get("url") or g.get("txt_url") or "https://queridodiario.ok.org.br"
            data = _fmt_data(g.get("date") or "")
            ex = g.get("excerpts") or []
            texto = (ex[0] if isinstance(ex, list) and ex else "") or ""
            ch = (muni, g.get("date"), q[:12])
            if ch in vistos:
                continue
            vistos.add(ch)
            resumo = f"{texto} | Diário Oficial de {muni}/{uf}"
            itens.append(_item(f"Diário Oficial — {muni}", resumo, link, "Licença Ambiental", uf=uf, data=data))
        time.sleep(0.4)
    return itens


# ---------------- 4) Portal ambiental (scaffold) ----------------
def buscar_portal_ambiental(cfg, timeout=25):
    if not cfg.get("ativo") or not cfg.get("url_busca"):
        return []
    try:
        r = requests.get(cfg["url_busca"], headers=UA, timeout=timeout)
        r.raise_for_status()
    except Exception as e:
        print(f"  ! {cfg['nome']}: {e}")
        return []
    soup = BeautifulSoup(r.text, "html.parser")
    blocos = soup.select(cfg.get("item_selector") or "body") or [soup.select_one("body")]
    itens = []
    for b in blocos:
        if not b:
            continue
        texto = b.get_text(" ", strip=True)
        if len(texto) < 40:
            continue
        itens.append(_item(cfg["nome"], texto, cfg["url_busca"], "Licença Ambiental", uf=cfg.get("uf", "")))
    return itens


def coletar_tudo(usar_noticias=True, usar_pncp=True, usar_diario=True, usar_portais=True):
    itens = []
    if usar_noticias:
        print("→ Notícias (Google News)...")
        n = buscar_noticias()
        print(f"  {len(n)} itens"); itens += n
    if usar_pncp:
        print("→ Licitações (PNCP)...")
        p = buscar_pncp()
        print(f"  {len(p)} itens"); itens += p
    if usar_diario:
        print("→ Diários Oficiais (Querido Diário)...")
        d = buscar_diario_oficial()
        print(f"  {len(d)} itens"); itens += d
    if usar_portais:
        for cfg in config.PORTAIS_AMBIENTAIS:
            if cfg.get("ativo"):
                print(f"→ Portal {cfg['nome']}...")
                itens += buscar_portal_ambiental(cfg)
    return itens
