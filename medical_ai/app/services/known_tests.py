"""
KNOWN_TESTS registry
─────────────────────
Covers all major lab panel types:
  CBC          - Complete Blood Count + differentials
  LFT          - Liver Function Tests
  RFT          - Renal Function Tests
  TFT          - Thyroid Function Tests
  LIPID        - Lipid Profile
  HBA1C        - Diabetes / Glucose panel
  ELECTROLYTES - Electrolytes + ABG
  COAGULATION  - Clotting studies
  CARDIAC      - Cardiac markers
  IRON         - Iron studies
  HORMONE      - Reproductive / adrenal hormones
  URINE        - Urinalysis
  TUMOUR       - Tumour markers
  VITAMINS     - Vitamin levels
  IMMUNOLOGY   - Autoimmune / infection serology
  HAEMATOLOGY  - Specialised haematology
  VITALS       - SpO2, BMI, BP (when reported numerically)

Format per entry:
    "MATCH_KEY": {
        "name":     display name shown in output,
        "unit":     fallback unit if report doesn't include one,
        "male":     (low, high)  normal range,
        "female":   (low, high)  normal range,
        "critical": (critical_low, critical_high)  — None means no threshold defined
    }
Notes:
  - Use None inside critical tuple when only one side is defined e.g. (None, 100.0)
  - male == female when no gender difference exists
  - All ranges are consensus adult reference intervals; paediatric ranges differ
"""

