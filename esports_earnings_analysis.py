"""
eSportsEarnings 电竞奖金数据分析 
==========================================================
数据来源: 天池
原始 CSV (放脚本同目录即可自动读取):
    highest_earning_players.csv   选手榜: PlayerId, NameFirst, NameLast,
                                  CurrentHandle, CountryCode, TotalUSDPrize, Game, Genre
    highest_earning_teams.csv     战队榜: TeamId, TeamName, TotalUSDPrize,
                                  TotalTournaments, Game, Genre  
    country-and-continent-codes-list.csv  国家-大洲映射表
"""
import os
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker

HERE = os.path.dirname(os.path.abspath(__file__))
OUT_DIR = os.path.join(HERE, "output_charts")
os.makedirs(OUT_DIR, exist_ok=True)
RNG = np.random.default_rng(42)

def _pick(df, candidates):
    """按候选列名(小写无下划线)取真实存在的列."""
    lut = {str(c).lower().replace("_", "").replace(" ", ""): c for c in df.columns}
    for cand in candidates:
        if cand in lut:
            return lut[cand]
    return None

def clean_players(df):
    handle = _pick(df, ["currenthandle", "handle", "tag"])
    fn, ln = _pick(df, ["namefirst"]), _pick(df, ["namelast"])
    win = _pick(df, ["totalusdprize", "totalusdwin", "prize", "earnings", "winnings"])
    cty = _pick(df, ["countrycode", "country", "nation"])
    if handle is not None:
        name = df[handle].astype(str).str.strip()
        if fn and ln:
            name = name.where(df[handle].notna(),
                              df[fn].astype(str).str.strip() + " " + df[ln].astype(str).str.strip())
    else:
        name = (df[fn].astype(str).str.strip() + " " + df[ln].astype(str).str.strip()) if fn and ln \
               else df[_pick(df, ["name", "player"])].astype(str).str.strip()
    out = pd.DataFrame({
        "name": name,
        "winnings_usd": pd.to_numeric(df[win], errors="coerce"),
        "country_code": df[cty].astype(str).str.strip().str.upper(),
        "game": df[_pick(df, ["game"])].astype(str).str.strip() if _pick(df, ["game"]) else pd.Series([""] * len(df)),
    })
    return out.dropna(subset=["winnings_usd"]).reset_index(drop=True)

def clean_teams(df):
    """战队榜没有国家列, 仅取队名/奖金/游戏."""
    team = _pick(df, ["teamname", "team", "name"])
    win = _pick(df, ["totalusdprize", "totalusdwin", "prize", "earnings", "winnings"])
    g = _pick(df, ["game"])
    out = pd.DataFrame({
        "team": df[team].astype(str).str.strip(),
        "winnings_usd": pd.to_numeric(df[win], errors="coerce"),
        "game": df[g].astype(str).str.strip() if g else pd.Series([""] * len(df)),
    })
    return out.dropna(subset=["winnings_usd"]).reset_index(drop=True)

def load_country_continent(path):
    cc = pd.read_csv(path)
    # 关键: 用两字码 Two_Letter_Country_Code 关联选手 CountryCode
    code = _pick(cc, ["twolettercountrycode", "twolettercode", "countrycode", "iso2", "code"])
    name = _pick(cc, ["countryname", "country"])
    cont = _pick(cc, ["continentname", "continent"])
    m = cc[[code, name, cont]].dropna(subset=[code]).copy()
    m.columns = ["country_code", "country_name", "continent"]
    m["country_code"] = m["country_code"].astype(str).str.strip().str.upper()
    return m.drop_duplicates("country_code")

def build_sample():
    countries = {"DK": "Europe", "SE": "Europe", "FI": "Europe", "FR": "Europe", "DE": "Europe",
        "RU": "Europe", "UA": "Europe", "US": "North America", "CA": "North America",
        "CN": "Asia", "KR": "Asia", "JP": "Asia", "BR": "South America", "AU": "Oceania"}
    names = {c: f"{k}_Rep" for k, c in enumerate(countries)}
    head = [("N0tail", "FI", 6952596.58), ("JerAx", "LV", 6470000.02), ("ana", "US", 6000411.96)]
    rows = [(nm, float(w), c) for nm, c, w in head]
    codes = list(countries.keys())
    w_e = np.array([2.0 if countries[c] == "Europe" else 1.0 for c in codes]); w_e /= w_e.sum()
    for i in range(160):
        c = str(RNG.choice(codes, p=w_e))
        rows.append((f"Player_{i+1:03d}", round(float(np.exp(RNG.normal(np.log(2.5e5), 0.9))), 2), c))
    players = pd.DataFrame(rows, columns=["name", "winnings_usd", "country_code", "game"])
    players["game"] = "Dota 2"
    teams = pd.DataFrame([(t, w, "Dota 2") for t, w in
                          [("OG", 33810636.13), ("Team Liquid", 22967431.10), ("Evil Geniuses", 19988670.62)]],
                         columns=["team", "winnings_usd", "game"])
    cc = pd.DataFrame([(k, names[k], countries[k]) for k in countries],
                      columns=["country_code", "country_name", "continent"])
    return players, teams, cc

