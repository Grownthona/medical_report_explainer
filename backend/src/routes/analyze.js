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


const { explainMedicalReport } = require('../services/geminiService');

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
async function extractTextFromImage(imagePath) {
  const processedPath = await preprocessImage(imagePath);
  const { data: { text } } = await Tesseract.recognize(processedPath, "eng");
  
  const cleanedReport = text
  // .replace(/[^\x00-\x7F]/g, "")  // remove weird unicode
  .replace(/\s+/g, " ")          // normalize spaces
  //.replace(/[_=]{2,}/g, "")      // remove OCR lines
  .trim();
  return cleanedReport;
}

router.post("/multiple", (req, res) => {
  upload.array("medicalFiles", 5)(req, res, async (err) => {
    if (err) {
      console.error("Upload error:", err);
      return res.status(400).json({ error: err.message });
    }
    const uploadedFiles = req.files.map(f => ({
      originalName: f.originalname,
      savedAs: f.filename,
      path: f.path
    }));
    const results = [];
    for (const file of req.files) {
      let reportText = "";
      try {
        if (file.mimetype === "application/pdf") {
          reportText =  await extractPDFText(file.path);
        } else {
          reportText =  await extractTextFromImage(file.path);
        }
        const analysis = await explainMedicalReport(reportText);
        //console.log("analysis:",analysis);
      
        return res.json({
            success: true,
            extractedText: reportText.substring(0, 2000), // Return first 2000 chars for display
            summary: analysis.summary,
            advice: analysis.advice,
            risk_level: analysis.risk_level,
            tests_analysis: analysis.tests_analysis
        });

        
      } catch (error) {
        console.error("Error processing file", file.originalname, error);
        results.push({
          error: error.message
        });
      }
    }

    res.json({ message: "Files processed successfully", files: results });
  });
});

module.exports = router;
