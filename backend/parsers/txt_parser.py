# parsers/txt_parser.py

import pandas as pd

def parse_23andme(filepath: str, effect_alleles: dict) -> dict:
    """
    Parse a 23andMe .txt export.
    effect_alleles: {(chr, pos): effect_allele_letter}
                    keyed on (chromosome, position) since most
                    weight files don't have rsIDs.
    Returns {(chr, pos): dosage}
    """
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
        genotype = row["genotype"]

        if not isinstance(genotype, str) or genotype in ("--", "II", "DD", "DI"):
            continue

        try:
            chrom = str(int(row["chromosome"]))  # normalize "01" -> "1"
            pos   = str(int(row["position"]))
        except (ValueError, TypeError):
            continue

        key = (chrom, pos)

        if key not in effect_alleles:
            continue

        effect        = effect_alleles[key]
        dosages[key]  = genotype.count(effect)

    return dosages