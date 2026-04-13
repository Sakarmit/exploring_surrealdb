"""
parsers/kg_parser.py
Parses course dataset CSV into structured JSON for SurrealDB ingestion.
"""

import csv
import re
from pathlib import Path
import hashlib

# Helper Fuctions
def stable_id(prefix, value):
    """Standardized hashing"""
    hash_part = hashlib.md5(value.encode()).hexdigest()[:10]
    clean_hash = re.sub(r'[^a-zA-Z0-9_]', '_', hash_part)
    return f"{prefix}:{clean_hash}"


def clean_id(val):
    return re.sub(r'[^a-zA-Z0-9_]', '_', val)


def clean_str(val):
    if val is None:
        return None
    val = val.strip()
    return val if val else None


def to_int(val):
    return int(val) if val is not None else None


def to_float(val):
    try:
        return float(val) if val is not None else None
    except ValueError:
        return None
    

def safe_default(val, default):
    return val if val is not None else default


def parse_list(val, sep="|"):
    if not val:
        return []
    return [v.strip() for v in val.split(sep) if v.strip()]


def parse_nested_list(val):
    """Handles 'en, sp | fr' → ['en','sp','fr']"""
    result = []
    for chunk in parse_list(val, "|"):
        result.extend(parse_list(chunk, ","))
    return result


def parse_weeks(val):
    """parse n weeks to n"""
    if val is None:
        return None

    val = str(val).strip().lower()

    if not val:
        return None

    m = re.search(r'(\d+)', val)
    if m:
        return int(m.group(1))

    return None


def load_csv(path):
    """Loads csv and converts to raw rows of data"""
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(path)

    with open(path, newline="", encoding="utf-8-sig") as f:
        raw = list(csv.DictReader(f))
        raw.append({"file_source":path})
        for row in raw:
            row["file_source"] = str(path)
        return raw


def normalize(rows):
    """Normalizes data such that only the columns wanted are stored.
    Returns list of normalized data"""

    normalized = []
    
    for i, row in enumerate(rows):
        course_id = clean_id(row.get("course_id") or f"row{i}")

        normalized.append({
            "id": f"course:{course_id}",
            "source": row.get("file_source"),

            "name": clean_str(row.get("xlsx_name")),
            "description": clean_str(row.get("scraped_description")),
            "url": clean_str(row.get("url")),

            "difficulty": clean_str(row.get("level_xlsx")),
            "rating": to_float(row.get("rating_xlsx")),
            "hours": to_float(row.get("hours")),
            "weeks": parse_weeks(row.get("duration_weeks")),

            "domain": clean_str(row.get("domain")),
            "subdomain": clean_str(row.get("subdomain")),

            "tools": parse_list(row.get("final_tools")),
            "objectives": parse_list(row.get("learning_objectives")),
            "languages": parse_nested_list(row.get("subtitle_languages")),

            "instructors": parse_list(row.get("instructor_names")),
            "instructor_titles": parse_list(row.get("instructor_titles")),
            "instructor_bios": parse_list(row.get("instructor_bios")),

            "modules": parse_list(row.get("module_summaries")),
            "videos": parse_list(row.get("all_video_titles")),
            "readings": parse_list(row.get("all_reading_titles")),
            "assignments": parse_list(row.get("all_assignment_titles")),
            "discussions": parse_list(row.get("all_discussion_titles")),
        })

    return normalized


def parse_module_summary(text):
    """parses nested module data"""
    video_count = 0
    minutes = 0.0
    assignment_count = 0

    for seg in text.split(","):
        if m := re.search(r'(\d+)\s*videos?', seg, re.I):
            video_count = int(m.group(1))
        if m := re.search(r'(\d+(?:\.\d+)?)\s*min', seg, re.I):
            minutes = float(m.group(1))
        if m := re.search(r'(\d+)\s*assignments?', seg, re.I):
            assignment_count += int(m.group(1))        
        if m := re.search(r'(\d+)\s*readings?', seg, re.I):
            assignment_count += int(m.group(1)) 
                   

    return video_count, minutes, assignment_count


