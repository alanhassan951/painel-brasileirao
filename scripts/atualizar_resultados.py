#!/usr/bin/env python3
"""Atualiza dados/jogos.csv com os jogos do Brasileirão a partir da API pública da ESPN.

Fonte: https://site.api.espn.com/apis/site/v2/sports/soccer/bra.1/scoreboard
(API pública, sem chave de acesso).

Regras:
- Só mexe nas linhas com competicao = "Brasileirão"; as demais ficam como estão.
- Cada jogo é identificado pelo par mandante x visitante (único no turno e returno).
- Preenche o placar de jogos encerrados que ainda estão sem placar na base.
- Nunca apaga nem sobrescreve um placar já preenchido. Se a API discordar de um
  placar existente, apenas avisa.
- Atualiza data e horário (convertidos para o horário de Brasília) de jogos ainda
  não disputados.
- Jogos adiados recebem a observação "Adiado; nova data a definir".
- Se a API discordar de muitos placares já conhecidos, o script para sem gravar nada
  (sinal de que a fonte mudou ou está com problema).

Uso:
  python3 scripts/atualizar_resultados.py               # consulta a API
  python3 scripts/atualizar_resultados.py arquivo.json  # usa um JSON salvo (testes)
"""
import csv
import datetime as dt
import json
import os
import sys
import time
import unicodedata
import urllib.request

API = "https://site.api.espn.com/apis/site/v2/sports/soccer/bra.1/scoreboard"
CSV = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "dados", "jogos.csv")
LIGA = "Brasileirão"
TEMPORADA = (dt.date(2026, 1, 20), dt.date(2026, 12, 15))
BRT = dt.timezone(dt.timedelta(hours=-3))  # Brasil sem horário de verão desde 2019

CLUBES = ["Athletico-PR", "Atlético-MG", "Bahia", "Botafogo", "Bragantino", "Chapecoense",
          "Corinthians", "Coritiba", "Cruzeiro", "Flamengo", "Fluminense", "Grêmio",
          "Internacional", "Mirassol", "Palmeiras", "Remo", "Santos", "São Paulo",
          "Vasco da Gama", "Vitória"]
APELIDOS = {
    "athletico paranaense": "Athletico-PR", "athletico-pr": "Athletico-PR", "athletico pr": "Athletico-PR",
    "atletico paranaense": "Athletico-PR", "cap": "Athletico-PR",
    "atletico-mg": "Atlético-MG", "atletico mg": "Atlético-MG", "atletico mineiro": "Atlético-MG", "cam": "Atlético-MG",
    "red bull bragantino": "Bragantino", "rb bragantino": "Bragantino", "bragantino": "Bragantino",
    "vasco": "Vasco da Gama", "clube do remo": "Remo",
}


def norm(s):
    s = unicodedata.normalize("NFD", s or "").encode("ascii", "ignore").decode()
    return " ".join(s.lower().replace(".", " ").split())


INDICE = {norm(c): c for c in CLUBES}
INDICE.update({norm(k): v for k, v in APELIDOS.items()})


def clube(team):
    for campo in ("displayName", "shortDisplayName", "name", "location", "abbreviation"):
        nome = INDICE.get(norm(team.get(campo, "")))
        if nome:
            return nome
    return None


def baixar(url):
    req = urllib.request.Request(url, headers={"User-Agent": "painel-brasileirao/1.0"})
    for tentativa in range(3):
        try:
            with urllib.request.urlopen(req, timeout=30) as r:
                return json.load(r)
        except Exception as e:  # noqa: BLE001
            if tentativa == 2:
                raise
            print(f"Falha ao acessar a API ({e}); tentando de novo...")
            time.sleep(3)


def eventos_da_api():
    ini, fim = TEMPORADA
    try:
        eventos = baixar(f"{API}?dates={ini:%Y%m%d}-{fim:%Y%m%d}&limit=1000").get("events", [])
    except Exception as e:  # noqa: BLE001
        print(f"Consulta por intervalo não aceita ({e}).")
        eventos = []
    if len(eventos) >= 300:
        return eventos
    # A API nem sempre aceita intervalos longos: consulta dia a dia.
    print(f"Consulta por intervalo trouxe {len(eventos)} jogos; consultando dia a dia...")
    vistos, eventos = set(), []
    d = ini
    falhas = 0
    while d <= fim:
        try:
            dia = baixar(f"{API}?dates={d:%Y%m%d}").get("events", [])
        except Exception as e:  # noqa: BLE001
            falhas += 1
            print(f"Aviso: falha ao consultar {d:%d/%m} ({e}).")
            if falhas > 10:
                sys.exit("Erro: muitas falhas ao consultar a API. Nada foi gravado.")
            dia = []
        for ev in dia:
            if ev.get("id") not in vistos:
                vistos.add(ev.get("id"))
                eventos.append(ev)
        d += dt.timedelta(days=1)
        time.sleep(0.15)
    return eventos


def ler_evento(ev):
    comp = (ev.get("competitions") or [{}])[0]
    times = {c.get("homeAway"): c for c in comp.get("competitors", [])}
    if "home" not in times or "away" not in times:
        return None
    casa, fora = clube(times["home"].get("team", {})), clube(times["away"].get("team", {}))
    if not casa or not fora:
        nomes = [times[k].get("team", {}).get("displayName") for k in ("home", "away")]
        sys.exit(f"Erro: clube não reconhecido na API: {nomes}. Atualize APELIDOS no script.")
    st = (ev.get("status") or comp.get("status") or {}).get("type", {})
    quando = dt.datetime.fromisoformat(ev["date"].replace("Z", "+00:00")).astimezone(BRT)

    def gols(c):
        try:
            return int(float(c.get("score")))
        except (TypeError, ValueError):
            return None

    encerrado = st.get("state") == "post" and st.get("completed") is True
    nome_status = (st.get("name") or "").upper()
    return {
        "casa": casa, "fora": fora,
        "data": quando.strftime("%Y-%m-%d"), "hora": quando.strftime("%H:%M"),
        "gm": gols(times["home"]) if encerrado else None,
        "gv": gols(times["away"]) if encerrado else None,
        "adiado": "POSTPONED" in nome_status or "SUSPENDED" in nome_status or "CANCELED" in nome_status,
        "hora_definida": ev.get("timeValid") is not False and comp.get("timeValid") is not False,
    }


