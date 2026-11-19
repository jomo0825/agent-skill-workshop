"""個人一週助理：只使用 Python 標準函式庫，輸入 JSON，輸出 JSON 與 HTML。"""

import argparse
import base64
import html
import json
import sys
from datetime import date, datetime, time, timedelta, timezone
from pathlib import Path


TZ = timezone(timedelta(hours=8))
PRIORITY = {"high": 0, "medium": 1, "low": 2}
SKILL_DIR = Path(__file__).resolve().parents[1]


def text(value, field):
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field} 必須是非空字串")
    return value


def parse_dt(value):
    parsed = datetime.fromisoformat(text(value, "時間"))
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise ValueError("時間必須包含 UTC offset，例如 +08:00")
    return parsed.astimezone(TZ)


def validate(data):
    """先檢查格式，避免不完整資料被默默當成可用資訊。"""
    if not isinstance(data, dict):
        raise ValueError("輸入必須是 JSON 物件")
    text(data["person"], "person")
    prefs = data["preferences"]
    if not isinstance(prefs, dict):
        raise ValueError("preferences 必須是物件")
    days = prefs["workdays"]
    if not isinstance(days, list) or any(type(d) is not int or not 0 <= d <= 6 for d in days):
        raise ValueError("workdays 必須是 0 至 6 的整數清單")
    if len(set(days)) != len(days):
        raise ValueError("workdays 不可重複")
    windows = prefs["windows"]
    if not isinstance(windows, list):
        raise ValueError("windows 必須是時段清單")
    parsed_windows = []
    for pair in windows:
        if not isinstance(pair, list) or len(pair) != 2:
            raise ValueError("每個 window 必須有開始與結束時間")
        start, end = [time.fromisoformat(text(v, "window 時間")) for v in pair]
        if start.tzinfo or end.tzinfo or start >= end:
            raise ValueError("window 必須是同日且開始早於結束的本地時間")
        parsed_windows.append((start, end))
    parsed_windows.sort()
    if any(a[1] > b[0] for a, b in zip(parsed_windows, parsed_windows[1:])):
        raise ValueError("windows 不可重疊")
    for kind in ("events", "tasks"):
        if not isinstance(data[kind], list):
            raise ValueError(f"{kind} 必須是清單")
        ids = set()
        for item in data[kind]:
            if not isinstance(item, dict):
                raise ValueError(f"{kind} 每項必須是物件")
            identity = text(item["id"], f"{kind}.id")
            text(item["title"], f"{kind}.title")
            if identity in ids:
                raise ValueError(f"{kind} 出現重複 id：{identity}")
            ids.add(identity)
            if kind == "events":
                if parse_dt(item["start"]) >= parse_dt(item["end"]):
                    raise ValueError(f"行程 {identity} 的結束時間必須晚於開始")
            else:
                if type(item["minutes"]) is not int or item["minutes"] <= 0:
                    raise ValueError(f"待辦 {identity} 的 minutes 必須是正整數")
                if item["priority"] not in PRIORITY:
                    raise ValueError(f"待辦 {identity} 的 priority 必須是 high / medium / low")
                parse_dt(item["due"])
    return parsed_windows


def subtract(slots, busy_start, busy_end):
    """從空檔中扣掉一段占用時間；相鄰邊界不重疊。"""
    result = []
    for start, end in slots:
        if busy_end <= start or busy_start >= end:
            result.append((start, end))
        else:
            if start < busy_start:
                result.append((start, busy_start))
            if busy_end < end:
                result.append((busy_end, end))
    return result


