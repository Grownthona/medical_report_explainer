const express = require("express");
const multer = require("multer");
const sharp = require("sharp");
const pdfParse = require("pdf-parse");
const Tesseract = require("tesseract.js");
//const tesseract = require("node-tesseract-ocr");
//const fileUpload = require('express-fileupload');
const router = express.Router();
const path = require("path");
const fs = require("fs");
const uploadDir = "uploads";
const axios = require("axios");
const FormData = require("form-data");


const { explainMedicalReport } = require('../services/geminiService');
const { json } = require("body-parser");

if (!fs.existsSync(uploadDir)) fs.mkdirSync(uploadDir);

const storage = multer.diskStorage({
  destination: (req, file, cb) => cb(null, "uploads/"),
  filename: (req, file, cb) =>
    cb(null, Date.now() + "-" + file.originalname)
});

const upload = multer({
  storage,
  limits: { fileSize: 10 * 1024 * 1024 }, // 10MB per file
  fileFilter: (req, file, cb) => {
    const allowedTypes = ["application/pdf", "image/jpeg", "image/png"];
    if (allowedTypes.includes(file.mimetype)) cb(null, true);
    else cb(new Error("Invalid file type"));
  }
});

function analyzeTextQuality(text) {
  if (!text) return { valid: false, reason: "Empty text" };

  const length = text.length;

  // Count readable words
  const words = text.split(/\s+/).filter(w => w.length > 2);
  const wordCount = words.length;

  // Count numbers (medical reports contain numbers)
  const numbers = text.match(/\d+/g) || [];
  const numberCount = numbers.length;

  // Detect excessive garbage characters
  const garbageMatches = text.match(/[^a-zA-Z0-9\s.,:%()/\-]/g) || [];
  const garbageRatio = garbageMatches.length / length;

  // Detect repeated broken OCR patterns
  const repeatedPattern = /(.)\1{4,}/g.test(text);

  // Basic heuristics
  if (length < 100) {
    return { valid: false, reason: "Text too short" };
  }

  if (wordCount < 20) {
    return { valid: false, reason: "Not enough readable words" };
  }

  if (numberCount < 5) {
    return { valid: false, reason: "Not enough numeric medical values" };
  }

  if (garbageRatio > 0.1) {
    return { valid: false, reason: "Too many unreadable characters" };
  }

  if (repeatedPattern) {
    return { valid: false, reason: "Corrupted OCR pattern detected" };
  }

  return { valid: true };
}

async function preprocessImage(inputPath) {

  const outputPath = path.join("uploads", "processed-" + Date.now() + ".png");

  await sharp(inputPath)
    .grayscale()          // remove colors (better OCR)
    .normalize()          // improve contrast
    .sharpen()            // make text clearer
    //.resize({ width: 2000 }) // upscale small images
    .png()
    .toFile(outputPath);
   
    // const { data } = await Tesseract.recognize(outputPath, {
    //   preserve_interword_spaces: 1,
    //   tessedit_pageseg_mode: 6
    // });

    const { data: { text } } = await Tesseract.recognize(
      outputPath,
      "eng", // language
      {
        logger: m => console.log(m.status) // optional
      }
    );

    // const averageConfidence = text.reduce((sum, w) => sum + w.confidence, 0) / text.length;
    // console.log(averageConfidence);
    console.log(text);

  return outputPath;
}

async function extractPDFText(filePath) {
  const dataBuffer = fs.readFileSync(filePath);
  const data = await pdfParse(dataBuffer);
  return data.text;
}

// Image OCR
async function extractTextFromImage(filePath) {
  // const processedPath = await preprocessImage(imagePath);
  // const { data: { text } } = await Tesseract.recognize(processedPath, "eng");

  const form = new FormData();
  form.append("file", fs.createReadStream(filePath));

  try {
    const response = await axios.post("http://127.0.0.1:8000/extract/text/", form, {
      headers: form.getHeaders(),
    });
    return response.data.result;
  } catch (error) {
    console.error("Error calling FastAPI:", error.message);
    throw error;
  }
}

// POST /multiple
router.post("/multiple", upload.array("medicalFiles", 5), async (req, res) => {
  try {
    if (!req.files || req.files.length === 0) {
      return res.status(400).json({ error: "No files uploaded" });
    }

    const results = [];

    for (const file of req.files) {
      try {
        let reportText = "";

        // Extract text based on file type
        if (file.mimetype === "application/pdf") {
          reportText = await extractPDFText(file.path);
        } else {
          reportText = await extractTextFromImage(file.path);
        }

        // Analyze medical report
        //const analysis = await explainMedicalReport(reportText);

        // Push structured result
        results.push({
          filename: file.originalname,
          success: true,
          extractedTextPreview: reportText.substring(0, 1000),
          summary: analysis.summary,
          advice: analysis.advice,
          risk_level: analysis.risk_level,
          tests_analysis: analysis.tests_analysis
        });

      } catch (fileError) {
        console.error("Error processing:", file.originalname, fileError);

        results.push({
          filename: file.originalname,
          success: false,
          error: fileError.message
        });
      }
    }

    console.log(JSON.stringify(results));
    // Send response AFTER all files processed
    return res.json({
      success: true,
      totalFiles: req.files.length,
      processed: results
    });

  } catch (err) {
    console.error("Server error:", err);
    return res.status(500).json({ error: "Internal Server Error" });
  }
});

module.exports = router;
