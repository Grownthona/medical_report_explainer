export const MOCK_SAMPLES = {
  // 1. For Multiple image file (Mixed Report)
  MULTIPLE_IMAGE_MIXED: {
    "is_mixed": true,
    "document_type": {
      "category": "LAB + IMAGING",
      "sub_type": "MIXED",
      "confidence": "MEDIUM",
      "is_mixed": true
    },
    "patient": {
      "name": "GRANTHANA RAHMAN Invoice No",
      "age_years": 24,
      "gender": "female",
      "report_type": null,
      "collection_date": "2024-11-07",
      "referred_by": null,
      "lab_no": null,
      "invoice_no": null
    },
    "sections": {
      "LAB": [
        {
          "summary": "Biochemical analysis showing phosphate levels.",
          "voice_explanation": "Your phosphate level is within the normal adult range, but slightly lower than pediatric reference values.",
          "tests_analysis": [],
          "risk_level": "Unknown",
          "advice": "Correlate with clinical findings.",
          "raw_text": "Biochemical Analysis Report...",
          "metadata": { "gender": "female", "confidence": "LOW" },
          "lab_values": []
        }
      ],
      "IMAGING": [
        {
          "summary": "X-RAY report showing small dense homogenous opacities in right lower zone.",
          "voice_explanation": "The X-ray shows some findings in the lower right part of your chest that might suggest a pleural reaction. This should be checked against your symptoms.",
          "tests_analysis": [],
          "risk_level": "Unknown",
          "advice": "Please correlate with clinical and laboratory findings.",
          "raw_text": "X-RAY REPORT...",
          "metadata": { "gender": "female", "confidence": "LOW" }
        }
      ]
    },
    "summary": {
      "total_tests": 0,
      "abnormal_count": 0,
      "critical_count": 0,
      "has_critical": false
    },
    "is_multi_patient": false
  },

  // 2. For multiple patient report
  MULTI_PATIENT: {
    "is_multi_patient": true,
    "total_patients": 2,
    "patients": [
      {
        "is_mixed": false,
        "document_type": { "category": "CLINICAL", "sub_type": "PROGRESS", "confidence": "HIGH", "is_mixed": false },
        "patient": { "name": "John Doe", "age_years": null, "gender": "male", "report_type": "PROGRESS" },
        "report": {
          "summary": "Patient reports persistent lower back pain for 3 weeks.",
          "voice_explanation": "John is experiencing sharp lower back pain radiating to his left leg. The diagnosis is a lumbar strain.",
          "tests_analysis": [
            { "test_name": "Finding 1", "result_explanation": "Chief Complaint: Persistent lower back pain." },
            { "test_name": "Finding 6", "result_explanation": "Primary Diagnosis: Lumbar Strain (ICD-10: M54.50)." }
          ],
          "risk_level": "Unknown",
          "advice": "Physical Therapy (2x weekly for 4 weeks)."
        },
        "sections": {},
        "summary": { "total_tests": 8, "abnormal_count": 0, "critical_count": 0, "has_critical": false },
        "patient_index": 0
      },
      {
        "is_mixed": false,
        "document_type": { "category": "CLINICAL", "sub_type": "PROGRESS", "confidence": "HIGH", "is_mixed": false },
        "patient": { "name": "GR Rahman", "age_years": 24, "gender": "female", "report_type": "PROGRESS" },
        "report": {
          "summary": "Similar clinical presentation as previous case with slight variations in vitals.",
          "voice_explanation": "This patient also has lumbar strain symptoms. Vitals are stable but pain is significant.",
          "tests_analysis": [
            { "test_name": "Finding 4", "result_explanation": "Vital Signs: BP: 125/80 mmHg | HR: 72 bpm" }
          ],
          "risk_level": "Unknown",
          "advice": "Follow-up in 14 days."
        },
        "sections": {},
        "summary": { "total_tests": 8, "abnormal_count": 0, "critical_count": 0, "has_critical": false },
        "patient_index": 1
      }
    ]
  },

  // 3. Single report proper data demo
  SINGLE_REPORT_PROPER: {
    "is_mixed": false,
    "document_type": {
      "category": "LAB",
      "sub_type": "CBC",
      "confidence": "HIGH",
      "is_mixed": false
    },
    "patient": {
      "name": "GRANTHANA RAHMAN",
      "age_years": 24,
      "gender": "female",
      "collection_date": "2024-11-05",
      "referred_by": "DR.MD.AZIZUL KAHHAR",
      "lab_no": "22411208208",
      "invoice_no": "D2411127699"
    },
    "report": {
      "summary": "This report shows that most of your blood test results are within the normal range. However, your ESR is elevated.",
      "voice_explanation": "Hello. Your blood test results are mostly normal, which is good news. Your red blood cells, white blood cells, and platelets are all within healthy ranges. The only finding that stands out is your ESR, or Erythrocyte Sedimentation Rate, which is a bit high. This can sometimes indicate inflammation or infection in the body.",
      "tests_analysis": [
        {
          "test_name": "Total Count (WBC)",
          "value": 10.74,
          "unit": "X10^9/L",
          "reference_range": "4.00-11.00X10^9/L",
          "status": "Normal",
          "keyword_explanation": "White Blood Cells fight infections.",
          "result_explanation": "Your White Blood Cell count is normal."
        },
        {
          "test_name": "ESR (Erythrocyte Sedimentation Rate)",
          "value": 47.0,
          "unit": "mm in 1st hr.",
          "reference_range": "0-20 mm in 1st hr.",
          "status": "High",
          "keyword_explanation": "ESR is a marker for inflammation.",
          "result_explanation": "Your ESR is 47 mm, which is higher than normal."
        }
      ],
      "risk_level": "Medium",
      "advice": "Consult with your doctor regarding the elevated ESR.",
      "raw_text": "HAEMATOLOGYREPORT..."
    },
    "summary": {
      "total_tests": 16,
      "abnormal_count": 1,
      "critical_count": 0,
      "has_critical": false
    }
  }
};