def build_plan(data, week):
    """先扣固定行程，再依優先級／期限依序安排，不宣稱全域最佳化。"""
    windows = validate(data)
    day = date.fromisoformat(week)
    if day.weekday() != 0:
        raise ValueError("--week 必須是週一日期")
    week_start = datetime.combine(day, time.min, TZ)
    week_end = week_start + timedelta(days=7)
    events = []
    for event in data["events"]:
        start, end = parse_dt(event["start"]), parse_dt(event["end"])
        if start < week_end and end > week_start:
            events.append({"id": event["id"], "title": event["title"],
                           "start": start.isoformat(), "end": end.isoformat()})
    events.sort(key=lambda e: (e["start"], e["id"]))
    conflicts = []
    for index, first in enumerate(events):
        for second in events[index + 1:]:
            if first["start"] < second["end"] and second["start"] < first["end"]:
                conflicts.append({"first": first["id"], "second": second["id"],
                                  "titles": [first["title"], second["title"]]})
    slots = []
    for offset in range(7):
        current = day + timedelta(days=offset)
        if current.weekday() in data["preferences"]["workdays"]:
            slots.extend((datetime.combine(current, a, TZ), datetime.combine(current, b, TZ))
                         for a, b in windows)
    for event in events:
        slots = subtract(slots, parse_dt(event["start"]), parse_dt(event["end"]))
    scheduled, unscheduled = [], []
    tasks = sorted(data["tasks"], key=lambda t: (PRIORITY[t["priority"]], parse_dt(t["due"]), t["id"]))
    for task in tasks:
        due = parse_dt(task["due"])
        if due < week_start:
            unscheduled.append({**task, "reason": "期限早於本週，已逾期；請確認新期限"})
            continue
        duration = timedelta(minutes=task["minutes"])
        for start, end in slots:
            finish = start + duration
            if finish <= min(end, due):
                scheduled.append({**task, "start": start.isoformat(), "end": finish.isoformat()})
                slots = subtract(slots, start, finish)
                break
        else:
            unscheduled.append({**task, "reason": "本週期限前沒有足夠的連續空檔"})
    scheduled.sort(key=lambda t: (t["start"], t["id"]))
    return {"person": data["person"], "week": week, "timezone": "UTC+08:00",
            "events": events, "conflicts": conflicts, "scheduled": scheduled,
            "unscheduled": unscheduled,
            "summary": {"events": len(events), "conflicts": len(conflicts),
                        "scheduled": len(scheduled), "unscheduled": len(unscheduled)}}


