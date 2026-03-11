export const MOCK_MIXED = {
  is_mixed: true,
  patient: {
    name: "GRANTHANA RAHMAN",
    age_years: 24,
    gender: "female",
    collection_date: "2024-11-06",
  },
  sections: {
    LAB: [
      {
        report_type: "LAB",
        summary:
          "Most blood parameters are within normal reference ranges. However, your ESR is elevated, suggesting possible inflammation.",
        risk_level: "Medium",
        advice:
          "Consult a doctor regarding the elevated ESR to determine if further evaluation is needed.",
        tests_analysis: [
          {
            test_name: "Haemoglobin",
            value: 13.2,
            unit: "g/dL",
            reference_range: "11.5–15.5 g/dL (F)",
            status: "Normal",
            keyword_explanation:
              "Hemoglobin is a protein in red blood cells that carries oxygen throughout the body. Low levels can indicate anemia; high levels may signal dehydration.",
            result_explanation:
              "Your hemoglobin of 13.2 g/dL is within the normal female range, indicating healthy oxygen-carrying capacity.",
          },
          {
            test_name: "ESR",
            value: 47,
            unit: "mm/hr",
            reference_range: "0–20 mm/hr (F)",
            status: "High",
            keyword_explanation:
              "Erythrocyte Sedimentation Rate (ESR) is a non-specific marker of inflammation or infection. Elevated values suggest the body may be fighting an infection or autoimmune condition.",
            result_explanation:
              "Your ESR of 47 mm/hr is above normal for females (0–20 mm/hr). This may indicate ongoing inflammation or infection — further investigation is recommended.",
          },
          {
            test_name: "WBC",
            value: 10.74,
            unit: "×10⁹/L",
            reference_range: "4.00–11.00 ×10⁹/L",
            status: "Normal",
            keyword_explanation:
              "White Blood Cells are immune cells that fight infections. High counts can indicate infection or stress; low counts may signal bone marrow issues.",
            result_explanation:
              "Your WBC count of 10.74 ×10⁹/L is within the normal range, indicating a healthy immune response.",
          },
          {
            test_name: "RBC",
            value: 4.76,
            unit: "×10¹²/L",
            reference_range: "3.8–5.0 ×10¹²/L (F)",
            status: "Normal",
            keyword_explanation:
              "Red Blood Cells carry hemoglobin and transport oxygen. Abnormal counts can reflect anemia, dehydration, or lung conditions.",
            result_explanation:
              "Your RBC count of 4.76 ×10¹²/L is within the normal female range.",
          },
          {
            test_name: "Platelets",
            value: 367,
            unit: "×10⁹/L",
            reference_range: "150–450 ×10⁹/L",
            status: "Normal",
            keyword_explanation:
              "Platelets are cell fragments responsible for blood clotting. High counts increase clot risk; low counts can cause excessive bleeding.",
            result_explanation:
              "Your platelet count of 367 ×10⁹/L is within the normal range, indicating healthy clotting ability.",
          },
          {
            test_name: "Neutrophil",
            value: 68,
            unit: "%",
            reference_range: "40–75%",
            status: "Normal",
            keyword_explanation:
              "Neutrophils are the first responders to bacterial infection and inflammation.",
            result_explanation:
              "Your neutrophil percentage of 68% is within the normal range.",
          },
          {
            test_name: "Lymphocyte",
            value: 23,
            unit: "%",
            reference_range: "20–50%",
            status: "Normal",
            keyword_explanation:
              "Lymphocytes are immune cells that fight viral infections and build long-term immunity.",
            result_explanation:
              "Your lymphocyte percentage of 23% is within the normal range.",
          },
          {
            test_name: "Phosphate",
            value: 3.5,
            unit: "mg/dl",
            reference_range: "2.6–4.5 mg/dl",
            status: "Normal",
            keyword_explanation:
              "Phosphate is a mineral vital for bone health, energy production, and nerve/muscle function.",
            result_explanation:
              "Your phosphate level of 3.5 mg/dl is within the normal adult range.",
          },
        ],
      },
    ],
    IMAGING: [
      {
        report_type: "IMAGING",
        summary:
          "Chest X-ray shows right basal pleural reaction. PNS X-ray suggests chronic rhinitis with mild deviated nasal septum.",
        risk_level: "Medium",
        advice:
          "Correlate findings with clinical symptoms. Consult a pulmonologist for the pleural reaction.",
        tests_analysis: [
          {
            test_name: "Chest X-Ray (PA View)",
            value: "Abnormal",
            unit: "",
            reference_range: "Clear lung fields",
            status: "Abnormal",
            keyword_explanation:
              "A chest X-ray images the lungs, heart, and thoracic structures. Opacities or blunted angles can indicate fluid, infection, or inflammation.",
            result_explanation:
              "Small dense opacities in the right lower zone with obliteration of the right CP angle are noted — consistent with Right Basal Pleural Reaction (irritation/fluid around the lung lining).",
          },
          {
            test_name: "Diaphragm",
            value: "Normal",
            unit: "",
            reference_range: "Normal position",
            status: "Normal",
            keyword_explanation:
              "The diaphragm separates the chest from the abdomen and is the main breathing muscle. Its position on X-ray helps assess lung volume.",
            result_explanation:
              "Diaphragm is normal in position with smooth contour of both domes.",
          },
          {
            test_name: "Heart Size",
            value: "Normal",
            unit: "",
            reference_range: "Normal transverse diameter",
            status: "Normal",
            keyword_explanation:
              "Heart size is assessed on X-ray to detect enlargement, which can indicate cardiac conditions.",
            result_explanation:
              "Heart appears of normal size based on transverse diameter.",
          },
          {
            test_name: "PNS X-Ray (O/M View)",
            value: "Abnormal",
            unit: "",
            reference_range: "Clear sinuses",
            status: "Abnormal",
            keyword_explanation:
              "Paranasal sinus X-ray examines the air-filled spaces around the nose for fluid, infection, or structural issues.",
            result_explanation:
              "All sinuses are clear. However, mild hypertrophy of inferior turbinates and mild DNS (convexity to left) are noted — suggestive of Chronic Rhinitis with mild DNS.",
          },
        ],
      },
    ],
  },
  summary: {
    total_tests: 12,
    abnormal_count: 3,
    critical_count: 0,
    has_critical: false,
  },
};

export const MOCK_SINGLE = {
  is_mixed: false,
  patient: {
    name: "GRANTHANA RAHMAN",
    age_years: 24,
    gender: "female",
    collection_date: "2024-11-07",
  },
  report: {
    report_type: "LAB",
    sub_type: "ELECTROLYTES",
    summary:
      "Your Phosphate (Inorganic) level is within the normal range for an adult.",
    risk_level: "Low",
    advice:
      "Normal results. Always discuss lab results with your doctor if you have concerns.",
    tests_analysis: [
      {
        test_name: "Phosphate (Inorganic)",
        value: 3.5,
        unit: "mg/dl",
        reference_range: "Adult: 2.6–4.5 mg/dl",
        status: "Normal",
        keyword_explanation:
          "Phosphate is an essential electrolyte crucial for bone formation, energy storage, nerve and muscle function, and acid-base balance. High levels can be due to kidney disease; low levels can result from vitamin D deficiency or malnutrition.",
        result_explanation:
          "Your phosphate level of 3.5 mg/dl falls within the normal adult range (2.6–4.5 mg/dl), indicating a healthy phosphate balance.",
      },
    ],
  },
  summary: {
    total_tests: 1,
    abnormal_count: 0,
    critical_count: 0,
    has_critical: false,
  },
};
