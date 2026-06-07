# -*- coding: utf-8 -*-
"""Extrator de leads via API Claude — agora também extrai DECISOR e DATA."""
import json
import os
from anthropic import Anthropic

import config

_client = None


def _get_client():
    global _client
    if _client is None:
        key = os.environ.get("ANTHROPIC_API_KEY")
        if not key:
            raise RuntimeError("Defina ANTHROPIC_API_KEY (veja .env.example).")
        _client = Anthropic(api_key=key)
    return _client


SYSTEM = f"""Você é analista de prospecção da Civil Obras, construtora de obras
industriais e do agronegócio no Sul/Centro-Oeste do Brasil (PR, RS, SC, MS, GO, MT).

Leia um texto (notícia ou edital/licitação) e diga se indica uma OPORTUNIDADE
CONCRETA DE OBRA: empresa/órgão que vai construir/ampliar unidade de armazenagem,
silo, secador, moega/transbordo/tombador, fábrica de ração, sementeira/UBS, granja/
frigorífico, estrutura industrial, OU obra comercial/logística que a Civil Obras
também executa: barracão, supermercado, atacadão/atacarejo, agropecuária/loja,
centro de distribuição ou centro logístico, OU obra pública/institucional de
edificação (licitações de prefeituras/governos): escola, creche, posto/unidade/
centro de saúde, UPA, hospital, quartel/base do corpo de bombeiros, batalhão da PM,
delegacia, ginásio, centro administrativo. NÃO conte como obra: pavimentação,
asfalto, saneamento, iluminação, compra de equipamentos ou serviços sem edificação.

Responda APENAS com um objeto JSON válido, sem markdown, sem texto fora dele.

Se NÃO for oportunidade de obra: {{"relevante": false}}

Se FOR:
{{
  "relevante": true,
  "empresa": "nome da empresa/cooperativa/órgão",
  "org": um de {config.ORG_TYPES},
  "uf": uma de {config.UFS} ou "",
  "municipio": "cidade" ou "",
  "local": "endereço/bairro/distrito/rodovia/ponto de referência da obra APENAS se
            citado no texto (ex.: 'distrito de Vila Nova', 'próximo ao Porto Seco',
            'Rua X'); senão "",
  "tipoObra": um de {config.WORK_TYPES},
  "valor": inteiro em reais (0 se não houver),
  "contato": nome do DECISOR **somente se aparecer no texto** (ex.: presidente,
             diretor citado); senão "A identificar",
  "cargo": um de {config.ROLES} (o cargo do contato; "A identificar" se não souber),
  "tel": telefone APENAS se constar no texto, senão "",
  "email": e-mail APENAS se constar no texto, senão "",
  "fase": uma de ["Licença","Financiamento","Cotação","Em obra","Pós-obra"] conforme
          o estágio indicado no texto (licença ambiental = "Licença"; financiamento/
          BNDES/Plano Safra aprovado = "Financiamento"; cotação/licitação/edital =
          "Cotação"; obra em andamento = "Em obra"; inaugurada/concluída = "Pós-obra");
          "" se não der para saber,
  "resumo": "uma frase com o sinal de obra e o próximo passo sugerido"
}}

REGRAS: use exatamente os textos das listas. NUNCA invente nome, telefone ou
e-mail de pessoa — só registre o que estiver explícito no texto fornecido."""


def _parse_json(txt):
    txt = (txt or "").strip()
    if txt.startswith("```"):
        txt = txt.strip("`")
        txt = txt[txt.find("{"):txt.rfind("}") + 1]
    try:
        return json.loads(txt)
    except Exception:
        a, b = txt.find("{"), txt.rfind("}")
        if a >= 0 and b > a:
            try:
                return json.loads(txt[a:b + 1])
            except Exception:
                return None
    return None


def extrair_lead(item, modelo=None):
    modelo = modelo or config.MODELO_BARATO
    conteudo = f"FONTE: {item['origem']}\nDATA: {item.get('data','')}\nTÍTULO: {item['titulo']}\nTEXTO: {item['resumo']}"
    try:
        resp = _get_client().messages.create(
            model=modelo, max_tokens=500, system=SYSTEM,
            messages=[{"role": "user", "content": conteudo}],
        )
    except Exception as e:
        print(f"  ! erro API: {e}")
        return None

    txt = "".join(b.text for b in resp.content if getattr(b, "type", "") == "text")
    data = _parse_json(txt)
    if not data or not data.get("relevante"):
        return None

    org = data.get("org") if data.get("org") in config.ORG_TYPES else "Cooperativa"
    tipo = data.get("tipoObra") if data.get("tipoObra") in config.WORK_TYPES else "Estrutura Industrial Geral"
    uf = data.get("uf") if data.get("uf") in config.UFS else item.get("uf_hint", "")
    cargo = data.get("cargo") if data.get("cargo") in config.ROLES else "A identificar"
    try:
        valor = int(float(data.get("valor") or 0))
    except (TypeError, ValueError):
        valor = 0

    fases = ["Licença", "Financiamento", "Cotação", "Em obra", "Pós-obra"]
    fase = data.get("fase") if data.get("fase") in fases else ""

    return {
        "empresa": (data.get("empresa") or "").strip(),
        "org": org,
        "uf": uf,
        "municipio": (data.get("municipio") or "").strip(),
        "local": (data.get("local") or "").strip(),
        "tipoObra": tipo,
        "fonte": item["origem"],
        "valor": valor,
        "contato": (data.get("contato") or "A identificar").strip() or "A identificar",
        "cargo": cargo,
        "tel": (data.get("tel") or "").strip(),
        "email": (data.get("email") or "").strip(),
        "canal": "",
        "status": "Mapeado",
        "fase": fase,
        "data": item.get("data", ""),
        "link": item.get("link", ""),
        "notas": (data.get("resumo") or "").strip(),
    }
