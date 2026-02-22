const express = require("express");
const router = express.Router();

const { analyzeReport } = require("../controllers/report");

router.post("/analyze", analyzeReport);

router.get('/', (req, res) => {
    res.json({
        status: 'ok',
        service: 'Medical Report AI Backend',
        timestamp: new Date().toISOString(),
    });
});

module.exports = router;