KNOWN_TESTS: dict[str, dict] = {

    # ════════════════════════════════════════════════════════════════
    # CBC — Complete Blood Count
    # ════════════════════════════════════════════════════════════════

    "HAEMOGLOBIN": {
        "name": "Haemoglobin", "unit": "g/dL",
        "male": (14.0, 18.0), "female": (12.0, 16.0),
        "critical": (7.0, 20.0),
    },
    "HEMOGLOBIN": {
        "name": "Haemoglobin", "unit": "g/dL",
        "male": (14.0, 18.0), "female": (12.0, 16.0),
        "critical": (7.0, 20.0),
    },
    "HB": {
        "name": "Haemoglobin", "unit": "g/dL",
        "male": (14.0, 18.0), "female": (12.0, 16.0),
        "critical": (7.0, 20.0),
    },
    "WBC": {
        "name": "WBC (Total)", "unit": "x10^9/L",
        "male": (4.0, 11.0), "female": (4.0, 11.0),
        "critical": (2.0, 30.0),
    },
    "TLC": {
        "name": "WBC (Total)", "unit": "x10^9/L",
        "male": (4.0, 11.0), "female": (4.0, 11.0),
        "critical": (2.0, 30.0),
    },
    "RBC": {
        "name": "RBC", "unit": "x10^12/L",
        "male": (4.5, 5.5), "female": (3.8, 5.0),
        "critical": (2.0, 7.0),
    },
    "PLATELETS": {
        "name": "Platelets", "unit": "x10^9/L",
        "male": (150.0, 400.0), "female": (150.0, 400.0),
        "critical": (50.0, 1000.0),
    },
    "PLT": {
        "name": "Platelets", "unit": "x10^9/L",
        "male": (150.0, 400.0), "female": (150.0, 400.0),
        "critical": (50.0, 1000.0),
    },
    "HCT": {
        "name": "HCT/PCV", "unit": "%",
        "male": (40.0, 54.0), "female": (37.0, 47.0),
        "critical": (20.0, 60.0),
    },
    "PCV": {
        "name": "HCT/PCV", "unit": "%",
        "male": (40.0, 54.0), "female": (37.0, 47.0),
        "critical": (20.0, 60.0),
    },
    "HCT/PCV": {
        "name": "HCT/PCV", "unit": "%",
        "male": (40.0, 54.0), "female": (37.0, 47.0),
        "critical": (20.0, 60.0),
    },
    "MCV": {
        "name": "MCV", "unit": "fL",
        "male": (83.0, 101.0), "female": (83.0, 101.0),
        "critical": None,
    },
    "MCH": {
        "name": "MCH", "unit": "pg",
        "male": (27.0, 32.0), "female": (27.0, 32.0),
        "critical": None,
    },
    "MCHC": {
        "name": "MCHC", "unit": "g/dL",
        "male": (31.5, 34.5), "female": (31.5, 34.5),
        "critical": (20.0, 40.0),
    },
    "RDW-CV": {
        "name": "RDW-CV", "unit": "%",
        "male": (11.6, 14.0), "female": (11.6, 14.0),
        "critical": None,
    },
    "RDW-SD": {
        "name": "RDW-SD", "unit": "fL",
        "male": (39.0, 46.0), "female": (39.0, 46.0),
        "critical": None,
    },
    "MPV": {
        "name": "MPV", "unit": "fL",
        "male": (7.4, 10.4), "female": (7.4, 10.4),
        "critical": None,
    },
    "PCT": {
        "name": "PCT", "unit": "%",
        "male": (0.20, 0.50), "female": (0.20, 0.50),
        "critical": None,
    },
    "PDW": {
        "name": "PDW", "unit": "%",
        "male": (10.0, 18.0), "female": (10.0, 18.0),
        "critical": None,
    },

    # ── Differential WBC ──────────────────────────────────────────
    "NEUTROPHILS": {
        "name": "Neutrophils", "unit": "%",
        "male": (40.0, 70.0), "female": (40.0, 70.0),
        "critical": None,
    },
    "LYMPHOCYTES": {
        "name": "Lymphocytes", "unit": "%",
        "male": (20.0, 46.0), "female": (20.0, 46.0),
        "critical": None,
    },
    "MONOCYTES": {
        "name": "Monocytes", "unit": "%",
        "male": (2.0, 8.0), "female": (2.0, 8.0),
        "critical": None,
    },
    "EOSINOPHILS": {
        "name": "Eosinophils", "unit": "%",
        "male": (1.0, 6.0), "female": (1.0, 6.0),
        "critical": None,
    },
    "BASOPHILS": {
        "name": "Basophils", "unit": "%",
        "male": (0.0, 1.0), "female": (0.0, 1.0),
        "critical": None,
    },
    "BANDS": {
        "name": "Band Neutrophils", "unit": "%",
        "male": (0.0, 5.0), "female": (0.0, 5.0),
        "critical": None,
    },
    "BLASTS": {
        "name": "Blast Cells", "unit": "%",
        "male": (0.0, 0.0), "female": (0.0, 0.0),
        "critical": (None, 1.0),           # any blast cells = critical
    },

    # ── Inflammatory markers ───────────────────────────────────────
    "ESR": {
        "name": "ESR", "unit": "mm/hr",
        "male": (0.0, 10.0), "female": (0.0, 20.0),
        "critical": None,
    },
    "CRP": {
        "name": "CRP", "unit": "mg/L",
        "male": (0.0, 10.0), "female": (0.0, 10.0),
        "critical": (None, 100.0),
    },
    "PROCALCITONIN": {
        "name": "Procalcitonin", "unit": "ng/mL",
        "male": (0.0, 0.5), "female": (0.0, 0.5),
        "critical": (None, 2.0),
    },
    "PCT_SEPSIS": {   # alternate key when labs label it PCT for sepsis context
        "name": "Procalcitonin", "unit": "ng/mL",
        "male": (0.0, 0.5), "female": (0.0, 0.5),
        "critical": (None, 2.0),
    },
    "IL-6": {
        "name": "Interleukin-6", "unit": "pg/mL",
        "male": (0.0, 7.0), "female": (0.0, 7.0),
        "critical": (None, 100.0),
    },


    # ════════════════════════════════════════════════════════════════
    # LFT — Liver Function Tests
    # ════════════════════════════════════════════════════════════════

    "ALT": {
        "name": "ALT (SGPT)", "unit": "U/L",
        "male": (7.0, 56.0), "female": (7.0, 45.0),
        "critical": (None, 1000.0),
    },
    "SGPT": {
        "name": "ALT (SGPT)", "unit": "U/L",
        "male": (7.0, 56.0), "female": (7.0, 45.0),
        "critical": (None, 1000.0),
    },
    "AST": {
        "name": "AST (SGOT)", "unit": "U/L",
        "male": (10.0, 40.0), "female": (10.0, 35.0),
        "critical": (None, 1000.0),
    },
    "SGOT": {
        "name": "AST (SGOT)", "unit": "U/L",
        "male": (10.0, 40.0), "female": (10.0, 35.0),
        "critical": (None, 1000.0),
    },
    "ALP": {
        "name": "ALP", "unit": "U/L",
        "male": (44.0, 147.0), "female": (44.0, 147.0),
        "critical": None,
    },
    "GGT": {
        "name": "GGT", "unit": "U/L",
        "male": (8.0, 61.0), "female": (5.0, 36.0),
        "critical": None,
    },
    "BILIRUBIN": {
        "name": "Total Bilirubin", "unit": "mg/dL",
        "male": (0.2, 1.2), "female": (0.2, 1.2),
        "critical": (None, 15.0),
    },
    "DIRECT BILIRUBIN": {
        "name": "Direct Bilirubin", "unit": "mg/dL",
        "male": (0.0, 0.3), "female": (0.0, 0.3),
        "critical": None,
    },
    "INDIRECT BILIRUBIN": {
        "name": "Indirect Bilirubin", "unit": "mg/dL",
        "male": (0.2, 0.9), "female": (0.2, 0.9),
        "critical": None,
    },
    "ALBUMIN": {
        "name": "Albumin", "unit": "g/dL",
        "male": (3.5, 5.0), "female": (3.5, 5.0),
        "critical": (2.0, None),
    },
    "TOTAL PROTEIN": {
        "name": "Total Protein", "unit": "g/dL",
        "male": (6.0, 8.3), "female": (6.0, 8.3),
        "critical": None,
    },
    "GLOBULIN": {
        "name": "Globulin", "unit": "g/dL",
        "male": (2.0, 3.5), "female": (2.0, 3.5),
        "critical": None,
    },
    "AG RATIO": {
        "name": "A/G Ratio", "unit": "",
        "male": (1.0, 2.5), "female": (1.0, 2.5),
        "critical": None,
    },
    "LDH": {
        "name": "LDH", "unit": "U/L",
        "male": (140.0, 280.0), "female": (140.0, 280.0),
        "critical": (None, 1000.0),
    },


    # ════════════════════════════════════════════════════════════════
    # RFT — Renal Function Tests
    # ════════════════════════════════════════════════════════════════

    "CREATININE": {
        "name": "Creatinine", "unit": "mg/dL",
        "male": (0.7, 1.2), "female": (0.5, 1.0),
        "critical": (None, 10.0),
    },
    "SERUM CREATININE": {
        "name": "Creatinine", "unit": "mg/dL",
        "male": (0.7, 1.2), "female": (0.5, 1.0),
        "critical": (None, 10.0),
    },
    "UREA": {
        "name": "Blood Urea", "unit": "mg/dL",
        "male": (15.0, 45.0), "female": (15.0, 45.0),
        "critical": (None, 200.0),
    },
    "BUN": {
        "name": "BUN", "unit": "mg/dL",
        "male": (7.0, 20.0), "female": (7.0, 20.0),
        "critical": (None, 100.0),
    },
    "EGFR": {
        "name": "eGFR", "unit": "mL/min/1.73m²",
        "male": (60.0, 120.0), "female": (60.0, 120.0),
        "critical": (15.0, None),
    },
    "URIC ACID": {
        "name": "Uric Acid", "unit": "mg/dL",
        "male": (3.5, 7.2), "female": (2.6, 6.0),
        "critical": (None, 12.0),
    },
    "CYSTATIN C": {
        "name": "Cystatin C", "unit": "mg/L",
        "male": (0.62, 1.15), "female": (0.62, 1.15),
        "critical": None,
    },


    # ════════════════════════════════════════════════════════════════
    # TFT — Thyroid Function Tests
    # ════════════════════════════════════════════════════════════════

    "TSH": {
        "name": "TSH", "unit": "mIU/L",
        "male": (0.4, 4.0), "female": (0.4, 4.0),
        "critical": (0.1, 10.0),
    },
    "T3": {
        "name": "T3 (Total)", "unit": "nmol/L",
        "male": (1.2, 2.7), "female": (1.2, 2.7),
        "critical": None,
    },
    "T4": {
        "name": "T4 (Total)", "unit": "nmol/L",
        "male": (66.0, 181.0), "female": (66.0, 181.0),
        "critical": None,
    },
    "FREE T3": {
        "name": "Free T3 (FT3)", "unit": "pmol/L",
        "male": (3.1, 6.8), "female": (3.1, 6.8),
        "critical": None,
    },
    "FT3": {
        "name": "Free T3 (FT3)", "unit": "pmol/L",
        "male": (3.1, 6.8), "female": (3.1, 6.8),
        "critical": None,
    },
    "FREE T4": {
        "name": "Free T4 (FT4)", "unit": "pmol/L",
        "male": (12.0, 22.0), "female": (12.0, 22.0),
        "critical": None,
    },
    "FT4": {
        "name": "Free T4 (FT4)", "unit": "pmol/L",
        "male": (12.0, 22.0), "female": (12.0, 22.0),
        "critical": None,
    },
    "ANTI-TPO": {
        "name": "Anti-TPO Antibody", "unit": "IU/mL",
        "male": (0.0, 34.0), "female": (0.0, 34.0),
        "critical": None,
    },
    "ANTI-TG": {
        "name": "Anti-Thyroglobulin", "unit": "IU/mL",
        "male": (0.0, 115.0), "female": (0.0, 115.0),
        "critical": None,
    },
    "THYROGLOBULIN": {
        "name": "Thyroglobulin", "unit": "ng/mL",
        "male": (1.4, 78.0), "female": (1.4, 78.0),
        "critical": None,
    },


    # ════════════════════════════════════════════════════════════════
    # LIPID — Lipid Profile
    # ════════════════════════════════════════════════════════════════

    "CHOLESTEROL": {
        "name": "Total Cholesterol", "unit": "mg/dL",
        "male": (0.0, 200.0), "female": (0.0, 200.0),
        "critical": (None, 300.0),
    },
    "LDL": {
        "name": "LDL Cholesterol", "unit": "mg/dL",
        "male": (0.0, 100.0), "female": (0.0, 100.0),
        "critical": (None, 190.0),
    },
    "HDL": {
        "name": "HDL Cholesterol", "unit": "mg/dL",
        "male": (40.0, 999.0), "female": (50.0, 999.0),
        "critical": (30.0, None),
    },
    "TRIGLYCERIDES": {
        "name": "Triglycerides", "unit": "mg/dL",
        "male": (0.0, 150.0), "female": (0.0, 150.0),
        "critical": (None, 500.0),
    },
    "VLDL": {
        "name": "VLDL Cholesterol", "unit": "mg/dL",
        "male": (2.0, 30.0), "female": (2.0, 30.0),
        "critical": None,
    },
    "NON-HDL": {
        "name": "Non-HDL Cholesterol", "unit": "mg/dL",
        "male": (0.0, 130.0), "female": (0.0, 130.0),
        "critical": None,
    },
    "TC/HDL": {
        "name": "Total Cholesterol / HDL Ratio", "unit": "",
        "male": (0.0, 5.0), "female": (0.0, 4.5),
        "critical": None,
    },
    "LDL/HDL": {
        "name": "LDL / HDL Ratio", "unit": "",
        "male": (0.0, 3.5), "female": (0.0, 3.0),
        "critical": None,
    },
    "APOLIPOPROTEIN A1": {
        "name": "Apolipoprotein A1", "unit": "mg/dL",
        "male": (110.0, 205.0), "female": (108.0, 225.0),
        "critical": None,
    },
    "APOLIPOPROTEIN B": {
        "name": "Apolipoprotein B", "unit": "mg/dL",
        "male": (52.0, 109.0), "female": (52.0, 109.0),
        "critical": None,
    },
    "LIPOPROTEIN A": {
        "name": "Lipoprotein (a)", "unit": "mg/dL",
        "male": (0.0, 30.0), "female": (0.0, 30.0),
        "critical": None,
    },


    # ════════════════════════════════════════════════════════════════
    # DIABETES / GLUCOSE PANEL
    # ════════════════════════════════════════════════════════════════

    "GLUCOSE": {
        "name": "Glucose (Fasting)", "unit": "mg/dL",
        "male": (70.0, 100.0), "female": (70.0, 100.0),
        "critical": (40.0, 500.0),
    },
    "FBS": {
        "name": "Fasting Blood Sugar", "unit": "mg/dL",
        "male": (70.0, 100.0), "female": (70.0, 100.0),
        "critical": (40.0, 500.0),
    },
    "RBS": {
        "name": "Random Blood Sugar", "unit": "mg/dL",
        "male": (70.0, 140.0), "female": (70.0, 140.0),
        "critical": (40.0, 500.0),
    },
    "PPBS": {
        "name": "Post-Prandial Blood Sugar", "unit": "mg/dL",
        "male": (70.0, 140.0), "female": (70.0, 140.0),
        "critical": (40.0, 500.0),
    },
    "HBA1C": {
        "name": "HbA1c", "unit": "%",
        "male": (4.0, 5.7), "female": (4.0, 5.7),
        "critical": (None, 10.0),
    },
    "FRUCTOSAMINE": {
        "name": "Fructosamine", "unit": "µmol/L",
        "male": (200.0, 285.0), "female": (200.0, 285.0),
        "critical": None,
    },
    "INSULIN": {
        "name": "Fasting Insulin", "unit": "µIU/mL",
        "male": (2.6, 24.9), "female": (2.6, 24.9),
        "critical": None,
    },
    "C-PEPTIDE": {
        "name": "C-Peptide", "unit": "ng/mL",
        "male": (0.8, 3.5), "female": (0.8, 3.5),
        "critical": None,
    },


    # ════════════════════════════════════════════════════════════════
    # ELECTROLYTES & ABG
    # ════════════════════════════════════════════════════════════════

    "SODIUM": {
        "name": "Sodium (Na)", "unit": "mEq/L",
        "male": (136.0, 145.0), "female": (136.0, 145.0),
        "critical": (120.0, 160.0),
    },
    "POTASSIUM": {
        "name": "Potassium (K)", "unit": "mEq/L",
        "male": (3.5, 5.0), "female": (3.5, 5.0),
        "critical": (2.5, 6.5),
    },
    "CHLORIDE": {
        "name": "Chloride (Cl)", "unit": "mEq/L",
        "male": (98.0, 107.0), "female": (98.0, 107.0),
        "critical": (80.0, 115.0),
    },
    "BICARBONATE": {
        "name": "Bicarbonate (HCO3)", "unit": "mEq/L",
        "male": (22.0, 29.0), "female": (22.0, 29.0),
        "critical": (10.0, 40.0),
    },
    "CALCIUM": {
        "name": "Calcium", "unit": "mg/dL",
        "male": (8.5, 10.5), "female": (8.5, 10.5),
        "critical": (6.0, 13.0),
    },
    "IONISED CALCIUM": {
        "name": "Ionised Calcium", "unit": "mmol/L",
        "male": (1.12, 1.32), "female": (1.12, 1.32),
        "critical": (0.8, 1.6),
    },
    "MAGNESIUM": {
        "name": "Magnesium", "unit": "mg/dL",
        "male": (1.7, 2.2), "female": (1.7, 2.2),
        "critical": (1.0, 4.0),
    },
    "PHOSPHATE": {
        "name": "Phosphate", "unit": "mg/dL",
        "male": (2.5, 4.5), "female": (2.5, 4.5),
        "critical": (1.0, 8.0),
    },
    "PH": {
        "name": "Blood pH", "unit": "",
        "male": (7.35, 7.45), "female": (7.35, 7.45),
        "critical": (7.2, 7.6),
    },
    "PAO2": {
        "name": "PaO2", "unit": "mmHg",
        "male": (75.0, 100.0), "female": (75.0, 100.0),
        "critical": (50.0, None),
    },
    "PACO2": {
        "name": "PaCO2", "unit": "mmHg",
        "male": (35.0, 45.0), "female": (35.0, 45.0),
        "critical": (20.0, 70.0),
    },
    "SPO2": {
        "name": "SpO2", "unit": "%",
        "male": (95.0, 100.0), "female": (95.0, 100.0),
        "critical": (88.0, None),
    },
    "BASE EXCESS": {
        "name": "Base Excess", "unit": "mEq/L",
        "male": (-2.0, 2.0), "female": (-2.0, 2.0),
        "critical": (-10.0, 10.0),
    },
    "LACTATE": {
        "name": "Lactate", "unit": "mmol/L",
        "male": (0.5, 2.0), "female": (0.5, 2.0),
        "critical": (None, 4.0),
    },
    "ANION GAP": {
        "name": "Anion Gap", "unit": "mEq/L",
        "male": (8.0, 16.0), "female": (8.0, 16.0),
        "critical": (None, 25.0),
    },


    # ════════════════════════════════════════════════════════════════
    # COAGULATION — Clotting Studies
    # ════════════════════════════════════════════════════════════════

    "INR": {
        "name": "INR", "unit": "",
        "male": (0.8, 1.2), "female": (0.8, 1.2),
        "critical": (None, 5.0),
    },
    "PT": {
        "name": "Prothrombin Time", "unit": "sec",
        "male": (11.0, 13.5), "female": (11.0, 13.5),
        "critical": (None, 30.0),
    },
    "APTT": {
        "name": "APTT", "unit": "sec",
        "male": (25.0, 35.0), "female": (25.0, 35.0),
        "critical": (None, 80.0),
    },
    "FIBRINOGEN": {
        "name": "Fibrinogen", "unit": "mg/dL",
        "male": (200.0, 400.0), "female": (200.0, 400.0),
        "critical": (100.0, None),
    },
    "D-DIMER": {
        "name": "D-Dimer", "unit": "µg/mL",
        "male": (0.0, 0.5), "female": (0.0, 0.5),
        "critical": (None, 4.0),
    },
    "BLEEDING TIME": {
        "name": "Bleeding Time", "unit": "min",
        "male": (1.0, 6.0), "female": (1.0, 6.0),
        "critical": (None, 15.0),
    },
    "CLOTTING TIME": {
        "name": "Clotting Time", "unit": "min",
        "male": (8.0, 15.0), "female": (8.0, 15.0),
        "critical": (None, 30.0),
    },
    "ANTI-XA": {
        "name": "Anti-Xa (LMWH level)", "unit": "IU/mL",
        "male": (0.5, 1.0), "female": (0.5, 1.0),
        "critical": None,
    },


    # ════════════════════════════════════════════════════════════════
    # CARDIAC MARKERS
    # ════════════════════════════════════════════════════════════════

    "TROPONIN I": {
        "name": "Troponin I", "unit": "ng/mL",
        "male": (0.0, 0.04), "female": (0.0, 0.04),
        "critical": (None, 0.4),
    },
    "TROPONIN T": {
        "name": "Troponin T", "unit": "ng/mL",
        "male": (0.0, 0.01), "female": (0.0, 0.01),
        "critical": (None, 0.1),
    },
    "HS-TROPONIN": {
        "name": "hs-Troponin", "unit": "ng/L",
        "male": (0.0, 14.0), "female": (0.0, 14.0),
        "critical": (None, 52.0),
    },
    "CK": {
        "name": "Creatine Kinase (CK)", "unit": "U/L",
        "male": (38.0, 174.0), "female": (26.0, 140.0),
        "critical": (None, 1000.0),
    },
    "CK-MB": {
        "name": "CK-MB", "unit": "U/L",
        "male": (0.0, 25.0), "female": (0.0, 25.0),
        "critical": (None, 50.0),
    },
    "MYOGLOBIN": {
        "name": "Myoglobin", "unit": "ng/mL",
        "male": (28.0, 72.0), "female": (25.0, 58.0),
        "critical": (None, 200.0),
    },
    "BNP": {
        "name": "BNP", "unit": "pg/mL",
        "male": (0.0, 100.0), "female": (0.0, 100.0),
        "critical": (None, 400.0),
    },
    "NT-PROBNP": {
        "name": "NT-proBNP", "unit": "pg/mL",
        "male": (0.0, 125.0), "female": (0.0, 125.0),
        "critical": (None, 900.0),
    },
    "HOMOCYSTEINE": {
        "name": "Homocysteine", "unit": "µmol/L",
        "male": (5.0, 15.0), "female": (5.0, 12.0),
        "critical": (None, 50.0),
    },
    "HS-CRP": {
        "name": "hs-CRP", "unit": "mg/L",
        "male": (0.0, 3.0), "female": (0.0, 3.0),
        "critical": (None, 10.0),
    },


    # ════════════════════════════════════════════════════════════════
    # IRON STUDIES
    # ════════════════════════════════════════════════════════════════

    "SERUM IRON": {
        "name": "Serum Iron", "unit": "µg/dL",
        "male": (60.0, 170.0), "female": (50.0, 170.0),
        "critical": (None, 350.0),
    },
    "TIBC": {
        "name": "TIBC", "unit": "µg/dL",
        "male": (250.0, 370.0), "female": (250.0, 370.0),
        "critical": None,
    },
    "TRANSFERRIN SATURATION": {
        "name": "Transferrin Saturation", "unit": "%",
        "male": (20.0, 50.0), "female": (15.0, 50.0),
        "critical": None,
    },
    "FERRITIN": {
        "name": "Ferritin", "unit": "ng/mL",
        "male": (24.0, 336.0), "female": (11.0, 307.0),
        "critical": (None, 1000.0),
    },
    "TRANSFERRIN": {
        "name": "Transferrin", "unit": "mg/dL",
        "male": (200.0, 360.0), "female": (200.0, 360.0),
        "critical": None,
    },


    # ════════════════════════════════════════════════════════════════
    # HORMONES — Reproductive & Adrenal
    # ════════════════════════════════════════════════════════════════

    "FSH": {
        "name": "FSH", "unit": "mIU/mL",
        "male": (1.5, 12.4), "female": (3.5, 12.5),   # follicular phase female
        "critical": None,
    },
    "LH": {
        "name": "LH", "unit": "mIU/mL",
        "male": (1.7, 8.6), "female": (2.4, 12.6),
        "critical": None,
    },
    "PROLACTIN": {
        "name": "Prolactin", "unit": "ng/mL",
        "male": (2.0, 18.0), "female": (2.0, 29.0),
        "critical": None,
    },
    "TESTOSTERONE": {
        "name": "Testosterone (Total)", "unit": "ng/dL",
        "male": (280.0, 1100.0), "female": (15.0, 70.0),
        "critical": None,
    },
    "FREE TESTOSTERONE": {
        "name": "Free Testosterone", "unit": "pg/mL",
        "male": (9.0, 30.0), "female": (0.0, 4.2),
        "critical": None,
    },
    "ESTRADIOL": {
        "name": "Estradiol (E2)", "unit": "pg/mL",
        "male": (10.0, 40.0), "female": (30.0, 400.0),
        "critical": None,
    },
    "PROGESTERONE": {
        "name": "Progesterone", "unit": "ng/mL",
        "male": (0.0, 0.5), "female": (0.1, 25.0),
        "critical": None,
    },
    "DHEA-S": {
        "name": "DHEA-S", "unit": "µg/dL",
        "male": (80.0, 560.0), "female": (35.0, 430.0),
        "critical": None,
    },
    "CORTISOL": {
        "name": "Cortisol (AM)", "unit": "µg/dL",
        "male": (6.0, 23.0), "female": (6.0, 23.0),
        "critical": (2.0, 50.0),
    },
    "ACTH": {
        "name": "ACTH", "unit": "pg/mL",
        "male": (7.2, 63.3), "female": (7.2, 63.3),
        "critical": None,
    },
    "ALDOSTERONE": {
        "name": "Aldosterone", "unit": "ng/dL",
        "male": (1.0, 21.0), "female": (1.0, 21.0),
        "critical": None,
    },
    "RENIN": {
        "name": "Plasma Renin Activity", "unit": "ng/mL/hr",
        "male": (0.2, 3.3), "female": (0.2, 3.3),
        "critical": None,
    },
    "BETA HCG": {
        "name": "Beta-hCG", "unit": "mIU/mL",
        "male": (0.0, 5.0), "female": (0.0, 5.0),     # non-pregnant female
        "critical": None,
    },
    "AMH": {
        "name": "Anti-Müllerian Hormone", "unit": "ng/mL",
        "male": (0.7, 19.0), "female": (0.9, 9.5),
        "critical": None,
    },
    "IGF-1": {
        "name": "IGF-1", "unit": "ng/mL",
        "male": (116.0, 358.0), "female": (116.0, 358.0),
        "critical": None,
    },
    "GROWTH HORMONE": {
        "name": "Growth Hormone", "unit": "ng/mL",
        "male": (0.0, 3.0), "female": (0.0, 8.0),
        "critical": None,
    },
    "PTH": {
        "name": "Parathyroid Hormone", "unit": "pg/mL",
        "male": (15.0, 65.0), "female": (15.0, 65.0),
        "critical": (None, 500.0),
    },


    # ════════════════════════════════════════════════════════════════
    # VITAMINS & MINERALS
    # ════════════════════════════════════════════════════════════════

    "VITAMIN D": {
        "name": "Vitamin D (25-OH)", "unit": "ng/mL",
        "male": (30.0, 100.0), "female": (30.0, 100.0),
        "critical": (10.0, None),
    },
    "VITAMIN B12": {
        "name": "Vitamin B12", "unit": "pg/mL",
        "male": (200.0, 900.0), "female": (200.0, 900.0),
        "critical": (100.0, None),
    },
    "FOLATE": {
        "name": "Folate (Folic Acid)", "unit": "ng/mL",
        "male": (2.7, 17.0), "female": (2.7, 17.0),
        "critical": (2.0, None),
    },
    "VITAMIN A": {
        "name": "Vitamin A (Retinol)", "unit": "µg/dL",
        "male": (30.0, 65.0), "female": (30.0, 65.0),
        "critical": None,
    },
    "VITAMIN E": {
        "name": "Vitamin E (Tocopherol)", "unit": "mg/L",
        "male": (5.5, 17.0), "female": (5.5, 17.0),
        "critical": None,
    },
    "VITAMIN C": {
        "name": "Vitamin C", "unit": "mg/dL",
        "male": (0.4, 2.0), "female": (0.4, 2.0),
        "critical": None,
    },
    "ZINC": {
        "name": "Zinc", "unit": "µg/dL",
        "male": (70.0, 120.0), "female": (70.0, 120.0),
        "critical": None,
    },
    "COPPER": {
        "name": "Copper", "unit": "µg/dL",
        "male": (70.0, 140.0), "female": (80.0, 155.0),
        "critical": None,
    },
    "SELENIUM": {
        "name": "Selenium", "unit": "µg/L",
        "male": (70.0, 150.0), "female": (70.0, 150.0),
        "critical": None,
    },


    # ════════════════════════════════════════════════════════════════
    # URINE — Urinalysis (quantitative values)
    # ════════════════════════════════════════════════════════════════

    "URINE PROTEIN": {
        "name": "Urine Protein", "unit": "mg/dL",
        "male": (0.0, 14.0), "female": (0.0, 14.0),
        "critical": (None, 300.0),
    },
    "URINE GLUCOSE": {
        "name": "Urine Glucose", "unit": "mg/dL",
        "male": (0.0, 15.0), "female": (0.0, 15.0),
        "critical": None,
    },
    "URINE CREATININE": {
        "name": "Urine Creatinine", "unit": "mg/dL",
        "male": (40.0, 300.0), "female": (40.0, 300.0),
        "critical": None,
    },
    "ACR": {
        "name": "Albumin:Creatinine Ratio", "unit": "mg/g",
        "male": (0.0, 30.0), "female": (0.0, 30.0),
        "critical": (None, 300.0),
    },
    "MICROALBUMIN": {
        "name": "Microalbumin", "unit": "mg/L",
        "male": (0.0, 20.0), "female": (0.0, 20.0),
        "critical": None,
    },
    "SPECIFIC GRAVITY": {
        "name": "Specific Gravity", "unit": "",
        "male": (1.005, 1.030), "female": (1.005, 1.030),
        "critical": None,
    },
    "URINE PH": {
        "name": "Urine pH", "unit": "",
        "male": (4.5, 8.0), "female": (4.5, 8.0),
        "critical": None,
    },
    "24H PROTEIN": {
        "name": "24h Urine Protein", "unit": "mg/24hr",
        "male": (0.0, 150.0), "female": (0.0, 150.0),
        "critical": (None, 3500.0),
    },


    # ════════════════════════════════════════════════════════════════
    # TUMOUR MARKERS
    # ════════════════════════════════════════════════════════════════

    "PSA": {
        "name": "PSA (Total)", "unit": "ng/mL",
        "male": (0.0, 4.0), "female": (0.0, 4.0),
        "critical": (None, 10.0),
    },
    "FREE PSA": {
        "name": "Free PSA", "unit": "ng/mL",
        "male": (0.0, 1.0), "female": (0.0, 1.0),
        "critical": None,
    },
    "CEA": {
        "name": "CEA", "unit": "ng/mL",
        "male": (0.0, 3.0), "female": (0.0, 3.0),
        "critical": (None, 20.0),
    },
    "AFP": {
        "name": "AFP (Alpha-Fetoprotein)", "unit": "ng/mL",
        "male": (0.0, 7.0), "female": (0.0, 7.0),
        "critical": (None, 400.0),
    },
    "CA-125": {
        "name": "CA-125", "unit": "U/mL",
        "male": (0.0, 35.0), "female": (0.0, 35.0),
        "critical": (None, 200.0),
    },
    "CA 19-9": {
        "name": "CA 19-9", "unit": "U/mL",
        "male": (0.0, 37.0), "female": (0.0, 37.0),
        "critical": (None, 200.0),
    },
    "CA 15-3": {
        "name": "CA 15-3", "unit": "U/mL",
        "male": (0.0, 30.0), "female": (0.0, 30.0),
        "critical": None,
    },
    "HE4": {
        "name": "HE4", "unit": "pmol/L",
        "male": (0.0, 70.0), "female": (0.0, 70.0),
        "critical": None,
    },
    "CYFRA 21-1": {
        "name": "CYFRA 21-1", "unit": "ng/mL",
        "male": (0.0, 3.3), "female": (0.0, 3.3),
        "critical": None,
    },


    # ════════════════════════════════════════════════════════════════
    # IMMUNOLOGY / SEROLOGY / INFECTION
    # ════════════════════════════════════════════════════════════════

    "ANA": {
        "name": "ANA (Antinuclear Antibody)", "unit": "titre",
        "male": (0.0, 1.0), "female": (0.0, 1.0),    # titre < 1:40 negative
        "critical": None,
    },
    "ANTI-DS DNA": {
        "name": "Anti-dsDNA", "unit": "IU/mL",
        "male": (0.0, 7.0), "female": (0.0, 7.0),
        "critical": None,
    },
    "RF": {
        "name": "Rheumatoid Factor", "unit": "IU/mL",
        "male": (0.0, 14.0), "female": (0.0, 14.0),
        "critical": None,
    },
    "ANTI-CCP": {
        "name": "Anti-CCP Antibody", "unit": "U/mL",
        "male": (0.0, 20.0), "female": (0.0, 20.0),
        "critical": None,
    },
    "ASO": {
        "name": "ASO Titre", "unit": "IU/mL",
        "male": (0.0, 200.0), "female": (0.0, 200.0),
        "critical": None,
    },
    "COMPLEMENT C3": {
        "name": "Complement C3", "unit": "mg/dL",
        "male": (90.0, 180.0), "female": (90.0, 180.0),
        "critical": None,
    },
    "COMPLEMENT C4": {
        "name": "Complement C4", "unit": "mg/dL",
        "male": (16.0, 47.0), "female": (16.0, 47.0),
        "critical": None,
    },
    "IGA": {
        "name": "IgA", "unit": "mg/dL",
        "male": (70.0, 400.0), "female": (70.0, 400.0),
        "critical": None,
    },
    "IGG": {
        "name": "IgG", "unit": "mg/dL",
        "male": (700.0, 1600.0), "female": (700.0, 1600.0),
        "critical": (None, 3000.0),
    },
    "IGM": {
        "name": "IgM", "unit": "mg/dL",
        "male": (40.0, 230.0), "female": (40.0, 230.0),
        "critical": None,
    },
    "IGE": {
        "name": "IgE (Total)", "unit": "IU/mL",
        "male": (0.0, 100.0), "female": (0.0, 100.0),
        "critical": None,
    },
    "CD4": {
        "name": "CD4 Count", "unit": "cells/µL",
        "male": (500.0, 1500.0), "female": (500.0, 1500.0),
        "critical": (200.0, None),
    },
    "WIDAL": {
        "name": "Widal Test (S. Typhi O)", "unit": "titre",
        "male": (0.0, 80.0), "female": (0.0, 80.0),   # titre ≤ 1:80 considered negative
        "critical": None,
    },
    "DENGUE NS1": {
        "name": "Dengue NS1 Antigen", "unit": "index",
        "male": (0.0, 1.0), "female": (0.0, 1.0),
        "critical": None,
    },
    "MALARIA": {
        "name": "Malaria Antigen", "unit": "index",
        "male": (0.0, 1.0), "female": (0.0, 1.0),
        "critical": None,
    },


    # ════════════════════════════════════════════════════════════════
    # SPECIALISED HAEMATOLOGY
    # ════════════════════════════════════════════════════════════════

    "RETICULOCYTES": {
        "name": "Reticulocyte Count", "unit": "%",
        "male": (0.5, 2.5), "female": (0.5, 2.5),
        "critical": None,
    },
    "ABSOLUTE RETICULOCYTES": {
        "name": "Absolute Reticulocyte Count", "unit": "x10^9/L",
        "male": (25.0, 75.0), "female": (25.0, 75.0),
        "critical": None,
    },
    "HAPTOGLOBIN": {
        "name": "Haptoglobin", "unit": "mg/dL",
        "male": (30.0, 200.0), "female": (30.0, 200.0),
        "critical": None,
    },
    "COOMBS DIRECT": {
        "name": "Direct Coombs Test", "unit": "titre",
        "male": (0.0, 0.0), "female": (0.0, 0.0),     # should be negative
        "critical": None,
    },
    "G6PD": {
        "name": "G6PD Activity", "unit": "U/g Hb",
        "male": (4.6, 13.5), "female": (4.6, 13.5),
        "critical": (2.0, None),
    },
    "SICKLING TEST": {
        "name": "Sickling Test", "unit": "",
        "male": (0.0, 0.0), "female": (0.0, 0.0),
        "critical": None,
    },
    "HB ELECTROPHORESIS": {
        "name": "Hb Electrophoresis (HbA)", "unit": "%",
        "male": (95.0, 100.0), "female": (95.0, 100.0),
        "critical": (70.0, None),
    },


    # ════════════════════════════════════════════════════════════════
    # VITALS / ANTHROPOMETRIC
    # ════════════════════════════════════════════════════════════════

    "BMI": {
        "name": "BMI", "unit": "kg/m²",
        "male": (18.5, 24.9), "female": (18.5, 24.9),
        "critical": (14.0, 40.0),
    },
    "PULSE": {
        "name": "Pulse Rate", "unit": "bpm",
        "male": (60.0, 100.0), "female": (60.0, 100.0),
        "critical": (40.0, 150.0),
    },
    "TEMPERATURE": {
        "name": "Temperature", "unit": "°C",
        "male": (36.1, 37.2), "female": (36.1, 37.2),
        "critical": (35.0, 40.0),
    },
    "RESPIRATORY RATE": {
        "name": "Respiratory Rate", "unit": "breaths/min",
        "male": (12.0, 20.0), "female": (12.0, 20.0),
        "critical": (8.0, 30.0),
    },
}