def build_graph(records):
    """Seperate data into tables"""
    tables = {
        "course": {},
        "subject": {},
        "tool": {},
        "language": {},
        "instructor": {},
        "module": {},
        "video": {},
        "lecture": {},
        "assignment": {},
        "discussion": {},
    }

    relations = {
        "belongs_to": [],
        "uses": [],
        "taught_in": [],
        "taught_by": [],
        "contains": [],
        "includes": [],
    }

    def relate(rel, src, dst):
        relations[rel].append({
            "id": stable_id("rel", f"{src}_{dst}"),
            "in": src,
            "out": dst
        })

    for r in records:
        cid = r["id"]
        
        tables["course"][cid] = {
            "id": cid,
            "source": r["source"],
            "name": r["name"],
            "description": r["description"],
            "url": r["url"],
            "difficulty": r["difficulty"],
            "rating": r["rating"],
            "hours": r["hours"],
            "weeks": safe_default(r["weeks"], 0),
            "objective": r["objectives"],
            "certificate": False,
        }

        # Subject table
        if r["domain"] and r["subdomain"]:
            sid = stable_id("subject", r["domain"] + r["subdomain"])
            tables["subject"][sid] = {
                "id": sid,
                "domain": r["domain"],
                "subdomain": r["subdomain"]
            }
            relate("belongs_to", cid, sid)
            
        # Tools table
        for t in r["tools"]:
            tid = stable_id("tool", t)
            tables["tool"][tid] = {"id": tid, "name": t}
            relate("uses", cid, tid)

        # Languages table
        for lang in r["languages"]:
            lid = stable_id("language", lang)
            tables["language"][lid] = {"id": lid, "shorthand": lang}
            relate("taught_in", cid, lid)

        # Instructions table
        for i, name in enumerate(r["instructors"]):
            iid = stable_id("instructor", name)
            tables["instructor"][iid] = {
                "id": iid,
                "name": name,
                "title": r["instructor_titles"][i] if i < len(r["instructor_titles"]) else None,
                "bio": r["instructor_bios"][i] if i < len(r["instructor_bios"]) else None,
            }
            relate("taught_by", cid, iid)

        # Modules table
        for i, m in enumerate(r["modules"]):
            course_id_clean = cid.split(":")[1]
            mid = f"module:{course_id_clean}_{i}"
            vc, mins, ac = parse_module_summary(m)

            tables["module"][mid] = {
                "id": mid,
                "description": m,
                "video_count": vc,
                "minutes": mins,
                "assignment_count": ac
            }
            relate("contains", cid, mid)

        # videos table
        for v in r["videos"]:
            vid = stable_id("video", v)
            tables["video"][vid] = {
                "id": vid,
                "name": v,
                "source": r["source"],
                "format": "video"
            }

        # lectures table
        for lec in r["readings"]:
            lid = stable_id("lecture", lec)
            tables["lecture"][lid] = {
                "id": lid,
                "type": "reading",
                "title": lec,
                "content": lec,
                "source": r['source']
            }
            relate("includes", cid, lid)

        # assignments table
        for a in r["assignments"]:
            aid = stable_id("assignment", a)
            tables["assignment"][aid] = {
                "id": aid,
                "type": "assignment",
                "title": a,
                "source": r["source"],
                "content": a
            }

        # discussions table
        for d in r["discussions"]:
            did = stable_id("discussion", d)
            tables["discussion"][did] = {
                "id": did,
                "title": d,
                "message": d
            }

    # Convert dicts → lists
    tables = {k: list(v.values()) for k, v in tables.items()}

    return {
        "tables": tables,
        "relations": relations
    }


def parse_kg(path, limit=None):
    raw = load_csv(path)
    normalized = normalize(raw)
    graph = build_graph(normalized)

    if limit:
        # Limit tables
        graph["tables"] = {
            k: v[:limit] for k, v in graph["tables"].items()
        }

        # Limit relations
        graph["relations"] = {
            k: v[:limit] for k, v in graph["relations"].items()
        }

    return graph


def debug_preview(result, n=2):    
    with open("debug.txt", "w", encoding="utf-8") as f:
        print("\n" + "="*60,file=f)
        print("TABLE PREVIEW",file=f)
        print("="*60,file=f)

        for table_name, records in result["tables"].items():
            print(f"\n--- {table_name.upper()} ({len(records)} records) ---",file=f)
            
            if not records:
                print("  [EMPTY]",file=f)
                continue

            for i, rec in enumerate(records[:n]):
                print(f"\n  [{i}]",file=f)
                for k, v in rec.items():
                    print(f"    {k}: {v}",file=f)

        print("\n" + "="*60,file=f)
        print("RELATION PREVIEW",file=f)
        print("="*60,file=f)

        for rel_name, records in result["relations"].items():
            print(f"\n--- {rel_name.upper()} ({len(records)} relations) ---",file=f)

            if not records:
                print("  [EMPTY]",file=f)
                continue

            for i, rec in enumerate(records[:n]):
                print(f"\n  [{i}]",file=f)
                for k, v in rec.items():
                    print(f"    {k}: {v}",file=f)


if __name__ == "__main__":    
    import sys
    import json

    path = sys.argv[1] if len(sys.argv) > 1 else "dataset/knowledge_graph/cs_dataset.csv"
    
    result = parse_kg(path)

    # debug_preview(result, n=2)

    print(json.dumps({
        "tables": {k: len(v) for k, v in result["tables"].items()},
        "relations": {k: len(v) for k, v in result["relations"].items()}
    }, indent=2))