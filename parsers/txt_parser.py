import pandas as pd

def parse_23andme(filepath: str, effect_alleles: dict) -> dict:

    df = pd.read_csv(
        filepath,
        sep="\t",
        comment="#",
        header=0,
        names=["rsid", "chromosome", "position", "genotype"],
        dtype=str,
    )

    dosages = {}

    for _, row in df.iterrows():
        rsid     = row["rsid"]
        genotype = row["genotype"]

        if not isinstance(genotype, str) or genotype in ("--", "II", "DD", "DI"):
            continue
        if rsid not in effect_alleles:
            continue

        effect = effect_alleles[rsid]
        dosages[rsid] = genotype.count(effect)

    return dosages