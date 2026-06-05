#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Robô Prospecta Obras — Civil Obras
Coleta sinais de obra (notícias + licitações PNCP + licenças), qualifica com a
API Claude (incl. decisor e data) e gera CSV pronto p/ importar no painel.

Uso:
    python robo.py                 # tudo, modelo barato
    python robo.py --dry-run       # só coleta e mostra (sem API)
    python robo.py --sem-pncp      # desliga uma fonte
    python robo.py --modelo preciso --limite 40
"""
import argparse
import csv
import json
import os
import re
import unicodedata
from datetime import datetime

import config
import fontes
import extrator

# carrega a chave do arquivo .env automaticamente, se existir
try:
    from dotenv import load_dotenv
    load_dotenv()
except Exception:
    pass

PASTA = os.path.dirname(os.path.abspath(__file__))
ARQ_VISTOS = os.path.join(PASTA, "vistos.json")
ARQ_SAIDA = os.path.join(PASTA, "leads_novos.csv")


def _slug(s):
    s = unicodedata.normalize("NFKD", (s or "").lower())
    s = "".join(c for c in s if not unicodedata.combining(c))
    return re.sub(r"[^a-z0-9]+", "", s)


def chave(lead):
    return f"{_slug(lead['empresa'])}|{_slug(lead['municipio'])}|{_slug(lead['tipoObra'])}"


def carregar_vistos():
    if os.path.exists(ARQ_VISTOS):
        try:
            return set(json.load(open(ARQ_VISTOS, encoding="utf-8")))
        except Exception:
            return set()
    return set()


def salvar_vistos(v):
    json.dump(sorted(v), open(ARQ_VISTOS, "w", encoding="utf-8"), ensure_ascii=False, indent=0)


def relevante_por_keyword(item):
    blob = f"{item.get('titulo','')} {item.get('resumo','')}".lower()
    return any(k in blob for k in config.KEYWORDS_OBRA)


def gravar_csv(leads):
    novo = not os.path.exists(ARQ_SAIDA)
    with open(ARQ_SAIDA, "a", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=config.CSV_HEADER)
        if novo:
            w.writeheader()
        for l in leads:
            w.writerow({k: l.get(k, "") for k in config.CSV_HEADER})


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--limite", type=int, default=60)
    ap.add_argument("--modelo", choices=["barato", "preciso"], default="barato")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--sem-noticias", action="store_true")
    ap.add_argument("--sem-pncp", action="store_true")
    ap.add_argument("--sem-diario", action="store_true")
    ap.add_argument("--sem-portais", action="store_true")
    args = ap.parse_args()
    modelo = config.MODELO_PRECISO if args.modelo == "preciso" else config.MODELO_BARATO

    print(f"\n=== Robô Prospecta Obras — {datetime.now():%d/%m/%Y %H:%M} ===")
    brutos = fontes.coletar_tudo(
        usar_noticias=not args.sem_noticias,
        usar_pncp=not args.sem_pncp,
        usar_diario=not args.sem_diario,
        usar_portais=not args.sem_portais,
    )
    candidatos = [i for i in brutos if relevante_por_keyword(i)]
    print(f"\n{len(brutos)} coletados → {len(candidatos)} passam no filtro de palavra-chave")

    if args.dry_run:
        for i in candidatos[:args.limite]:
            print(f"  • [{i['origem']}|{i.get('data','-')}] {i['titulo'][:80]}")
        print("\n(dry-run: nenhuma chamada de API feita)")
        return

    vistos = carregar_vistos()
    leads = []
    for i in candidatos[:args.limite]:
        lead = extrator.extrair_lead(i, modelo=modelo)
        if not lead or not lead["empresa"]:
            continue
        k = chave(lead)
        if k in vistos:
            continue
        vistos.add(k)
        leads.append(lead)
        dec = lead["contato"] if lead["contato"] != "A identificar" else "decisor a identificar"
        print(f"  ✓ {lead['empresa']} — {lead['tipoObra']} ({lead['uf']}) · {dec}")

    if leads:
        gravar_csv(leads)
        salvar_vistos(vistos)
        print(f"\n{len(leads)} leads novos em {os.path.basename(ARQ_SAIDA)} → importe no painel.")
    else:
        print("\nNenhum lead novo desta vez.")


if __name__ == "__main__":
    main()
