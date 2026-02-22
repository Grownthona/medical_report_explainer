exports.analyzeReport = async (req, res) => {
  try {
    const { text } = req.body;

    // Later we connect Gemini here
    res.json({
      success: true,
      message: "Report received",
      originalText: text
    });

  } catch (error) {
    res.status(500).json({ error: error.message });
  }
};
