import httpx

CANDIDATES = [
    # (source, slug)
    ("greenhouse", "palantir"), ("greenhouse", "palantirtechnologies"),
    ("greenhouse", "snowflakecomputing"), ("greenhouse", "snowflakeinc"),
    ("greenhouse", "personiogmbh"), ("greenhouse", "personio-1"),
    ("lever", "deepl"), ("greenhouse", "deeplco"), ("greenhouse", "deepl-gmbh"),
    ("ashby", "openai"), ("ashby", "palantir"),
    ("ashby", "personio"), ("ashby", "deepl"), ("ashby", "snowflake"),
]

with httpx.Client(timeout=15, follow_redirects=True) as c:
    ok = []
    for source, slug in CANDIDATES:
        try:
            if source == "greenhouse":
                url = f"https://boards-api.greenhouse.io/v1/boards/{slug}/jobs"
                r = c.get(url)
            elif source == "lever":
                r = c.get(f"https://api.lever.co/v0/postings/{slug}?mode=json")
            else:
                r = c.post(
                    f"https://api.ashbyhq.com/posting-api/job-board/{slug}",
                    json={},
                )
            status = r.status_code
            n = ""
            if status == 200:
                data = r.json()
                n = f" -> {len(data.get('jobs', data if isinstance(data, list) else []))} jobs"
                ok.append((source, slug))
            print(f"{status} {source}/{slug}{n}")
        except Exception as e:
            print(f"ERR {source}/{slug}: {type(e).__name__}")
