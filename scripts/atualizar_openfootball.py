#!/usr/bin/env python3
"""Atualiza dados/jogos.csv com os jogos do Brasileirão publicados pelo openfootball.

Fonte: https://github.com/openfootball/football.json (2026/br.1.json, domínio público).

Regras:
- Só mexe nas linhas com competicao = "Brasileirão"; as demais ficam como estão.
- Cada jogo é identificado pelo par mandante x visitante (único no turno e returno).
- Atualiza data, hora e placar quando o openfootball tiver a informação.
- Nunca apaga um placar já preenchido (se o openfootball ainda não tiver o jogo,
  um placar digitado à mão é mantido).
- Jogos marcados como adiados no openfootball recebem a observação correspondente.

Uso: python3 scripts/atualizar_openfootball.py [caminho/para/br.1.json]
Sem argumento, baixa o arquivo direto do GitHub.
"""
import csv, json, os, sys, urllib.request

URL = "https://raw.githubusercontent.com/openfootball/football.json/master/2026/br.1.json"
CSV = os.path.join(os.path.dirname(__file__), "..", "dados", "jogos.csv")
LIGA = "Brasileirão"
NOMES = {
    "Botafogo FR": "Botafogo", "CA Mineiro": "Atlético-MG", "CA Paranaense": "Athletico-PR",
    "CR Flamengo": "Flamengo", "CR Vasco da Gama": "Vasco da Gama", "Chapecoense AF": "Chapecoense",
    "Clube do Remo": "Remo", "Coritiba FBC": "Coritiba", "Cruzeiro EC": "Cruzeiro", "EC Bahia": "Bahia",
    "EC Vitória": "Vitória", "Fluminense FC": "Fluminense", "Grêmio FBPA": "Grêmio", "Mirassol FC": "Mirassol",
    "RB Bragantino": "Bragantino", "SC Corinthians Paulista": "Corinthians", "SC Internacional": "Internacional",
    "SE Palmeiras": "Palmeiras", "Santos FC": "Santos", "São Paulo FC": "São Paulo",
}


def carregar_fonte():
    if len(sys.argv) > 1:
        with open(sys.argv[1], encoding="utf-8") as f:
            return json.load(f)
    with urllib.request.urlopen(URL, timeout=60) as r:
        return json.load(r)


def main():
    fonte = carregar_fonte()["matches"]
    jogos = {}
    for m in fonte:
        a, b = NOMES.get(m["team1"]), NOMES.get(m["team2"])
        if not a or not b:
            sys.exit(f"Clube desconhecido no openfootball: {m['team1']} / {m['team2']}")
        s = m.get("score")
        ft = (s if isinstance(s, list) else s.get("ft")) if s else None
        jogos[(a, b)] = {"data": m["date"], "hora": m.get("time") or "", "ft": ft,
                         "adiado": m.get("status") == "postponed",
                         "fase": m["round"].replace("Matchday ", "") + "ª rodada"}

    with open(CSV, encoding="utf-8", newline="") as f:
        linhas = list(csv.DictReader(f))
    campos = list(linhas[0].keys())

    mudancas, vistos = [], set()
    for r in linhas:
        if r["competicao"] != LIGA:
            continue
        k = (r["mandante"], r["visitante"])
        j = jogos.get(k)
        if not j:
            print(f"Aviso: {k[0]} x {k[1]} não está no openfootball; linha mantida.")
            continue
        vistos.add(k)
        antes = dict(r)
        if j["data"] and j["data"] != r["data"]:
            r["data"] = j["data"]
        if j["hora"] and j["hora"] != r["hora"]:
            r["hora"] = j["hora"]
        if j["ft"] is not None:
            r["gols_mandante"], r["gols_visitante"] = str(j["ft"][0]), str(j["ft"][1])
            if "adiad" in r["observacao"].lower() and "nova data" in r["observacao"].lower():
                r["observacao"] = ""
        elif j["adiado"] and r["gols_mandante"] == "" and "adiad" not in r["observacao"].lower():
            r["observacao"] = "Adiado; nova data a definir"
        if r != antes:
            if r["gols_mandante"] != antes["gols_mandante"] or r["gols_visitante"] != antes["gols_visitante"]:
                mudancas.append(f"{k[0]} {r['gols_mandante']}x{r['gols_visitante']} {k[1]}")
            else:
                mudancas.append(f"{k[0]} x {k[1]}: data/hora {r['data']} {r['hora']}".strip())

    faltando = set(jogos) - vistos
    for a, b in sorted(faltando):
        print(f"Aviso: {a} x {b} está no openfootball mas não na base.")

    n_liga = sum(1 for r in linhas if r["competicao"] == LIGA)
    if n_liga != 380:
        sys.exit(f"Erro: a base tem {n_liga} jogos do Brasileirão (esperado 380).")

    linhas.sort(key=lambda r: (r["data"], r["hora"], r["competicao"], r["mandante"]))
    with open(CSV, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=campos)
        w.writeheader()
        w.writerows(linhas)

    com_placar = sum(1 for m in fonte if m.get("score"))
    ultimo = max((m["date"] for m in fonte if m.get("score")), default="-")
    print(f"openfootball: {com_placar} jogos com placar, último em {ultimo}.")
    print(f"{len(mudancas)} mudança(s):" if mudancas else "Nenhuma mudança.")
    for m in mudancas:
        print(" -", m)


if __name__ == "__main__":
    main()
