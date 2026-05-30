#!/usr/bin/env python3
"""SFC教員辞典Markdownをパースしてdata.jsを生成"""

import re
import json

MD_PATH = "/Users/watanabeeita/Desktop/活動/AO受験/研究/03_参考資料/SFC教員/sfc_faculty_dictionary.md"
OUT_PATH = "public/data.js"

def parse_md(path):
    with open(path, encoding="utf-8") as f:
        text = f.read()

    # ランキングテーブルから順位とおすすめ度を抽出
    ranking = {}
    for m in re.finditer(r"\| #(\d+) \| (★+[☆]*) \| (.+?) \|", text):
        rank, stars, name = m.group(1), m.group(2), m.group(3).strip()
        ranking[name] = {"rank": int(rank), "stars": stars}

    # 全教員一覧セクション以降を対象にする
    all_section = text.split("## 全教員一覧（128名）", 1)
    if len(all_section) < 2:
        raise ValueError("全教員一覧セクションが見つかりません")
    body = all_section[1]

    # ### 氏名 で分割（テーマ別グループの ### は除外済み）
    sections = re.split(r"\n### ", body)
    sections = [s for s in sections if s.strip()]

    professors = []
    for sec in sections:
        lines = sec.strip().split("\n")
        name = lines[0].strip()

        # 推薦情報
        rank_info = ranking.get(name, {})
        rank_num = rank_info.get("rank")
        stars = rank_info.get("stars", "")

        # 推薦行から取得（Markdownにも埋め込まれている場合）
        rec_match = re.search(r"\*\*推薦 #(\d+)\*\* / おすすめ度: (★+[☆]*)", sec)
        if rec_match:
            rank_num = int(rec_match.group(1))
            stars = rec_match.group(2)

        # 写真URL
        img_match = re.search(r"!\[.*?\]\((https?://[^\)]+)\)", sec)
        img = img_match.group(1) if img_match else ""

        def extract_field(label):
            m = re.search(rf"\*\*{re.escape(label)}\*\* (.+?)(?=\n\n|\n\*\*|\Z)", sec, re.DOTALL)
            return m.group(1).strip() if m else ""

        def extract_list(label):
            m = re.search(rf"\*\*{re.escape(label)}\*\*\n((?:- .+\n?)+)", sec)
            if not m:
                return []
            items = re.findall(r"- (.+)", m.group(1))
            return [i.strip() for i in items]

        position = extract_field("所属・職位:")
        expertise = extract_field("専門分野:")
        research = extract_field("研究紹介:")
        theme_connection = extract_field("俺のテーマとの接点:")
        analysis = extract_field("分析:")
        books = extract_list("著書:")
        papers = extract_list("主要論文（最新5件）:")
        awards = extract_list("受賞:")
        grants = extract_list("科研費・研究プロジェクト:")

        profile_match = re.search(r"\*\*プロフィール:\*\* \[.+?\]\((.+?)\)", sec)
        kris_match = re.search(r"\*\*研究者DB:\*\* \[.+?\]\((.+?)\)", sec)
        profile_url = profile_match.group(1) if profile_match else ""
        kris_url = kris_match.group(1) if kris_match else ""

        professors.append({
            "name": name,
            "rank": rank_num,
            "stars": stars,
            "img": img,
            "position": position,
            "expertise": expertise,
            "research": research,
            "themeConnection": theme_connection,
            "analysis": analysis,
            "books": books,
            "papers": papers,
            "awards": awards,
            "grants": grants,
            "profileUrl": profile_url,
            "krisUrl": kris_url,
        })

    return professors

def main():
    profs = parse_md(MD_PATH)
    # rankがある教授を先に、ない教授はあいうえお順
    profs_with_rank = [p for p in profs if p["rank"] is not None]
    profs_without_rank = [p for p in profs if p["rank"] is None]
    profs_with_rank.sort(key=lambda x: x["rank"])

    all_profs = profs
    json_str = json.dumps(all_profs, ensure_ascii=False, indent=2)

    with open(OUT_PATH, "w", encoding="utf-8") as f:
        f.write(f"const FACULTY_DATA = {json_str};\n")

    print(f"生成完了: {len(all_profs)}名 → {OUT_PATH}")

if __name__ == "__main__":
    main()