def load_data():
    p = os.path.join(HERE, "highest_earning_players.csv")
    t = os.path.join(HERE, "highest_earning_teams.csv")
    c = os.path.join(HERE, "country-and-continent-codes-list.csv")
    if all(os.path.exists(f) for f in (p, t, c)):
        players = clean_players(pd.read_csv(p))
        teams = clean_teams(pd.read_csv(t))
        cc = load_country_continent(c)
        src = "REAL"
    else:
        players, teams, cc = build_sample(); src = "SAMPLE"
    return players, teams, cc, src

def analyze(players, teams, cc, src="SAMPLE"):
    # 国家维度仅选手榜有 country, 战队不参与
    players = players.merge(cc[["country_code", "country_name", "continent"]], on="country_code", how="left")
    n_players, n_teams = len(players), len(teams)
    total = players["winnings_usd"].sum() + teams["winnings_usd"].sum()
    top_players = players.nlargest(10, "winnings_usd")
    top_teams = teams.nlargest(10, "winnings_usd")
    country = (players.groupby(["country_code", "country_name"], dropna=False)["winnings_usd"]
               .sum().reset_index().sort_values("winnings_usd", ascending=False))
    cont = players.groupby("continent", dropna=False)["winnings_usd"].sum().sort_values(ascending=False)
    pp = players["winnings_usd"].sort_values(ascending=False)
    k = max(1, int(round(len(pp) * 0.01)))
    top1_share = pp.head(k).sum() / pp.sum()
    top50_share = players.nlargest(50, "winnings_usd")["winnings_usd"].sum() / players["winnings_usd"].sum()
    res = dict(src=src, n_players=n_players, n_teams=n_teams, total=total,
               top_players=top_players, top_teams=top_teams, country=country, cont=cont,
               top1_share=top1_share, top50_share=top50_share)

    # 图1 Top10 选手
    tp = top_players[["name", "winnings_usd"]].iloc[::-1]
    fig, ax = plt.subplots(figsize=(9, 4.8)); ax.barh(tp["name"], tp["winnings_usd"], color="#2E5E8C")
    ax.set_title("Top 10 Highest-Earning Esports Players (Individual Prize)"); ax.set_xlabel("Total Winnings (USD)")
    ax.xaxis.set_major_formatter(mticker.FuncFormatter(lambda v, _: f"${v/1e6:.1f}M"))
    for s in ("top", "right"): ax.spines[s].set_visible(False)
    fig.tight_layout(); fig.savefig(os.path.join(OUT_DIR, "fig1_top_players.png")); plt.close(fig)

    # 图2 Top10 战队
    tt = top_teams[["team", "winnings_usd"]].iloc[::-1]
    fig, ax = plt.subplots(figsize=(9, 4.8)); ax.barh(tt["team"], tt["winnings_usd"], color="#C0504D")
    ax.set_title("Top 10 Highest-Earning Esports Teams"); ax.set_xlabel("Total Winnings (USD)")
    ax.xaxis.set_major_formatter(mticker.FuncFormatter(lambda v, _: f"${v/1e6:.1f}M"))
    for s in ("top", "right"): ax.spines[s].set_visible(False)
    fig.tight_layout(); fig.savefig(os.path.join(OUT_DIR, "fig2_top_teams.png")); plt.close(fig)

    # 图3 Top10 国家 (仅选手榜奖金)
    tc = country.head(10)
    fig, ax = plt.subplots(figsize=(9, 4.8)); ax.bar(tc["country_code"].astype(str), tc["winnings_usd"], color="#6A8C3F")
    ax.set_title("Esports Winnings by Country (Players, ISO alpha-2)"); ax.set_ylabel("Total Winnings (USD)")
    ax.set_xlabel("Country Code"); ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda v, _: f"${v/1e6:.0f}M"))
    for s in ("top", "right"): ax.spines[s].set_visible(False)
    fig.tight_layout(); fig.savefig(os.path.join(OUT_DIR, "fig3_top_countries.png")); plt.close(fig)

    # 图4 大洲占比 (仅选手榜奖金)
    fig, ax = plt.subplots(figsize=(7.2, 4.8)); cc_ = cont[cont > 0]
    ap = lambda p: f"{p:.1f}%" if p >= 3 else ""
    w, _, _ = ax.pie(cc_.values, autopct=ap, startangle=90, wedgeprops=dict(width=0.42), pctdistance=0.78)
    ax.legend(w, [f"{i}  {v / cont.sum() * 100:.1f}%" for i, v in cc_.items()],
              loc="center left", bbox_to_anchor=(1.02, 0.5), frameon=False, fontsize=9)
    ax.set_title("Share of Esports Winnings by Continent (Players)")
    fig.tight_layout(); fig.savefig(os.path.join(OUT_DIR, "fig4_continent_share.png")); plt.close(fig)

    print(f"[source] {src}  players={n_players}  teams={n_teams}  total=${total:,.0f}")
    for i, v in cont.items():
        print(f"  {str(i):<16} ${v:,.0f}  ({v / cont.sum() * 100:.1f}%)")
    print(f"Top country (players) = {country.iloc[0]['country_code']} ${country.iloc[0]['winnings_usd']:,.0f}")
    print(f"Top1% players share={top1_share*100:.1f}%   Top50 players share={top50_share*100:.1f}%")
    return res

if __name__ == "__main__":
    p, t, c, s = load_data(); r = analyze(p, t, c, s); print("charts ->", OUT_DIR)
