import httpx

with httpx.Client(timeout=15, follow_redirects=True) as c:
    # 1) does plain GET work on ashby?
    try:
        r = c.get("https://api.ashbyhq.com/posting-api/job-board/cognition")
        print("ASHBY GET /cognition:", r.status_code)
    except Exception as e:
        print("ASHBY GET err:", type(e).__name__)

    GREENHOUSE = [
        "booking", "adyen", "deliveryhero", "mollie", "backbase",
        "scandit", "nexthink", "getyourguide", "messagebird", "bynder",
        "propertyfinder", "careem", "wefox", "sumup", "klarna",
        "stripe", "figma", "notion", "glean", "writer",
    ]
    LEVER = ["n26", "picnic", "bunq"]
    ASHBY = ["tabby", "revolut", "linear"]

    print("\n-- greenhouse --")
    ok_gh = []
    for slug in GREENHOUSE:
        try:
            r = c.get(f"https://boards-api.greenhouse.io/v1/boards/{slug}/jobs")
            mark = "OK " if r.status_code == 200 else f"{r.status_code}"
            print(mark, slug)
            if r.status_code == 200:
                ok_gh.append(slug)
        except Exception as e:
            print("ERR", slug)

    print("\n-- lever --")
    ok_lv = []
    for slug in LEVER:
        try:
            r = c.get(f"https://api.lever.co/v0/postings/{slug}?mode=json")
            mark = "OK " if r.status_code == 200 else f"{r.status_code}"
            print(mark, slug)
            if r.status_code == 200:
                ok_lv.append(slug)
        except Exception as e:
            print("ERR", slug)

    print("\n-- ashby --")
    ok_as = []
    for slug in ASHBY:
        try:
            r = c.post(
                f"https://api.ashbyhq.com/posting-api/job-board/{slug}",
                json={"includeCompensation": False},
                headers={"Origin": "https://jobs.ashbyhq.com"},
            )
            mark = "OK " if r.status_code == 200 else f"{r.status_code}"
            print(mark, slug)
            if r.status_code == 200:
                ok_as.append(slug)
        except Exception as e:
            print("ERR", slug)

    print("\nWORKING:", {"greenhouse": ok_gh, "lever": ok_lv, "ashby": ok_as})