def render_html(plan, banner):
    """所有使用者文字先跳脫；圖片嵌入，單一 HTML 可離線分享。"""
    esc = lambda value: html.escape(str(value), quote=True)
    image = base64.b64encode(banner.read_bytes()).decode("ascii")
    stats = plan["summary"]
    cards = "".join(f'<div class="stat"><strong>{stats[k]}</strong><span>{label}</span></div>'
                    for k, label in [("events", "固定行程"), ("scheduled", "已安排待辦"),
                                     ("conflicts", "行程衝突"), ("unscheduled", "待確認項目")])
    warnings = [f'固定行程衝突：{esc(c["titles"][0])} ／ {esc(c["titles"][1])}'
                for c in plan["conflicts"]]
    warnings += [f'{esc(t["title"])}：{esc(t["reason"])}' for t in plan["unscheduled"]]
    notices = "".join(f"<li>{warning}</li>" for warning in warnings) or "<li>本週沒有待確認項目。</li>"
    sections = []
    monday = date.fromisoformat(plan["week"])
    for offset in range(7):
        day = monday + timedelta(days=offset)
        start = datetime.combine(day, time.min, TZ)
        end = start + timedelta(days=1)
        rows = []
        for kind, items in [("固定", plan["events"]), ("建議", plan["scheduled"])]:
            for item in items:
                a, b = parse_dt(item["start"]), parse_dt(item["end"])
                if a < end and b > start:
                    clipped_a, clipped_b = max(a, start), min(b, end)
                    end_label = "24:00" if clipped_b == end else clipped_b.strftime("%H:%M")
                    label = f'{clipped_a:%H:%M}–{end_label}'
                    rows.append((a, f'<li><time>{label}</time><span class="tag">{kind}</span>'
                                    f'<span>{esc(item["title"])}</span></li>'))
        content = "".join(row for _, row in sorted(rows)) or '<li class="empty">尚無行程，留點時間給自己。</li>'
        weekday = "一二三四五六日"[day.weekday()]
        sections.append(f'<section class="day"><h3>{day:%m/%d} <small>週{weekday}</small></h3><ul>{content}</ul></section>')
    return f'''<!doctype html>
<html lang="zh-Hant"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(plan["person"])}的一週計畫</title>
<style>
:root{{color-scheme:light}}*{{box-sizing:border-box}}body{{margin:0;background:#f4f2ed;color:#253d3b;font-family:"Microsoft JhengHei",sans-serif;line-height:1.7}}
main{{max-width:1080px;margin:auto;padding:32px 24px}}.hero{{position:relative;border-radius:24px;overflow:hidden;background:#e8e7dd}}
.hero img{{display:block;width:100%;height:260px;object-fit:cover}}.heading{{padding:24px 30px;background:#fffcf4}}
h1{{font-size:32px;margin:0 0 8px}}p{{margin:4px 0}}.eyebrow{{font-size:13px;letter-spacing:2px;color:#537e76}}
.stats{{display:grid;grid-template-columns:repeat(4,1fr);gap:12px;margin:24px 0}}.stat{{padding:18px;background:white;border-radius:16px}}
.stat strong{{display:block;font-size:30px}}.stat span{{font-size:14px}}.notice{{background:#fff0dc;border:1px solid #ead2ad;border-radius:18px;padding:20px 24px}}
h2{{font-size:21px;margin:0 0 12px}}.notice ul{{margin:0;padding-left:24px}}.grid{{display:grid;grid-template-columns:1fr 1fr;gap:16px;margin-top:24px}}
.day{{background:white;border-radius:18px;padding:20px}}h3{{margin:0 0 12px}}small{{font-weight:normal;color:#65847b}}
.day ul{{list-style:none;padding:0;margin:0}}.day li{{display:flex;gap:10px;align-items:baseline;padding:10px 0;border-top:1px solid #edf0eb}}
time{{white-space:nowrap;font-size:13px}}.tag{{font-size:11px;background:#e9f2ec;border-radius:5px;padding:2px 5px;white-space:nowrap}}.empty{{color:#7b8d86}}
footer{{font-size:13px;color:#63766d;margin-top:24px}}@media(max-width:700px){{.grid{{grid-template-columns:1fr}}.stats{{grid-template-columns:1fr 1fr}}.hero img{{height:180px}}h1{{font-size:25px}}.day li{{flex-wrap:wrap}}}}
</style></head><body><main>
<header class="hero"><img src="data:image/png;base64,{image}" alt="AI 生成的個人助理桌面插畫"><div class="heading">
<p class="eyebrow">MY WEEK · PERSONAL ASSISTANT</p><h1>{esc(plan["person"])}的一週計畫</h1>
<p>{esc(plan["week"])} 起的一週 · UTC+08:00 · 模擬教學範例</p></div></header>
<div class="stats">{cards}</div><aside class="notice"><h2>先看這些提醒</h2><ul>{notices}</ul></aside>
<div class="grid">{"".join(sections)}</div><footer>待辦時間為建議，尚未寫入任何日曆。固定行程保留原樣；未計入交通時間。採優先級與期限的貪婪排程，結果不保證最佳。</footer>
</main></body></html>'''


def main(argv=None):
    parser = argparse.ArgumentParser(description="產生個人一週計畫（Python 3.10+）")
    parser.add_argument("--input", required=True, type=Path)
    parser.add_argument("--week", required=True, help="週一日期，YYYY-MM-DD")
    parser.add_argument("--out", required=True, type=Path)
    args = parser.parse_args(argv)
    try:
        data = json.loads(args.input.read_text(encoding="utf-8-sig"))
        plan = build_plan(data, args.week)
        page = render_html(plan, SKILL_DIR / "assets" / "banner.png")
        args.out.mkdir(parents=True, exist_ok=True)
        (args.out / "plan.json").write_text(json.dumps(plan, ensure_ascii=False, indent=2), encoding="utf-8")
        (args.out / "week-plan.html").write_text(page, encoding="utf-8")
    except (OSError, ValueError, KeyError, TypeError, OverflowError) as error:
        print(f"無法產生計畫：{error}", file=sys.stderr)
        return 2
    print(json.dumps({"output": str(args.out.resolve()), **plan["summary"]}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
