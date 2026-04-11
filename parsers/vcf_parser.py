def parse_vcf(filepath: str, effect_alleles: dict) -> dict:
    dosages = {}

    with open(filepath, "r") as f:
        for line in f:

            if line.startswith("#"):
                continue

            parts = line.strip().split("\t")
            if len(parts) < 10:
                continue

            rsid = parts[2]
            if not rsid.startswith("rs"):
                continue

            if rsid not in effect_alleles:
                continue

            ref     = parts[3]
            alt     = parts[4]
            sample  = parts[9]
            gt = sample.split(":")[0]
            gt = gt.replace("|", "/")

            if gt not in ("0/0", "0/1", "1/0", "1/1"):
                continue
            allele_a, allele_b = gt.split("/")
            alt_count = (allele_a == "1") + (allele_b == "1")

            effect = effect_alleles[rsid]

            if effect == alt:
                dosages[rsid] = alt_count
            elif effect == ref:
                dosages[rsid] = 2 - alt_count
            else:
                continue

    return dosages