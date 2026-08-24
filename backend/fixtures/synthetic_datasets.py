"""Fake, realistic dataset profiles for demoing and dogfooding the tool
end-to-end without real ACE/TASO data. Deliberately varied in size, format,
and domain, and deliberately varied in FAIR maturity (one strong, one weak,
two mixed) so a demo run shows the tool's actual range, not just one score.

Real institutional data — especially anything OMOP/health-record-shaped —
likely needs a cleared data-governance path before touching any LLM, on-prem
or not (see ROADMAP.md). These fixtures exist so that question never blocks
building, testing, or demoing the tool.

Each answer's "note" is deliberately specific (never just restating the
question) — this also exercises engine/remediation.py's reference-grounding
check, which rejects a generated remediation that doesn't engage with what
the person actually said.
"""

_LABELS = {
    "yes": "Yes, clearly true",
    "partial": "Partially / inconsistently true",
    "no": "No, not true",
    "dont_know": "I don't know",
}


def _a(value: str, note: str) -> dict:
    return {"value": value, "label": _LABELS[value], "note": note}


SYNTHETIC_DATASETS = [
    {
        "slug": "tb-wgs-collection",
        "subject_label": "ACE — TB Whole-Genome Sequencing Collection",
        "description": "Whole-genome sequencing reads and variant calls from a multi-site TB surveillance study.",
        "format": "FASTQ / BAM / VCF",
        "size": "~800 GB across 340 samples",
        "domain": "Genomics / infectious disease surveillance",
        "answers": {
            "fair.f1-identifier": _a("yes", "Each sequencing batch gets a Zenodo DOI once QC passes."),
            "fair.f2-metadata-richness": _a(
                "yes", "The sample sheet records collection site, date, and sequencing platform for every run."
            ),
            "fair.f4-discoverable": _a(
                "partial", "Listed in our internal HPC catalog, but not in any public or cross-institution index yet."
            ),
            "fair.a1-access-process": _a(
                "yes", "Access requests are routed through the PI and the ACE data office."
            ),
            "fair.a1-2-access-control": _a(
                "partial",
                "HPC cluster accounts are provisioned per request, but there's no formal process for revoking access when someone leaves the project.",
            ),
            "fair.a2-metadata-persistence": _a(
                "no", "If the HPC storage volume were wiped, the sample sheet lives only on that same volume."
            ),
            "fair.i1-i2-standard-formats": _a(
                "yes", "Standard FASTQ/BAM formats, reads aligned against a standard M. tuberculosis reference genome."
            ),
            "fair.r1-data-dictionary": _a(
                "yes", "The full sequencing protocol and variable definitions are documented in the lab wiki."
            ),
            "fair.r1-1-license": _a("dont_know", "Honestly not sure if we've ever put a license statement on this collection."),
            "fair.r1-2-provenance": _a(
                "yes", "The full chain from sample collection through variant calling is logged in our LIMS."
            ),
            "fair.r1-3-community-standard": _a(
                "yes", "We follow standard GATK best-practices pipeline conventions for WGS variant calling."
            ),
            "fair.f3-metadata-links-to-data": _a(
                "partial", "The metadata sheet references the batch ID but not every individual sample's own DOI."
            ),
        },
    },
    {
        "slug": "chw-household-survey",
        "subject_label": "ACE — CHW Household Health Survey (CSV export)",
        "description": "A community health worker household survey, exported as a flat CSV file.",
        "format": "CSV",
        "size": "~12 MB, one file",
        "domain": "Community health / field survey",
        "answers": {
            "fair.f1-identifier": _a("no", "It's just a CSV sitting in a shared Google Drive folder."),
            "fair.f2-metadata-richness": _a(
                "no", "There's no description anywhere beyond the filename 'survey_final_v3.csv'."
            ),
            "fair.f4-discoverable": _a("no", "Only the two people who ran the survey know it exists."),
            "fair.a1-access-process": _a("no", "Whoever has the Drive link can open it — no formal process."),
            "fair.a1-2-access-control": _a(
                "no", "The Drive link has been shared over email a few times; nobody's tracking who still has access."
            ),
            "fair.a2-metadata-persistence": _a(
                "dont_know", "Not sure what would happen to any record of this if the Drive folder got deleted."
            ),
            "fair.i1-i2-standard-formats": _a(
                "partial",
                "It's a plain CSV so the file format itself is standard, but the column headers are just whatever the field team typed in — no coding scheme.",
            ),
            "fair.r1-data-dictionary": _a(
                "no", "There's no codebook — some columns use abbreviations only the field team understands."
            ),
            "fair.r1-1-license": _a("no", "This has never been discussed."),
            "fair.r1-2-provenance": _a(
                "partial", "We know roughly which team collected it and when, but nothing's written down formally."
            ),
            "fair.r1-3-community-standard": _a("no", "It's structured however the field team happened to set up their spreadsheet."),
            "fair.f3-metadata-links-to-data": _a(
                "dont_know", "There isn't really separate metadata from the file itself to check."
            ),
        },
    },
    {
        "slug": "amr-surveillance-panel",
        "subject_label": "ACE — Antimicrobial Resistance Surveillance Isolate Panel",
        "description": "Bacterial isolate records with resistance profiles from a regional AMR surveillance program.",
        "format": "Structured lab records (WHONET export)",
        "size": "~2 GB, ~4,000 isolate records",
        "domain": "Antimicrobial resistance / clinical microbiology",
        "answers": {
            "fair.f1-identifier": _a(
                "partial", "Each isolate has a lab accession number, but there's no single identifier for the panel as a whole dataset."
            ),
            "fair.f2-metadata-richness": _a(
                "yes", "Species, resistance profile, collection site, and date are recorded for every isolate."
            ),
            "fair.f4-discoverable": _a("no", "It's not listed anywhere outside our own lab tracking spreadsheet."),
            "fair.a1-access-process": _a(
                "partial", "Other AMR surveillance partners can request it, but the process isn't written down anywhere formal."
            ),
            "fair.a1-2-access-control": _a("no", "Data is shared via email attachments on request — there's no access list."),
            "fair.a2-metadata-persistence": _a(
                "yes", "The lab tracking system is backed up nightly and lives separately from any one researcher's laptop."
            ),
            "fair.i1-i2-standard-formats": _a("yes", "We use WHONET-compatible resistance coding throughout."),
            "fair.r1-data-dictionary": _a(
                "partial", "Column meanings are known to the lab team but have never been written into a formal codebook."
            ),
            "fair.r1-1-license": _a("no", "No terms have ever been stated."),
            "fair.r1-2-provenance": _a("yes", "The full lab workflow from isolate to susceptibility result is logged."),
            "fair.r1-3-community-standard": _a(
                "yes", "WHONET is the recognized community standard format for AMR surveillance data."
            ),
            "fair.f3-metadata-links-to-data": _a("no", "There's no formal metadata record separate from the raw lab spreadsheet."),
        },
    },
    {
        "slug": "malaria-rdt-image-archive",
        "subject_label": "ACE — Malaria RDT Image Archive",
        "description": "Photographed rapid diagnostic test strips collected across multiple clinic sites for an ML classifier project.",
        "format": "JPEG images + a loose metadata spreadsheet",
        "size": "~15 GB, ~22,000 images",
        "domain": "Diagnostics / machine learning training data",
        "answers": {
            "fair.f1-identifier": _a("no", "Images are just named by device serial number and capture timestamp."),
            "fair.f2-metadata-richness": _a(
                "partial", "We know which clinic each batch came from, but not much beyond that."
            ),
            "fair.f4-discoverable": _a("dont_know", "Not sure if this has ever been registered anywhere."),
            "fair.a1-access-process": _a("no", "Whoever has access to the shared drive has access — no request process."),
            "fair.a1-2-access-control": _a("no", "There's no tracking of who has downloaded or copied the images."),
            "fair.a2-metadata-persistence": _a(
                "no", "All the metadata lives in the same folder as the images themselves — no separate record."
            ),
            "fair.i1-i2-standard-formats": _a(
                "yes", "Standard JPEG images, captured with a consistent protocol across devices."
            ),
            "fair.r1-data-dictionary": _a("no", "There's no documentation of the capture protocol or annotation scheme."),
            "fair.r1-1-license": _a("dont_know", "This has never come up."),
            "fair.r1-2-provenance": _a(
                "partial", "We know which study this came from, but not the individual capture/annotation steps."
            ),
            "fair.r1-3-community-standard": _a("no", "No recognized medical-imaging data standard has been applied yet."),
            "fair.f3-metadata-links-to-data": _a("no", "There's no separate metadata record to check against."),
        },
    },
]
