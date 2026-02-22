
const { GoogleGenerativeAI } = require("@google/generative-ai");

require("dotenv").config();

const genAI = new GoogleGenerativeAI(process.env.GEMINI_API_KEY);

const model = genAI.getGenerativeModel({
  model: "gemini-2.5-flash", // better than gemini-pro 
    generationConfig: {
        temperature: 0.2,
    }
})

const testResult = {
  "summary": "The medical report includes both blood test results and an X-ray report for Ms. Farah Dira Rahman, a 50-year-old female. Most of the blood parameters, including hemoglobin, red blood cell count, total white blood cell count, platelet count, and various red blood cell indices, are within their normal reference ranges. However, the Erythrocyte Sedimentation Rate (ESR) is elevated, and the Mean Platelet Volume (MPV) is slightly high. The X-ray of the lumbar spine reveals degenerative changes, including bone spurs (osteophytes), sacralization of the L5 vertebra, a forward slip of the L4 vertebra over L5, and signs of inflammation in both sacroiliac joints (bilateral sacroiliitis). The disc spaces are noted as normal.",
  "tests_analysis": [
    {
      "test_name": "Haemoglobin",
      "value": 12.30,
      "unit": "gm/dl",
      "reference_range": "Female: 12.00 - 15.00 gm/dl",
      "status": "Normal",
      "keyword_explanation": "Haemoglobin is a protein found in red blood cells that is responsible for carrying oxygen from the lungs to the rest of the body's tissues and organs. It is a crucial component of the circulatory system. A high level might indicate dehydration or certain lung conditions, while a low level is often associated with anemia, blood loss, or nutritional deficiencies. Symptoms of low haemoglobin can include fatigue, shortness of breath, and pale skin, while high levels might cause dizziness or headaches.",
      "result_explanation": "The patient's haemoglobin level is 12.30 gm/dl, which falls within the normal reference range for females (12.00 - 15.00 gm/dl). This indicates that the oxygen-carrying capacity of the blood is currently within expected limits."
    },
    {
      "test_name": "ESR (Autoanalyzer Method)",
      "value": 34.00,
      "unit": "mm in 1st hr.",
      "reference_range": "Female: 0 - 20 mm in 1st hr.",
      "status": "High",
      "keyword_explanation": "The Erythrocyte Sedimentation Rate (ESR) measures how quickly red blood cells settle at the bottom of a test tube in one hour. It is a non-specific test used to detect inflammation or infection in the body, relating to the immune system's general inflammatory response. An elevated ESR can be caused by infections, autoimmune diseases (like rheumatoid arthritis or lupus), certain cancers, or kidney disease. A low ESR is less common but can be seen in conditions like polycythemia. Symptoms are usually related to the underlying condition causing inflammation, such as fever, pain, or fatigue.",
      "result_explanation": "The patient's ESR is 34 mm in 1st hr., which is higher than the normal reference range for females (0 - 20 mm in 1st hr.). An elevated ESR can be an indicator of inflammation or infection in the body. It is a non-specific test, meaning it can be high for various reasons and requires further investigation to determine the underlying cause."
    },
    {
      "test_name": "Total Count of WBC",
      "value": 10.00,
      "unit": "x10^9/L",
      "reference_range": "4.0 - 11.0 x10^9/L",
      "status": "Normal",
      "keyword_explanation": "The Total Count of White Blood Cells (WBCs), also known as leukocytes, measures the total number of these immune cells in the blood. WBCs are vital components of the immune system, responsible for fighting infections and responding to inflammation throughout the body. A high count (leukocytosis) often indicates an infection (bacterial, viral, fungal), inflammation, or stress. A low count (leukopenia) can be due to bone marrow problems, autoimmune diseases, or certain medications. Symptoms of abnormal WBC counts are usually related to the underlying cause, such as fever or frequent infections.",
      "result_explanation": "The patient's total white blood cell count is 10.00 x10^9/L, which is within the normal reference range (4.0 - 11.0 x10^9/L). This suggests that the overall number of infection-fighting cells in the blood is currently within expected limits."
    },
    {
      "test_name": "RBC (Blood)",
      "value": 4.60,
      "unit": "x10^12/L",
      "reference_range": "Women: 3.8 - 5.0 x10^12/L",
      "status": "Normal",
      "keyword_explanation": "Red Blood Cells (RBCs), or erythrocytes, are the most abundant cells in the blood and are responsible for transporting oxygen from the lungs to the body's tissues, primarily through their haemoglobin content. This relates to the circulatory system. A high RBC count can be seen in dehydration, certain lung diseases, or polycythemia vera. A low RBC count is a hallmark of anemia, which can be caused by blood loss, nutritional deficiencies, or chronic diseases. Symptoms of low RBCs include fatigue, shortness of breath, and pale skin, while high levels might cause dizziness or headaches.",
      "result_explanation": "The patient's red blood cell count is 4.60 x10^12/L, which falls within the normal reference range for women (3.8 - 5.0 x10^12/L). This indicates that the number of oxygen-carrying cells in the blood is currently within expected limits."
    },
    {
      "test_name": "Platelets",
      "value": 315.00,
      "unit": "x10^9/L",
      "reference_range": "150 - 450 x10^9/L",
      "status": "Normal",
      "keyword_explanation": "Platelets, also known as thrombocytes, are small cell fragments in the blood that play a critical role in blood clotting (hemostasis) and stopping bleeding. They are part of the circulatory system. A high platelet count (thrombocytosis) can be associated with inflammation, infection, iron deficiency, or certain cancers. A low platelet count (thrombocytopenia) can result from bone marrow disorders, autoimmune diseases, or severe infections. Symptoms of low platelets include easy bruising and prolonged bleeding, while very high levels can sometimes increase the risk of blood clots.",
      "result_explanation": "The patient's platelet count is 315.00 x10^9/L, which is within the normal reference range (150 - 450 x10^9/L). This suggests that the number of cells involved in blood clotting is currently within expected limits."
    },
    {
      "test_name": "Neutrophils",
      "value": 57.00,
      "unit": "%",
      "reference_range": "Adult: 40 - 70 %",
      "status": "Normal",
      "keyword_explanation": "Neutrophils are the most common type of white blood cell and are a primary defense against bacterial and fungal infections. They are a key component of the immune system. A high percentage of neutrophils (neutrophilia) often indicates a bacterial infection, inflammation, or stress. A low percentage (neutropenia) can be caused by viral infections, bone marrow suppression, or certain medications. Symptoms of abnormal neutrophil levels are typically related to the underlying cause, such as fever or increased susceptibility to infections.",
      "result_explanation": "The patient's neutrophil percentage is 57%, which falls within the normal reference range for adults (40 - 70%). This indicates that the proportion of these infection-fighting white blood cells is currently within expected limits."
    },
    {
      "test_name": "Lymphocytes",
      "value": 34.00,
      "unit": "%",
      "reference_range": "Adult: 20 - 45 %",
      "status": "Normal",
      "keyword_explanation": "Lymphocytes are a type of white blood cell crucial for the immune system, involved in fighting viral infections and producing antibodies. A high percentage of lymphocytes (lymphocytosis) is often seen in viral infections, chronic infections, or certain cancers like leukemia. A low percentage (lymphopenia) can indicate immunodeficiency, severe stress, or certain autoimmune diseases. Symptoms of abnormal lymphocyte levels are usually related to the underlying condition, such as swollen lymph nodes or frequent infections.",
      "result_explanation": "The patient's lymphocyte percentage is 34%, which falls within the normal reference range for adults (20 - 45%). This indicates that the proportion of these immune cells, important for fighting viral infections, is currently within expected limits."
    },
    {
      "test_name": "Monocytes",
      "value": 5.00,
      "unit": "%",
      "reference_range": "Adult: 2 - 8 %",
      "status": "Normal",
      "keyword_explanation": "Monocytes are a type of white blood cell that play a role in the immune system by engulfing pathogens and cellular debris (phagocytosis) and presenting antigens to other immune cells. A high percentage of monocytes (monocytosis) can be associated with chronic infections (e.g., tuberculosis), inflammation, or certain cancers. A low percentage (monocytopenia) is less common but can be seen with bone marrow suppression. Symptoms are generally non-specific and related to the underlying condition.",
      "result_explanation": "The patient's monocyte percentage is 5%, which falls within the normal reference range for adults (2 - 8%). This indicates that the proportion of these immune cells, involved in clearing debris and fighting chronic infections, is currently within expected limits."
    },
    {
      "test_name": "Eosinophils",
      "value": 4.00,
      "unit": "%",
      "reference_range": "Adult: 1 - 6 %",
      "status": "Normal",
      "keyword_explanation": "Eosinophils are a type of white blood cell involved in allergic reactions, asthma, and fighting parasitic infections. They are part of the immune system. A high percentage of eosinophils (eosinophilia) is commonly seen in allergic conditions (like asthma or hay fever), parasitic infections, or certain skin conditions. A low percentage (eosinopenia) is less common and can be caused by stress or certain medications. Symptoms are typically related to the underlying allergic or parasitic condition, such as itching, rash, or wheezing.",
      "result_explanation": "The patient's eosinophil percentage is 4%, which falls within the normal reference range for adults (1 - 6%). This indicates that the proportion of these immune cells, involved in allergic responses and fighting parasites, is currently within expected limits."
    },
    {
      "test_name": "HCT/PCV",
      "value": 38.40,
      "unit": "%",
      "reference_range": "Female: 37 - 47 %",
      "status": "Normal",
      "keyword_explanation": "Hematocrit (HCT) or Packed Cell Volume (PCV) measures the percentage of red blood cells in a given volume of blood. It reflects the proportion of blood that is made up of red blood cells and is an indicator of the blood's oxygen-carrying capacity, relating to the circulatory system. A high HCT/PCV can indicate dehydration, polycythemia vera, or lung disease. A low HCT/PCV is often associated with anemia, blood loss, or overhydration. Symptoms are similar to those for abnormal red blood cell counts, such as fatigue or dizziness.",
      "result_explanation": "The patient's HCT/PCV is 38.40%, which falls within the normal reference range for females (37 - 47%). This indicates that the proportion of red blood cells in the blood is currently within expected limits."      
    },
    {
      "test_name": "MCV",
      "value": 83.50,
      "unit": "fL",
      "reference_range": "83 - 101 fL",
      "status": "Normal",
      "keyword_explanation": "Mean Corpuscular Volume (MCV) measures the average size of red blood cells. It is an important index for classifying different types of anemia, relating to the circulatory system. A high MCV (macrocytic) can suggest vitamin B12 or folate deficiency, or liver disease. A low MCV (microcytic) is often seen in iron deficiency anemia or thalassemia. Symptoms are generally those of anemia, such as fatigue and weakness.",
      "result_explanation": "The patient's MCV is 83.50 fL, which is within the normal reference range (83 - 101 fL). This indicates that the average size of the red blood cells is currently within expected limits."
    },
    {
      "test_name": "MCH",
      "value": 27.00,
      "unit": "pg/ml",
      "reference_range": "27 - 32 pg/ml",
      "status": "Normal",
      "keyword_explanation": "Mean Corpuscular Hemoglobin (MCH) measures the average amount of hemoglobin in a single red blood cell. This index helps in classifying anemias and relates to the circulatory system. A high MCH can be associated with macrocytic anemias (large red blood cells), such as those caused by vitamin B12 or folate deficiency. A low MCH is typically seen in microcytic anemias (small red blood cells), like iron deficiency anemia or thalassemia. Symptoms are usually related to the underlying anemia.",
      "result_explanation": "The patient's MCH is 27.00 pg/ml, which is within the normal reference range (27 - 32 pg/ml). This indicates that the average amount of hemoglobin in each red blood cell is currently within expected limits."      
    },
    {
      "test_name": "MCHC",
      "value": 32.00,
      "unit": "g/dL",
      "reference_range": "31.5 - 34.5 g/dL",
      "status": "Normal",
      "keyword_explanation": "Mean Corpuscular Hemoglobin Concentration (MCHC) measures the average concentration of hemoglobin within a given volume of red blood cells. It helps in classifying anemias and relates to the circulatory system. A high MCHC is rare but can be seen in conditions like hereditary spherocytosis. A low MCHC is characteristic of hypochromic anemias, such as iron deficiency anemia or thalassemia. Symptoms are generally those of anemia.",
      "result_explanation": "The patient's MCHC is 32.00 g/dL, which is within the normal reference range (31.5 - 34.5 g/dL). This indicates that the average concentration of hemoglobin within the red blood cells is currently within expected limits."
    },
    {
      "test_name": "RDW-SD (fl)",
      "value": 40.60,
      "unit": "%",
      "reference_range": "38.0 - 42.0 %",
      "status": "Normal",
      "keyword_explanation": "Red Cell Distribution Width - Standard Deviation (RDW-SD) measures the variation in the size of red blood cells (anisocytosis). It is a useful index for differentiating between various types of anemia, relating to the circulatory system. A high RDW-SD indicates a wide range of red blood cell sizes and can be seen in iron deficiency anemia, vitamin B12/folate deficiency, or mixed anemias. A low RDW-SD is not typically clinically significant. Symptoms are usually related to the underlying anemia.",
      "result_explanation": "The patient's RDW-SD is 40.60%, which falls within the normal reference range (38.0 - 42.0%). This indicates that the variation in the size of the red blood cells is currently within expected limits."
    },
    {
      "test_name": "RDW-CV (%)",
      "value": 13.60,
      "unit": "%",
      "reference_range": "11.6 - 14.0 %",
      "status": "Normal",
      "keyword_explanation": "Red Cell Distribution Width - Coefficient of Variation (RDW-CV) is another measure of the variation in the size of red blood cells. Similar to RDW-SD, it helps in differentiating between various types of anemia, relating to the circulatory system. A high RDW-CV indicates a wide range of red blood cell sizes and can be seen in iron deficiency anemia, vitamin B12/folate deficiency, or mixed anemias. A low RDW-CV is not typically clinically significant. Symptoms are usually related to the underlying anemia.",
      "result_explanation": "The patient's RDW-CV is 13.60%, which falls within the normal reference range (11.6 - 14.0%). This indicates that the variation in the size of the red blood cells is currently within expected limits."
    },
    {
      "test_name": "IG%",
      "value": 0.00,
      "unit": "%",
      "reference_range": "Unknown",
      "status": "Unknown",
      "keyword_explanation": "Immature Granulocytes (IG%) refers to the percentage of early forms of white blood cells (neutrophils, eosinophils, basophils) that are typically found in the bone marrow and not in significant numbers in the peripheral blood. Their presence in the bloodstream can indicate a strong bone marrow response to infection or inflammation, or certain bone marrow disorders, relating to the immune and hematopoietic systems. A high IG% can be seen in severe infections (sepsis), inflammation, or certain leukemias. A low IG% is generally expected as they are normally absent or very low. Symptoms are usually related to the underlying condition causing their presence.",
      "result_explanation": "The patient's IG% is 0.00%. Without a specific reference range provided in the report, it is difficult to determine the clinical significance of this value. Generally, immature granulocytes are absent or present in very low numbers in healthy individuals."
    },
    {
      "test_name": "NRBC%",
      "value": 0.00,
      "unit": "",
      "reference_range": "Unknown",
      "status": "Unknown",
      "keyword_explanation": "Nucleated Red Blood Cells (NRBC%) are immature red blood cells that still contain a nucleus, which is normally lost before they enter the bloodstream. Their presence in peripheral blood can indicate severe stress on the bone marrow, severe anemia, or certain bone marrow disorders, relating to the circulatory and hematopoietic systems. A high NRBC% can be seen in severe anemia, bone marrow stress (e.g., severe hypoxia), myelofibrosis, or certain leukemias. A low NRBC% is generally expected as they are normally absent in healthy adults. Symptoms are usually related to the underlying condition causing their presence.",
      "result_explanation": "The patient's NRBC% is 0.00. Without a specific unit or reference range provided in the report, it is difficult to determine the clinical significance of this value. Generally, nucleated red blood cells are absent in the peripheral blood of healthy adults."
    },
    {
      "test_name": "MPV",
      "value": 10.50,
      "unit": "fL",
      "reference_range": "7.40 - 10.40 fL",
      "status": "High",
      "keyword_explanation": "Mean Platelet Volume (MPV) measures the average size of platelets. It can provide clues about platelet production and destruction, relating to the circulatory system and hemostasis. A high MPV can indicate that the bone marrow is producing larger, younger platelets, possibly in response to increased platelet destruction or turnover. It can also be associated with myeloproliferative disorders or an increased risk of cardiovascular disease. A low MPV can be seen in bone marrow failure or aplastic anemia. Symptoms are often non-specific and related to underlying conditions affecting platelet function.",
      "result_explanation": "The patient's MPV is 10.50 fL, which is slightly higher than the normal reference range (7.40 - 10.40 fL). A slightly elevated MPV can sometimes indicate that the bone marrow is producing larger, younger platelets, possibly in response to a need for more platelets or increased platelet turnover. This finding should be considered in the context of other platelet parameters and the patient's overall clinical picture."
    },
    {
      "test_name": "PCT",
      "value": 0.33,
      "unit": "%",
      "reference_range": "0.13 - 0.50 %",
      "status": "Normal",
      "keyword_explanation": "Plateletcrit (PCT) measures the percentage of blood volume occupied by platelets, similar to how hematocrit measures red blood cell volume. It provides an overall assessment of platelet mass, reflecting both platelet count and size, relating to the circulatory system and hemostasis. A high PCT can indicate thrombocytosis (high platelet count) or larger platelets. A low PCT can indicate thrombocytopenia (low platelet count) or smaller platelets. Symptoms are often non-specific and related to underlying conditions affecting platelet function.",
      "result_explanation": "The patient's PCT is 0.33%, which falls within the normal reference range (0.13 - 0.50%). This indicates that the total volume occupied by platelets in the blood is currently within expected limits."
    },
    {
      "test_name": "PDW",
      "value": 11.70,
      "unit": "%",
      "reference_range": "10 - 18 %",
      "status": "Normal",
      "keyword_explanation": "Platelet Distribution Width (PDW) measures the variation in the size of platelets. It can help differentiate between various causes of platelet disorders, relating to the circulatory system and hemostasis. A high PDW indicates a wide range of platelet sizes, often seen in conditions with increased platelet destruction or production. A low PDW is not typically clinically significant or may indicate a uniform population of platelets. Symptoms are often non-specific and related to underlying conditions affecting platelet function.",
      "result_explanation": "The patient's PDW is 11.70%, which falls within the normal reference range (10 - 18%). This indicates that the variation in the size of the platelets is currently within expected limits."
    }
  ],
  "risk_level": "Medium",
  "advice": "It is important to consult with a healthcare professional, such as the referring physician (Prof. Dr. N K Datta, Hand & Micro Surgeon), to discuss these results in the context of your medical history and any symptoms you may be experiencing. The elevated ESR and slightly high MPV should be further evaluated to understand their cause. The X-ray findings, particularly the degenerative changes in the lumbar spine (osteophytes, sacralization of L5, forward slip of L4 over L5) and bilateral sacroiliitis, are significant and will likely require further clinical assessment and potentially a management plan. Do not self-diagnose or attempt to treat any conditions based solely on this report. A doctor can provide a comprehensive interpretation and recommend appropriate next steps."
};

