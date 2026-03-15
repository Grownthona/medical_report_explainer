# web_enricher.py
from __future__ import annotations
import logging
import re
import httpx
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

SOURCES = {
    "medlineplus": "https://medlineplus.gov/lab-tests/{slug}/",
}

TEST_SLUGS: dict[str, str] = {
    # ── CBC / Haematology ─────────────────────────────────────────────
    "HAEMOGLOBIN":                  "hemoglobin-test",
    "HEMOGLOBIN":                   "hemoglobin-test",
    "HB":                           "hemoglobin-test",
    "HGB":                          "hemoglobin-test",
    "ESR":                          "erythrocyte-sedimentation-rate-esr",
    "ERYTHROCYTESEDIMENTATIONRATE": "erythrocyte-sedimentation-rate-esr",
    "WBC":                          "white-blood-count-wbc",
    "TOTALCOUNTWBC":                "white-blood-count-wbc",
    "TOTALCOUNT":                   "white-blood-count-wbc",
    "WHITEBLOODCOUNT":              "white-blood-count-wbc",
    "RBC":                          "red-blood-cell-rbc-count",
    "REDBLOODCELL":                 "red-blood-cell-rbc-count",
    "PLATELETS":                    "platelet-tests",
    "PLATELETCOUNT":                "platelet-tests",
    "PLT":                          "platelet-tests",
    "PDW":                          "platelet-tests",
    "HCT":                          "hematocrit-test",
    "PCV":                          "hematocrit-test",
    "PCVHCT":                       "hematocrit-test",
    "HEMATOCRIT":                   "hematocrit-test",
    "MCV":                          "mcv-mean-corpuscular-volume",
    "MEANCORPUSCULARVOLUME":        "mcv-mean-corpuscular-volume",
    "MCH":                          "red-blood-cell-rbc-indices",
    "MCHC":                         "red-blood-cell-rbc-indices",
    "RBCINDICES":                   "red-blood-cell-rbc-indices",
    "RDW":                          "rdw-red-cell-distribution-width",
    "RDWSD":                        "rdw-red-cell-distribution-width",
    "RDWCV":                        "rdw-red-cell-distribution-width",
    "REDCELLDISTRIBUTIONWIDTH":     "rdw-red-cell-distribution-width",
    "MPV":                          "mpv-blood-test",
    "MEANPLATELETVOLUME":           "mpv-blood-test",
    "CBC":                          "complete-blood-count-cbc",
    "COMPLETEBLOODCOUNT":           "complete-blood-count-cbc",
    "BLOODDIFFERENTIAL":            "blood-differential",
    "DIFFERENTIALCOUNT":            "blood-differential",
    "NEUTROPHILS":                  "blood-differential",
    "LYMPHOCYTES":                  "blood-differential",
    "MONOCYTES":                    "blood-differential",
    "EOSINOPHILS":                  "blood-differential",

    # ── Biochemistry / Metabolic ──────────────────────────────────────
    "PHOSPHATE":                    "phosphate-in-blood",
    "PHOSPHATEINORGANIC":           "phosphate-in-blood",
    "INORGANICPHOSPHATE":           "phosphate-in-blood",
    "GLUCOSE":                      "blood-glucose-test",
    "BLOODGLUCOSE":                 "blood-glucose-test",
    "FASTINGGLUCOSE":               "blood-glucose-test",
    "HBA1C":                        "hemoglobin-a1c-hba1c-test",
    "GLYCATEDHEMOGLOBIN":           "hemoglobin-a1c-hba1c-test",
    "A1C":                          "hemoglobin-a1c-hba1c-test",
    "CREATININE":                   "creatinine-test",
    "SERUMCREATININE":              "creatinine-test",
    "BUN":                          "bun-blood-urea-nitrogen",
    "BLOODUREANITROGEN":            "bun-blood-urea-nitrogen",
    "UREA":                         "bun-blood-urea-nitrogen",
    "GFR":                          "glomerular-filtration-rate-gfr-test",
    "EGFR":                         "glomerular-filtration-rate-gfr-test",
    "SODIUM":                       "sodium-blood-test",
    "POTASSIUM":                    "potassium-blood-test",
    "CHLORIDE":                     "chloride-blood-test",
    "CALCIUM":                      "calcium-blood-test",
    "MAGNESIUM":                    "magnesium-blood-test",
    "URICACID":                     "uric-acid-test",
    "CRP":                          "c-reactive-protein-crp-test",
    "CREACTIVEPROTEIN":             "c-reactive-protein-crp-test",
    "ALBUMIN":                      "albumin-blood-test",
    "TOTALPROTEIN":                 "total-protein-and-albumin-globulin-a-g-ratio",
    "GLOBULIN":                     "globulin-test",
    "ELECTROLYTES":                 "electrolyte-panel",
    "ELECTROLYTEPANEL":             "electrolyte-panel",
    "BMP":                          "basic-metabolic-panel-bmp",
    "BASICMETABOLICPANEL":          "basic-metabolic-panel-bmp",
    "CMP":                          "comprehensive-metabolic-panel-cmp",
    "COMPREHENSIVEMETABOLICPANEL":  "comprehensive-metabolic-panel-cmp",

    # ── Liver Function ────────────────────────────────────────────────
    "ALT":                          "alt-blood-test",
    "ALANINEAMINOTRANSFERASE":      "alt-blood-test",
    "SGPT":                         "alt-blood-test",
    "AST":                          "ast-test",
    "ASPARTATEAMINOTRANSFERASE":    "ast-test",
    "SGOT":                         "ast-test",
    "GGT":                          "gamma-glutamyl-transferase-ggt-test",
    "GAMMAGLUTAMYLTRANSFERASE":     "gamma-glutamyl-transferase-ggt-test",
    "BILIRUBIN":                    "bilirubin-blood-test",
    "BILIRUBINTOTAL":               "bilirubin-blood-test",
    "DIRECTBILIRUBIN":              "bilirubin-blood-test",
    "INDIRECTBILIRUBIN":            "bilirubin-blood-test",
    "ALP":                          "alkaline-phosphatase",
    "ALKALINEPHOSPHATASE":          "alkaline-phosphatase",
    "LFT":                          "liver-function-tests",
    "LIVERFUNCTIONTEST":            "liver-function-tests",

    # ── Thyroid ───────────────────────────────────────────────────────
    "TSH":                          "tsh-thyroid-stimulating-hormone-test",
    "THYROIDSTIMULATINGHORMONE":    "tsh-thyroid-stimulating-hormone-test",
    "T3":                           "triiodothyronine-t3-tests",
    "TRIIODOTHYRONINE":             "triiodothyronine-t3-tests",
    "FREET3":                       "triiodothyronine-t3-tests",
    "T4":                           "thyroxine-t4-test",
    "THYROXINE":                    "thyroxine-t4-test",
    "FREET4":                       "thyroxine-t4-test",
    "THYROIDANTIBODIES":            "thyroid-antibodies",

    # ── Lipids ────────────────────────────────────────────────────────
    "CHOLESTEROL":                  "cholesterol-levels",
    "TOTALCHOLESTEROL":             "cholesterol-levels",
    "HDL":                          "cholesterol-levels",
    "LDL":                          "cholesterol-levels",
    "TRIGLYCERIDES":                "triglycerides-test",
    "TG":                           "triglycerides-test",

    # ── Iron Studies ──────────────────────────────────────────────────
    "IRON":                         "iron-tests",
    "FERRITIN":                     "ferritin-blood-test",
    "TIBC":                         "iron-tests",

    # ── Coagulation ───────────────────────────────────────────────────
    "PT":                           "prothrombin-time-test-and-inr-ptinr",
    "INR":                          "prothrombin-time-test-and-inr-ptinr",
    "PROTHROMBINTIME":              "prothrombin-time-test-and-inr-ptinr",
    "PTT":                          "partial-thromboplastin-time-ptt-test",
    "APTT":                         "partial-thromboplastin-time-ptt-test",
    "DDIMER":                       "d-dimer-test",

    # ── Diabetes ──────────────────────────────────────────────────────
    "DIABETESTEST":                 "diabetes-tests",
    "INSULIN":                      "insulin-in-blood",
    "CPEPTIDE":                     "c-peptide-test",

    # ── Cardiac ───────────────────────────────────────────────────────
    "TROPONIN":                     "troponin-test",
    "BNP":                          "natriuretic-peptide-tests-bnp-nt-probnp",
    "NTPROBNP":                     "natriuretic-peptide-tests-bnp-nt-probnp",
    "CK":                           "creatine-kinase",
    "CREATINEKINASE":               "creatine-kinase",
    "CKMB":                         "creatine-kinase",
    "LDH":                          "lactate-dehydrogenase-ldh-test",

    # ── Imaging / X-Ray AI findings ───────────────────────────────────
    "MASS":                         "lung-function-tests",
    "LUNGOPACITY":                  "lung-function-tests",
    "ATELECTASIS":                  "lung-function-tests",
    "INFILTRATION":                 "lung-function-tests",
    "PNEUMOTHORAX":                 "lung-function-tests",
    "EFFUSION":                     "pleural-fluid-analysis",
    "PLEURALEFFUSION":              "pleural-fluid-analysis",
    "CONSOLIDATION":                "lung-function-tests",
    "FIBROSIS":                     "lung-function-tests",
    "NODULE":                       "lung-function-tests",
    "CARDIOMEGALY":                 "measuring-blood-pressure",
    "ENLARGEDCARDIOMEDIASTINUM":    "electrocardiogram",
    "PLEURALTHICKENING":            "pleural-fluid-analysis",
    "EMPHYSEMA":                    "lung-function-tests",
    "LUNGLESION":                   "lung-function-tests",
    "PNEUMONIA":                    "lung-function-tests",

    # ── Urine / Kidney ────────────────────────────────────────────────
    "URINALYSIS":                   "glucose-in-urine-test",
    "PROTEINURINE":                 "protein-in-urine",
    "MICROALBUMIN":                 "microalbumin-creatinine-ratio",

    # ── Vitamins & Minerals ───────────────────────────────────────────
    "VITAMIND":                     "vitamin-d-test",
    "VITAMINB12":                   "vitamin-b-test",
    "VITAMINB":                     "vitamin-b-test",
    "FOLATE":                       "vitamin-b-test",
    "VITAMINE":                     "vitamin-e-tocopherol-test",

    # ── Hormones ──────────────────────────────────────────────────────
    "TESTOSTERONE":                 "testosterone-levels-test",
    "FSH":                          "follicle-stimulating-hormone-fsh-levels-test",
    "LH":                           "luteinizing-hormone-lh-levels-test",
    "PROLACTIN":                    "prolactin-levels",
    "PROGESTERONE":                 "progesterone-test",
    "ESTROGEN":                     "estrogen-levels-test",
    "CORTISOL":                     "cortisol-test",
    "DHEA":                         "dhea-sulfate-test",

    # ── Infection / Inflammation ──────────────────────────────────────
    "PROCALCITONIN":                "procalcitonin-test",
    "MALARIA":                      "malaria-tests",
    "DENGUE":                       "dengue-fever-test",
    "WIDAL":                        "bacteria-culture-test",
    "BLOODCULTURE":                 "bacteria-culture-test",
    "URINECULTURE":                 "bacteria-culture-test",

    # ── Dental ───────────────────────────────────────────────────────
    "MISSINGTEETH":                 "dental-exam",
    "PERIAPICALPATHOSIS":           "dental-exam",
    "PERIODONTALBONELOSS":          "dental-exam",
    "RADIOLUCENCY":                 "dental-exam",
    "ENDODONTICRESTORATION":        "dental-exam",
    "RADICULARCYST":                "dental-exam",

    # ── Mental health ─────────────────────────────────────────────────
    "CLINICALSUMMARY":              "mental-health-screening",
    "PSYCHIATRICASSESSMENT":        "mental-health-screening",
    "DEPRESSION":                   "depression-screening",
    "ANXIETY":                      "mental-health-screening",
}