def main():
    if len(sys.argv) > 1:
        with open(sys.argv[1], encoding="utf-8") as f:
            eventos = json.load(f).get("events", [])
    else:
        eventos = eventos_da_api()
    api = {}
    for ev in eventos:
        j = ler_evento(ev)
        if j:
            api[(j["casa"], j["fora"])] = j
    # Rodadas ainda sem horário definido vêm com o mesmo horário provisório para todos os jogos
    # do dia; nesse caso o horário é tratado como "a definir".
    por_dia = {}
    for j in api.values():
        if j["gm"] is None:
            por_dia.setdefault(j["data"], []).append(j)
    for jogos_do_dia in por_dia.values():
        if len(jogos_do_dia) >= 5 and len({j["hora"] for j in jogos_do_dia}) == 1:
            for j in jogos_do_dia:
                j["hora_definida"] = False
    print(f"API: {len(api)} jogos do Brasileirão, {sum(1 for j in api.values() if j['gm'] is not None)} encerrados.")
    if len(api) < 300:
        sys.exit(f"Erro: a API trouxe só {len(api)} jogos (esperado perto de 380). Nada foi gravado.")

    with open(CSV, encoding="utf-8", newline="") as f:
        linhas = list(csv.DictReader(f))
    campos = list(linhas[0].keys())
    hoje = dt.datetime.now(BRT).strftime("%Y-%m-%d")

    conferidos = divergentes = 0
    mudancas, avisos = [], []
    for r in linhas:
        if r["competicao"] != LIGA:
            continue
        j = api.get((r["mandante"], r["visitante"]))
        if not j:
            continue
        tem_placar = r["gols_mandante"] != "" and r["gols_visitante"] != ""
        if tem_placar:
            if j["gm"] is not None:
                conferidos += 1
                if (int(r["gols_mandante"]), int(r["gols_visitante"])) != (j["gm"], j["gv"]):
                    divergentes += 1
                    avisos.append(f"{r['mandante']} x {r['visitante']}: base {r['gols_mandante']}x{r['gols_visitante']}, "
                                  f"API {j['gm']}x{j['gv']} (mantido o da base)")
            continue
        if j["gm"] is not None:
            r["gols_mandante"], r["gols_visitante"] = str(j["gm"]), str(j["gv"])
            r["data"], r["hora"] = j["data"], j["hora"]
            if "adiad" in r["observacao"].lower() and "nova data" in r["observacao"].lower():
                r["observacao"] = ""
            mudancas.append(f"{r['mandante']} {j['gm']}x{j['gv']} {r['visitante']}")
        elif j["adiado"]:
            if "adiad" not in r["observacao"].lower():
                r["observacao"] = "Adiado; nova data a definir"
                mudancas.append(f"{r['mandante']} x {r['visitante']}: adiado")
        elif j["data"] >= hoje or r["data"] < hoje:
            nova_hora = j["hora"] if j["hora_definida"] else ""
            if (j["data"], nova_hora) != (r["data"], r["hora"]):
                mudancas.append(f"{r['mandante']} x {r['visitante']}: {r['data']} {r['hora']} -> {j['data']} {nova_hora}".rstrip())
                r["data"], r["hora"] = j["data"], nova_hora
                if "adiad" in r["observacao"].lower() and "nova data" in r["observacao"].lower():
                    r["observacao"] = r["observacao"].replace("Adiado; nova data a definir", "Jogo adiado").strip()

    for a in avisos:
        print("Aviso:", a)
    if conferidos >= 20 and divergentes > conferidos * 0.1:
        sys.exit(f"Erro: a API discorda de {divergentes} de {conferidos} placares já conhecidos. Nada foi gravado.")

    n_liga = sum(1 for r in linhas if r["competicao"] == LIGA)
    if n_liga != 380:
        sys.exit(f"Erro: a base tem {n_liga} jogos do Brasileirão (esperado 380). Nada foi gravado.")
    for r in linhas:
        for c in ("gols_mandante", "gols_visitante"):
            if r[c] != "" and (not r[c].isdigit()):
                sys.exit(f"Erro: placar inválido em {r['mandante']} x {r['visitante']}. Nada foi gravado.")

    linhas.sort(key=lambda r: (r["data"], r["hora"], r["competicao"], r["mandante"]))
    with open(CSV, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=campos)
        w.writeheader()
        w.writerows(linhas)

    print(f"Placares conferidos com a base: {conferidos} ({divergentes} divergentes).")
    print(f"{len(mudancas)} mudança(s):" if mudancas else "Nenhuma mudança.")
    for m in mudancas:
        print(" -", m)
    resumo = os.environ.get("GITHUB_STEP_SUMMARY")
    if resumo:
        with open(resumo, "a", encoding="utf-8") as f:
            f.write(f"### Atualização de resultados\n\n{len(api)} jogos na API; {conferidos} placares conferidos "
                    f"({divergentes} divergentes).\n\n")
            f.write("\n".join(f"- {m}" for m in mudancas) or "Nenhuma mudança.")
            f.write("\n")


if __name__ == "__main__":
    main()