/**
 * Validate AI JSON safely
 */

function safeParseJSON(str) {
   if (!str) return null; 
    try {
        return JSON.parse(str);
    } catch (err) {
        // Attempt to extract JSON-looking content with regex
        const match = str.match(/\{[\s\S]*\}/); // everything between first { and last }
        if (match) {
            try {
                return JSON.parse(match[0]);
            } catch (_) {
                return null;
            }
        }
        return null;
    }
}

  function extractJson(text) {
    const match = text.match(/\{[\s\S]*\}/);
    if (!match) throw new Error("No JSON found");
    return JSON.parse(match[0]);
  }

  function ocrQualityScore(text) {
    const totalChars = text.length;
    const unreadable = (text.match(/[^\x00-\x7F]/g) || []).length;

    if (totalChars < 50) return "LOW";
    if ((unreadable / totalChars) > 0.05) return "LOW";
    return "HIGH";
  }

  function getFinalOcrQuality(confidence, text) {
    const heuristic = ocrQualityScore(text);
    if (confidence < 60 || heuristic === "LOW") return "LOW";
    if (confidence < 85) return "MEDIUM";
    return "HIGH";
  }

  // Remove unwanted characters and normalize spaces
  function cleanReport(report) {
    if (!report) return "";

    // Remove only weird symbols
    //report = report.replace(/[~*|`^]/g, "");

    // Normalize multiple spaces but keep newlines
    report = report.replace(/[ ]{2,}/g, " ");

    //report = report.replace(/[^\x00-\x7F]/g, "");

    return report.trim();
}
/**
 * Main Medical Explanation Function
 */
  async function explainMedicalReport(reportText) {
      const prompt = `
        You are a cautious and educational medical explanation AI.

        TASK:
        Analyze the medical report and return structured JSON.
        For EACH medical test found, create a JSON object with the following fields:

        1) "test_name": Name of the test.
        2) "value": The measured value (as a number if possible).
        3) "unit": The unit of measurement, if provided.
        4) "reference_range": The normal reference range, if provided.
        5) "status": "Normal", "High", "Low", or "Unknown" if unclear.
        6) "keyword_explanation": Explain the medical keyword in detail:
          - What the test measures
          - Why it is important
          - What body system it relates to
          - Common reasons it may go high or low
          - Possible symptoms (general, not diagnosing)
          - explain shortly in few lines
        7) "result_explanation": Explain the patient's specific result in simple language.

        IMPORTANT INSTRUCTIONS:
        - If multiple tests are present, analyze each separately in its own JSON object.
        - Do NOT merge explanations between different tests.
        - Keep explanations factual, neutral, and educational.
        - Maintain a calm and professional tone.
        - Always include all JSON keys, even if the value is unknown (use "Unknown" or empty string).

        STRICT RULES:
        - Do NOT diagnose diseases.
        - Do NOT prescribe medication.
        - Do NOT suggest specific treatments.
        - If unsure, say "Consult a doctor".
        - Do NOT invent missing values.
        - Only analyze what is explicitly present in the report.
        - Return VALID JSON only.
        - Do NOT include markdown or text outside JSON.

        JSON FORMAT EXAMPLE:
        {
          "summary": "Overall simplified explanation of the report in plain language",
          "tests_analysis": [
            {
              "test_name": "Hemoglobin",
              "value": 10.2,
              "unit": "g/dL",
              "reference_range": "13.0-17.0",
              "status": "Unknown",
              "keyword_explanation": "...",
              "result_explanation": "..."
            }
          ],
          "risk_level": "Low | Medium | High",
          "advice": "General safety advice only. If abnormalities exist, recommend consulting a doctor."
        }

        Medical Report:
        ${reportText}
      `;

      try {
          // const cleanedPrompt = cleanReport(prompt);

          // console.log("clean promt:", cleanedPrompt);
          // const result = await model.generateContent(prompt);
          // // Check both possible properties
  
          // //const responseText = result?.candidates?.[0]?.content || result?.output_text;
          // const responseText = result.response.text();

          // if (!responseText) {
          //     return { error: "Gemini returned empty response" };
          // }
          // const parsedOutput = safeParseJSON(responseText);

          // if (!parsedOutput) {
          //     console.error("Failed to parse JSON:", responseText);
          //     return { error: "Gemini returned invalid JSON", raw: responseText };
          // }

          return testResult;

      } catch (error) {
          console.error("Gemini API Error:", error.response?.data || error.message);
          return { error: "Failed to process report" };
      }
  }
module.exports = { explainMedicalReport };