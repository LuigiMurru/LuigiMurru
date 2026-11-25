import json
import os
import re
import urllib.request
from collections import Counter
from datetime import datetime, timezone

TOKEN = os.environ["GH_TOKEN"]
YEAR = datetime.now(timezone.utc).year

QUERY = """
query {
  viewer {
    isHireable
    contributionsCollection {
      contributionCalendar {
        totalContributions
      }
    }
    repositories(first: 100, ownerAffiliations: OWNER) {
      nodes {
        isPrivate
        diskUsage
        primaryLanguage {
          name
        }
      }
    }
  }
}
"""

req = urllib.request.Request(
    "https://api.github.com/graphql",
    data=json.dumps({"query": QUERY}).encode("utf-8"),
    headers={
        "Authorization": f"Bearer {TOKEN}",
        "Content-Type": "application/json",
    },
)

with urllib.request.urlopen(req) as resp:
    data = json.loads(resp.read().decode("utf-8"))["data"]["viewer"]

repos = data["repositories"]["nodes"]
public_count = sum(1 for r in repos if not r["isPrivate"])
private_count = sum(1 for r in repos if r["isPrivate"])
total_kb = sum(r["diskUsage"] or 0 for r in repos)
storage = f"{total_kb / 1024:.1f} MB" if total_kb < 1024 * 1024 else f"{total_kb / (1024 * 1024):.2f} GB"
contribs = data["contributionsCollection"]["contributionCalendar"]["totalContributions"]
hire_line = "✅ Available for Hire" if data["isHireable"] else "🚫 Not Opted to Hire"

langs = Counter(r["primaryLanguage"]["name"] for r in repos if r["primaryLanguage"])
total_lang_repos = sum(langs.values())
top_lang = langs.most_common(1)[0][0] if langs else "Code"

lang_lines = []
for lang, count in langs.most_common(5):
    pct = (count / total_lang_repos) * 100
    filled = round((pct / 100) * 25)
    bar = "█" * filled + "░" * (25 - filled)
    repo_label = f"{count} {'repo' if count == 1 else 'repos'}"
    lang_lines.append(f"{lang:<25}{repo_label:<20}{bar}   {pct:05.2f} %")

now_str = datetime.now(timezone.utc).strftime("%d/%m/%Y %H:%M:%S UTC")

stats_block = (
    "<!--START_SECTION:waka-->\n"
    "```text\n"
    "🐱 My GitHub Data\n\n"
    f"    📦 {storage} Used in GitHub's Storage\n\n"
    f"    🏆 {contribs} Contributions in the Year {YEAR}\n\n"
    f"    {hire_line}\n\n"
    f"    📜 {public_count} Public Repositories\n\n"
    f"    🔑 {private_count} Private Repositories\n\n"
    f"I Mostly Code in {top_lang}\n\n"
    + "\n".join(lang_lines)
    + f"\n\nLast Updated on {now_str}\n"
    "```\n"
    "<!--END_SECTION:waka-->"
)

with open("README.md", "r", encoding="utf-8") as f:
    readme = f.read()

updated = re.sub(
    r"<!--START_SECTION:waka-->.*?<!--END_SECTION:waka-->",
    stats_block,
    readme,
    flags=re.DOTALL,
)

with open("README.md", "w", encoding="utf-8") as f:
    f.write(updated)
