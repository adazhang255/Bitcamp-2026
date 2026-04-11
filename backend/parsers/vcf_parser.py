# parsers/vcf_parser.py

def parse_vcf(filepath: str, effect_alleles: dict) -> dict:
    """
    Parse a standard VCF file.
    effect_alleles: {(chr, pos): effect_allele_letter}
    Returns {(chr, pos): dosage}
    """
    dosages = {}

    with open(filepath, "r") as f:
        for line in f:
            if line.startswith("#"):
                continue

            parts = line.strip().split("\t")
            if len(parts) < 10:
                continue

            # CHROM may be "chr1" or just "1" — normalize to just the number
            chrom = parts[0].replace("chr", "").replace("Chr", "")
            pos   = parts[1]
            ref   = parts[3]
            alt   = parts[4]

            key = (chrom, pos)

            if key not in effect_alleles:
                continue

            sample = parts[9]
            gt     = sample.split(":")[0].replace("|", "/")

            if gt not in ("0/0", "0/1", "1/0", "1/1"):
                continue

            allele_a, allele_b = gt.split("/")
            alt_count = (allele_a == "1") + (allele_b == "1")

            effect = effect_alleles[key]

            if effect == alt:
                dosages[key] = alt_count
            elif effect == ref:
                dosages[key] = 2 - alt_count
            else:
                continue

    return dosages