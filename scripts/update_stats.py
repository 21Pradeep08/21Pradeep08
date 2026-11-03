"""Fetch LeetCode + CodeChef stats and rewrite the badge blocks in README.md."""
import json, re, sys, urllib.request

LC_USER = "pradeep21o8"
CC_USER = "pradeep_21o8"
UA = {"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/124 Safari/537.36"}


def get(url, data=None, headers=None):
    req = urllib.request.Request(url, data=data, headers={**UA, **(headers or {})})
    with urllib.request.urlopen(req, timeout=30) as r:
        return r.read().decode("utf-8", "replace")


def leetcode():
    errs = []
    try:
        q = {"query": "query u($u:String!){matchedUser(username:$u){submitStatsGlobal{acSubmissionNum{difficulty count}}}}",
             "variables": {"u": LC_USER}}
        out = get("https://leetcode.com/graphql", json.dumps(q).encode(),
                  {"Content-Type": "application/json", "Referer": f"https://leetcode.com/u/{LC_USER}/"})
        rows = json.loads(out)["data"]["matchedUser"]["submitStatsGlobal"]["acSubmissionNum"]
        return next(r["count"] for r in rows if r["difficulty"] == "All")
    except Exception as e:
        errs.append(f"graphql: {e}")
    for url, key in (("https://leetcode-stats-api.herokuapp.com/" + LC_USER, "totalSolved"),
                     ("https://alfa-leetcode-api.onrender.com/" + LC_USER + "/solved", "solvedProblem")):
        try:
            return int(json.loads(get(url))[key])
        except Exception as e:
            errs.append(f"{url}: {e}")
    raise RuntimeError("; ".join(errs))


def codechef():
    html = get(f"https://www.codechef.com/users/{CC_USER}")
    rating = re.search(r'rating-number[^>]*>\s*(\d+)', html)
    solved = re.search(r'Total Problems Solved:\s*(\d+)', html)
    stars = re.search(r'rating-star[^>]*>(.*?)</div>', html, re.S)
    nstars = len(re.findall("★", stars.group(1))) if stars else 0
    return (int(rating.group(1)) if rating else None,
            int(solved.group(1)) if solved else None, nstars)


def badge(label, msg, color, logo):
    esc = lambda t: str(t).replace("-", "--").replace("_", "__").replace(" ", "_")
    return f"![{label}](https://img.shields.io/badge/{esc(label)}-{esc(msg)}-{color}?logo={logo}&logoColor=white)"


def main():
    parts = []
    try:
        parts.append(badge("LeetCode", f"{leetcode()} solved", "FFA116", "leetcode"))
    except Exception as e:
        print("leetcode failed:", e, file=sys.stderr)
    try:
        rating, solved, stars = codechef()
        if rating:
            parts.append(badge("CodeChef", f"{rating} rating" + (f" · {stars}★" if stars else ""), "5B4638", "codechef"))
        if solved:
            parts.append(badge("CodeChef", f"{solved} solved", "5B4638", "codechef"))
    except Exception as e:
        print("codechef failed:", e, file=sys.stderr)
    if not parts:
        sys.exit("no stats fetched; leaving README unchanged")
    block = "<!--STATS-->" + " ".join(parts) + "<!--/STATS-->"
    s = open("README.md", encoding="utf-8").read()
    new = re.sub(r"<!--STATS-->.*?<!--/STATS-->", lambda m: block, s, flags=re.S)
    if new != s:
        open("README.md", "w", encoding="utf-8").write(new)
        print("README updated")


main()