# ── Intent keywords — only enrich when user is asking for explanation ─────────
_EXPLAIN_KEYWORDS = [
    # English
    "what is", "what does", "what are", "why is", "why are", "why did",
    "explain", "meaning", "means", "cause", "causes", "reason", "reasons",
    "dangerous", "serious", "worried", "concern", "diet", "food", "eat",
    "treatment", "should i", "what should", "how to", "how do",
    "tell me about", "describe", "understand",
    # Bengali
    "কি", "কেন", "মানে", "কারণ", "ব্যাখ্যা", "বিপজ্জনক",
    "চিকিৎসা", "খাবার", "কী করব", "বলুন",
    # Arabic
    "ما هو", "لماذا", "اشرح", "سبب",
    # Hindi
    "क्या है", "क्यों", "कारण", "समझाएं",
    # Urdu
    "کیا ہے", "کیوں", "وجہ", "سمجھائیں",
]

# ── Session-level cache: normalised key → parsed knowledge dict ───────────────
_cache: dict[str, dict] = {}


def needs_enrichment(query: str) -> bool:
    """Return True if the query is asking for explanation, not just values."""
    q = query.lower()
    return any(k in q for k in _EXPLAIN_KEYWORDS)


async def fetch_test_knowledge(test_name: str) -> dict | None:
    """
    Fetch medical knowledge for a test from MedlinePlus (NIH).
    Returns structured dict or None if not found / network error.
    Results are cached in-process for the server lifetime.
    """
    key = _normalise_name(test_name)

    if key in _cache:
        logger.debug("Cache hit for %s", key)
        return _cache[key]

    slug = TEST_SLUGS.get(key)
    if not slug:
        logger.debug("No MedlinePlus slug for test key: %s (raw: %s)", key, test_name)
        return None

    url = SOURCES["medlineplus"].format(slug=slug)

    try:
        async with httpx.AsyncClient(timeout=8.0, follow_redirects=True) as client:
            resp = await client.get(
                url,
                headers={
                    "User-Agent": "MediBot/1.0 (medical report explainer; non-commercial)",
                    "Accept": "text/html",
                },
            )
        if resp.status_code != 200:
            logger.warning("MedlinePlus returned %d for %s", resp.status_code, url)
            return None

        knowledge = _parse_medlineplus(resp.text, test_name, url)
        _cache[key] = knowledge
        logger.info("Enriched '%s' from MedlinePlus (%s)", test_name, slug)
        return knowledge

    except httpx.TimeoutException:
        logger.warning("Timeout fetching MedlinePlus for %s", test_name)
        return None
    except Exception as exc:
        logger.warning("Web enrichment failed for %s: %s", test_name, exc)
        return None


