import sys

import httpx

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
BASE = "http://localhost:8000/api"

# FDE-heavy employers with DE/NL/CH/UAE presence on public boards
COMPANIES = [
    ("Palantir Technologies", "greenhouse", "palantir"),   # Berlin/The Hague/Zurich/Dubai - invented the FDE role
    ("OpenAI", "greenhouse", "openai"),                     # Forward Deployed Eng, incl. Dubai
    ("Anthropic", "greenhouse", "anthropic"),               # Applied/Deployed engineers
    ("Scale AI", "greenhouse", "scaleai"),                  # Forward Deployed Engineer title
    ("Databricks", "greenhouse", "databricks"),
    ("Snowflake", "greenhouse", "snowflake"),
    ("Datadog", "greenhouse", "datadog"),                   # Amsterdam office
    ("Celonis", "greenhouse", "celonis"),                   # Munich HQ, Solution Consulting
    ("Personio", "greenhouse", "personio"),                 # Munich HR tech
    ("Helsing", "greenhouse", "helsing"),                   # Munich defence AI, deployment roles
    ("DeepL", "greenhouse", "deepl"),                       # Cologne
    ("Mistral AI", "lever", "mistral"),                     # EU AI leader, remote-friendly
]

with httpx.Client(timeout=30) as c:
    added = []
    for name, source, slug in COMPANIES:
        r = c.post(f"{BASE}/companies", json={"name": name, "source": source, "slug": slug})
        if r.status_code == 200:
            added.append(name)
        elif r.status_code == 409:
            added.append(f"{name} (already)")
        else:
            print(f"SKIP {name}: {r.status_code} {r.text[:100]}")
    print("COMPANIES ADDED:", ", ".join(added))

    # upload the real CV (PDF parsed server-side), promote to master, drop test resume
    cv_path = r"C:\Users\thann\Downloads\Sudhir_CV_21Feb2026_DE.docx(2) (1).pdf"
    with open(cv_path, "rb") as fh:
        r = c.post(
            f"{BASE}/resumes/upload",
            files={"file": ("Sudhir_Kumar_Thanna_CV.pdf", fh, "application/pdf")},
        )
    print("UPLOAD:", r.status_code, r.json() if r.status_code == 200 else r.text[:200])
    rid = r.json()["id"]

    resumes = c.get(f"{BASE}/resumes").json()
    for res in resumes:
        if res["id"] != rid and "test_resume" in res["name"]:
            c.delete(f"{BASE}/resumes/{res['id']}")
            print("REMOVED old test resume", res["id"])
    c.post(f"{BASE}/resumes/{rid}/set-master")

    profile = {
        "full_name": "Sudhir Kumar Thanna",
        "email": "thannasudhir9@gmail.com",
        "phone": "+39-3511687490",
        "location": "Frankfurt, Germany",
        "summary": (
            "Senior Technical Consultant & Forward-Deployed style Salesforce engineer with 10+ years "
            "delivering enterprise platforms end-to-end for clients across Europe (DE/CH/BE/FI/UK/IT): "
            "requirement analysis, architecture, implementation, integrations and go-live. Deep expertise "
            "in Revenue Cloud, Agentforce/Agentic AI, Omnistudio, Data Cloud and complex REST/SOAP "
            "integrations. 25x Salesforce certified incl. Integration/System/Application Architect. "
            "PMP, TOGAF EA Practitioner, CSPO, CSM, SAFe6."
        ),
        "skills": [
            "Salesforce", "Revenue Cloud", "Agentforce", "Agentic AI", "Generative AI",
            "LLM", "Prompt Engineering", "Omnistudio", "Data Cloud", "CPQ",
            "Apex", "LWC", "Integration Architect", "REST API", "SOAP",
            "Enterprise Architecture", "TOGAF", "Solution Design", "Stakeholder Management",
            "Java", "Spring Boot", "Python", "SQL", "CI/CD", "Copado", "Git",
        ],
        "desired_titles": [
            "Forward Deployed Engineer", "Forward Deployed Software Engineer",
            "Deployment Strategist", "Solutions Engineer", "Solutions Architect",
            "Customer Engineer", "Implementation Engineer", "Implementation Consultant",
            "Technical Consultant", "Field Engineer", "Professional Services Engineer",
            "Solution Consultant", "Technical Architect",
        ],
        "preferred_locations": [
            "Germany", "Berlin", "Munich", "Frankfurt", "Hesse",
            "Netherlands", "Amsterdam", "The Hague",
            "Switzerland", "Zurich", "Geneva", "Baar",
            "Dubai", "Abu Dhabi", "United Arab Emirates", "UAE",
        ],
        "remote_ok": True,
    }
    r = c.put(f"{BASE}/profile", json=profile, timeout=300)
    print("PROFILE:", r.status_code)

    print("SYNCING all boards (this can take a minute)...", flush=True)
    r = c.post(f"{BASE}/sync?wait=true", timeout=600)
    data = r.json()
    print(f"SYNC: {data['companies_synced']} boards ok | fetched={data['jobs_fetched']} "
          f"| new={data['jobs_new']}")
    for e in data["errors"]:
        print("  ERR:", e[:140])
