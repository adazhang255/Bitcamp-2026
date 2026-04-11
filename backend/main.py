# main.py

from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import tempfile, os, json
from pathlib import Path
import pandas as pd

from parsers.vcf_parser import parse_vcf
from parsers.txt_parser import parse_23andme
from scoring.prs_scoring import score_all_disorders, DISORDER_META
from scoring.normalizer import to_percentiles
from ml.model import predict_with_explanation


# ── startup: load effect alleles once ────────────────────────────────────────

EFFECT_ALLELES: dict = {}

# replace the build_effect_alleles function in main.py

def build_effect_alleles() -> dict:
    """
    Build {(chr, pos): effect_allele} from all weights files.
    Called once at startup.
    """
    ea = {}
    for f in Path("weights").glob("*.txt"):
        try:
            df = pd.read_csv(f, sep="\t", comment="#", dtype=str)
            df.columns = [c.strip().lower() for c in df.columns]

            if "chr_name" not in df.columns or "chr_position" not in df.columns:
                continue
            if "effect_allele" not in df.columns:
                continue

            # normalize chromosome format
            df["chr_name"] = (
                df["chr_name"]
                .str.replace("chr", "", case=False)
                .str.lstrip("0")
                .replace("", "0")
            )

            for _, row in df.iterrows():
                key = (str(row["chr_name"]), str(row["chr_position"]).strip())
                ea[key] = str(row["effect_allele"])

        except Exception as e:
            print(f"Warning: could not read {f.name}: {e}")

    print(f"Loaded effect alleles for {len(ea):,} positions")
    return ea


@asynccontextmanager
async def lifespan(app: FastAPI):
    # runs before the server starts accepting requests
    global EFFECT_ALLELES
    print("Loading effect alleles...")
    EFFECT_ALLELES = build_effect_alleles()
    yield
    # runs on shutdown (nothing to clean up)


app = FastAPI(title="GenoRisk", version="1.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "https://genorisk.vercel.app"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── helpers ───────────────────────────────────────────────────────────────────

def detect_and_parse(filepath: str) -> dict:
    """Sniff the file format and route to the right parser."""
    with open(filepath) as f:
        for line in f:
            if line.startswith("#"):
                continue
            first = line.strip()
            break

    cols = first.split("\t")

    # 23andMe: rsid in col 0, genotype string in col 3
    if cols[0].startswith("rs") and len(cols) == 4:
        return parse_23andme(filepath, EFFECT_ALLELES)

    # VCF: CHROM in col 0 (number or "chrN"), rsid in col 2
    return parse_vcf(filepath, EFFECT_ALLELES)


def run_pipeline(filepath: str) -> dict:
    """Full pipeline: parse → score → normalize → predict."""
    snp_dosages = detect_and_parse(filepath)

    if len(snp_dosages) == 0:
        raise ValueError(
            "No matching SNPs found. Make sure this is a valid "
            "23andMe or VCF file."
        )

    raw_scores  = score_all_disorders(snp_dosages)
    percentiles = to_percentiles(raw_scores)
    predictions = predict_with_explanation(percentiles)

    return {
        "snps_parsed": len(snp_dosages),
        "results":     predictions,
    }


# ── routes ────────────────────────────────────────────────────────────────────

@app.get("/health")
def health():
    return {"status": "ok", "snps_loaded": len(EFFECT_ALLELES)}


@app.post("/analyze")
async def analyze(file: UploadFile = File(...)):
    """
    Main endpoint. Accepts .vcf or 23andMe .txt file.
    File is deleted immediately after processing — nothing persisted.
    """
    filename = file.filename or ""

    if not filename.endswith((".vcf", ".txt")):
        raise HTTPException(400, "Only .vcf and .txt files are supported.")

    contents = await file.read()

    if len(contents) > 100 * 1024 * 1024:   # 100MB limit
        raise HTTPException(413, "File too large. Max size is 100MB.")

    suffix = Path(filename).suffix
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        tmp.write(contents)
        tmp_path = tmp.name

    try:
        payload = run_pipeline(tmp_path)
        return {"status": "ok", **payload}

    except ValueError as e:
        raise HTTPException(422, str(e))

    except FileNotFoundError as e:
        raise HTTPException(500, str(e))

    except Exception as e:
        raise HTTPException(500, f"Analysis failed: {e}")

    finally:
        os.unlink(tmp_path)   # always delete the temp file


@app.get("/demo")
def demo():
    """Pre-baked scores for live demo — no upload needed."""
    path = Path("data/demo_payload.json")
    if not path.exists():
        raise HTTPException(
            404,
            "Run `python scripts/generate_demo.py` to create the demo payload."
        )
    return json.loads(path.read_text())


@app.get("/disorders")
def list_disorders():
    """Metadata about every supported disorder — used by the frontend."""
    return DISORDER_META