def _parse_medlineplus(html: str, test_name: str, url: str) -> dict:
    """
    Parse a MedlinePlus lab-test page into a structured knowledge dict.

    MedlinePlus pages use <h2> headings to divide sections. We extract
    the sections most relevant to patient-facing explanation.
    """
    soup = BeautifulSoup(html, "html.parser")

    # Extract page title (full test name)
    full_name = ""
    h1 = soup.find("h1")
    if h1:
        full_name = h1.get_text(strip=True)

    # Walk all h2 sections and capture text beneath each
    sections: dict[str, str] = {}
    for h2 in soup.find_all("h2"):
        heading = h2.get_text(strip=True).lower()
        parts: list[str] = []
        for sibling in h2.find_next_siblings():
            if sibling.name == "h2":
                break
            if sibling.name in ("p", "ul", "ol"):
                parts.append(sibling.get_text(" ", strip=True))
        if parts:
            # Cap each section at 500 chars to keep context lean
            sections[heading] = " ".join(parts)[:500]

    return {
        "source":           "MedlinePlus (NIH)",
        "url":              url,
        "full_name":        full_name or test_name,
        "what_it_measures": _first(sections, [
            "what is it used for",
            "why do i need",
            "what is a",
        ]),
        "abnormal_means":   _first(sections, [
            "what do the results mean",
            "what do my test results mean",
        ]),
        "common_causes":    _first(sections, [
            "what do abnormal results mean",
            "what causes",
        ]),
        "patient_advice":   _first(sections, [
            "is there anything else i need to know",
            "what else should i know",
        ]),
    }


