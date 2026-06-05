# Robô Prospecta Obras — Civil Obras

Backend leve que **descobre oportunidades de obra do agro/indústria** monitorando
sinais públicos, qualifica cada uma com a API da Claude e gera um **CSV pronto
para importar no app Prospecta Obras**.

## Como funciona (arquitetura)

```
   FONTES PÚBLICAS                 FILTRO            INTELIGÊNCIA            SAÍDA
 ┌────────────────────┐        ┌───────────┐      ┌──────────────┐     ┌──────────────┐
 │ Google News (RSS)  │──┐     │ palavra-  │      │  API Claude  │     │ leads_novos  │
 │ anúncios/expansão  │  │     │  chave de │      │  extrai e    │     │    .csv      │
 ├────────────────────┤  ├───▶ │   obra    │────▶ │  classifica  │───▶ │ (formato do  │
 │ Portais ambientais │  │     │ (de graça)│      │  em JSON     │     │    app)      │
 │ IMA/IAT/FEPAM/...  │──┘     └───────────┘      └──────┬───────┘     └──────┬───────┘
 └────────────────────┘                                 │ dedupe              │ importar
                                                    vistos.json          no app (Leads)
```

1. **Coleta** (`fontes.py`) — TRÊS fontes funcionam de imediato:
   - **Google News RSS** (anúncios de expansão), agora com a DATA de publicação;
   - **PNCP** (`pncp.gov.br/api/consulta` — licitações/editais de obra, API pública sem login).
   - **Querido Diário** (`api.queridodiario.ok.org.br` — Diários Oficiais, onde
     licenças e obras públicas são publicadas; tag "Licença Ambiental").
   Os portais estaduais (IMA/IAT/FEPAM…) seguem como adaptadores configuráveis.
2. **Filtro barato** — só o que contém palavra de obra (silo, ração, secador, moega…)
   segue adiante, para não gastar API à toa.
3. **Extração** (`extrator.py`) — a Claude lê cada item e devolve um lead estruturado
   (empresa, UF, município, tipo de obra, valor, **decisor e cargo** se citados na
   fonte, e a **data**) **ou descarta** se não for obra. Nunca inventa nome/telefone.
   É isso que deixa o robô resistente à variação de formato entre fontes.
4. **Dedupe** — `vistos.json` evita repetir o mesmo alvo.
5. **Saída** — `leads_novos.csv` no formato exato do app.

## Setup (5 min)

```bash
pip install -r requirements.txt
cp .env.example .env        # cole sua ANTHROPIC_API_KEY
```

## Rodar

```bash
python robo.py --dry-run     # ver o que coletaria (sem gastar API)
python robo.py               # coleta + qualifica + gera leads_novos.csv
python robo.py --modelo preciso --limite 30
```

Depois importe `leads_novos.csv` no app: **Leads → Importar (CSV)**.

## Automatizar (sem servidor)

O arquivo `.github/workflows/agendador.yml` roda o robô **toda segunda às 8h**, de
graça, no GitHub Actions. IMPORTANTE: suba para o repositório os **arquivos de
dentro** da pasta `robo-prospecta/` (robo.py, config.py, requirements.txt e a pasta
.github na RAIZ do repositório — não dentro de uma subpasta).

1. Crie um repositório no GitHub e envie esses arquivos.
2. Em Settings → Secrets and variables → Actions, crie o secret `ANTHROPIC_API_KEY`.
3. Em Actions, habilite os workflows. Pronto: o CSV fica na aba Actions a cada run.

Rodar na hora: aba Actions → "Robô Prospecta Obras" → Run workflow.

## Ligar os portais de licenciamento ambiental

Cada órgão tem site próprio. Em `config.PORTAIS_AMBIENTAIS`:
1. Abra a página de **consulta de processos/licenças** do órgão.
2. Copie a URL de busca para `url_busca`.
3. Inspecione o HTML e ponha o seletor das linhas de resultado em `item_selector`.
4. Mude `"ativo": True`.

O adaptador genérico extrai o texto desses blocos e a Claude faz o resto.
Sinal mais valioso: pedidos de **LP/LI** para "unidade armazenadora", "fábrica de
ração" e "secador" — obra quase certa entrando no funil.

## Custo

O filtro de palavra-chave roda de graça; só itens promissores vão à API.
Extração usa **claude-haiku-4-5** (modelo rápido e econômico) por padrão — cada item
é uma chamada curta. Centenas de itens por semana custam poucos centavos de dólar.
Use `--modelo preciso` (claude-sonnet-4-6) só quando precisar de mais acerto.
