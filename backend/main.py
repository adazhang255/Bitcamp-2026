from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import tempfile, os, shutil
from pathlib import Path

from parsers.vcf_parser import parse_vcf
from parsers.txt_parser import parse_23andme
from scoring.prs_scoring import score_all_disorders
from scoring.normalizer import to_percentiles
from ml.model import predict_with_explanation

app = FastAPI(title="GenoRisk", version="1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "https://genorisk.vercel.app"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── helpers ──────────────────────────────────────────────────────────────────

def detect_and_parse(filepath: str) -> dict:
    """
    Sniff the file format and route to the right parser.
    Returns {rsid: dosage} dict.
    """
    with open(filepath) as f:
        first_real_line = next(l for l in f if not l.startswith("#")).strip()

    # 23andMe: first column is rsid, fourth is genotype string like "AG"
    if first_real_line.startswith("rs") and len(first_real_line.split("\t")) == 4:
        return parse_23andme(filepath)

    # VCF: first column is CHROM (a chromosome number or "chr1" etc.)
    return parse_vcf(filepath)


def run_pipeline(filepath: str) -> dict:
    """Full pipeline: parse -> score -> normalize -> ML predict."""
    snp_dosages  = detect_and_parse(filepath)
    raw_scores   = score_all_disorders(snp_dosages)
    percentiles  = to_percentiles(raw_scores)
    predictions  = predict_with_explanation(percentiles)
    return {
        "snps_parsed": len(snp_dosages),
        "results":     predictions,
    }


# ── routes ───────────────────────────────────────────────────────────────────

@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/analyze")
async def analyze(file: UploadFile = File(...)):
    """
    Main endpoint. Accepts a .vcf or 23andMe .txt file.
    Deletes the file immediately after processing — nothing persisted.
    """
    filename = file.filename or ""

    if not filename.endswith((".vcf", ".txt")):
        raise HTTPException(400, "Only .vcf and .txt files are supported.")

    max_mb = 100
    contents = await file.read()
    if len(contents) > max_mb * 1024 * 1024:
        raise HTTPException(413, f"File too large. Max size is {max_mb}MB.")

    suffix = Path(filename).suffix
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        tmp.write(contents)
        tmp_path = tmp.name

    try:
        payload = run_pipeline(tmp_path)
        return {"status": "ok", **payload}
    except ValueError as e:
        raise HTTPException(422, f"Could not parse file: {e}")
    except Exception as e:
        raise HTTPException(500, f"Analysis failed: {e}")
    finally:
        os.unlink(tmp_path)   # always delete, even if we crashed


@app.get("/demo")
def demo():
    """
    Returns pre-baked realistic scores — use this on stage
    so you don't need to upload a real genome file during the demo.
    """
    import json
    payload_path = Path("data/demo_payload.json")
    if not payload_path.exists():
        raise HTTPException(404, "Demo payload not found. Run scripts/generate_demo.py first.")
    return json.loads(payload_path.read_text())


@app.get("/disorders")
def list_disorders():
    """
    Returns metadata about every supported disorder —
    useful for the frontend to build its UI without hardcoding names.
    """
    from scoring.prs_scoring import DISORDER_META
    return DISORDER_META