def _first(sections: dict[str, str], keys: list[str]) -> str:
    """Return the first matching section value or empty string."""
    for k in keys:
        if k in sections and sections[k]:
            return sections[k]
    return ""


def _normalise_name(name: str) -> str:
    """
    Convert a raw test name from the report JSON into a canonical
    uppercase key that matches TEST_SLUGS.
    """
    name = name.upper().strip()

    # Remove parenthetical content e.g. "Phosphate (Inorganic)" → "PHOSPHATE"
    name = re.sub(r"\s*\(.*?\)", "", name)

    # Remove noisy words that don't change the test identity
    noise = r"\b(BLOOD|SERUM|PLASMA|INORGANIC|TEST|LEVEL|LEVELS|" \
            r"ANALYSIS|REPORT|EVALUATION|ASSESSMENT|TOTAL|COUNT|" \
            r"COMPLETE|RANDOM|FASTING|SPOT)\b"
    name = re.sub(noise, "", name)

    # Strip all non-alphanumeric characters
    name = re.sub(r"[^A-Z0-9]", "", name)

    # Apply manual aliases for tricky compound names from your JSON formats
    aliases: dict[str, str] = {
        # HCT variants
        "PCVHCT":               "HCT",
        "HCTPCV":               "HCT",
        # WBC variants
        "TOTALCOUNTOFWBC":      "WBC",
        "TOTALCOUNTWBC":        "WBC",
        "WBCTOTAL":             "WBC",
        # RBC
        "RBCBLOOD":             "RBC",
        # Haemoglobin spelling variants
        "HB":                   "HAEMOGLOBIN",
        "HGB":                  "HAEMOGLOBIN",
        # Phosphate
        "PHOSPHATEINORGANIC":   "PHOSPHATE",
        # X-ray report test names from your JSON
        "DXCHESTPIAVIEW":       "LUNGOPACITY",
        "DXCHEST":              "LUNGOPACITY",
        "CHESTXRAY":            "LUNGOPACITY",
        "XRAYPARANASINUSES":    "CLINICALSUMMARY",
        "PNSXRAY":              "CLINICALSUMMARY",
        "XRAYPARANASAL":        "CLINICALSUMMARY",
        # Psychiatric / clinical
        "CLINICALSUMMARY":      "CLINICALSUMMARY",
        # Bilirubin
        "BILIRUBINTOTAL":       "BILIRUBIN",
        # Uric acid
        "URICACID":             "URICACID",
    }

    return aliases.get(name, name)