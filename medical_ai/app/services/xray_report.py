"""
X-Ray Analyzer Service
Pre-trained model: TorchXRayVision (DenseNet121)

SETUP:
  pip install torchxrayvision torch torchvision pillow numpy
"""

import io
import logging

import numpy as np
import torch
import torchxrayvision as xrv
from PIL import Image

logger = logging.getLogger(__name__)


class XRayService:

    def __init__(self):
        self.model  = None
        self.labels = []
        self._load_model()

    # ── Load model ────────────────────────────────────────────────────────────
    def _load_model(self):
        try:
            logger.info("⏳ Loading DenseNet121 (TorchXRayVision)...")
            self.model  = xrv.models.DenseNet(weights="densenet121-res224-all")
            self.model.eval()
            self.labels = self.model.pathologies
            logger.info("✅ X-ray model loaded")
        except Exception as e:
            logger.error(f"❌ Failed to load X-ray model: {e}")

    # ── Preprocess ────────────────────────────────────────────────────────────
    def _preprocess(self, image_bytes: bytes) -> torch.Tensor:
        """Convert raw image bytes → model-ready tensor [1, 1, 224, 224]."""
        img       = Image.open(io.BytesIO(image_bytes)).convert("L")
        img_array = np.array(img.resize((224, 224))).astype(np.float32)
        img_array = (img_array / 255.0) * 2048 - 1024          # scale to [-1024, 1024]
        return torch.from_numpy(img_array).unsqueeze(0).unsqueeze(0)

    # ── Public method ─────────────────────────────────────────────────────────
    def analyze(self, image_bytes: bytes) -> dict:
        """
        Run pathology detection on raw image bytes.

        Returns:
            {
                "success":      bool,
                "findings":     [ { "condition": str, "probability": float } ],
                "top_findings": [ ... ],   # only findings > 10%
                "model":        str,
                "disclaimer":   str
            }
        """
        if self.model is None:
            raise RuntimeError("X-ray model is not loaded. Check torchxrayvision installation.")

        tensor = self._preprocess(image_bytes)

        with torch.no_grad():
            outputs = self.model(tensor).squeeze().numpy()

        findings = [
            {"condition": label, "probability": round(float(np.clip(score, 0, 1)) * 100, 1)}
            for label, score in zip(self.labels, outputs)
            if label
        ]

        findings.sort(key=lambda x: x["probability"], reverse=True)

        return {
            "success":      True,
            "findings":     findings,
            "top_findings": [f for f in findings if f["probability"] > 10],
            "model":        "DenseNet121 — densenet121-res224-all",
            "disclaimer":   "AI-assisted only. Not a medical diagnosis. Consult a doctor.",
        }