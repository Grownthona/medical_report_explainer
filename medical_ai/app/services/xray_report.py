import gc
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
        logger.info("XRayService created (model loads on first use)")

    def _load_model(self):
        if self.model is not None:
            return
        try:
            logger.info("Loading DenseNet121 in half precision...")
            self.model = xrv.models.DenseNet(weights="densenet121-res224-rsna")
            self.model.eval()
            self.model = self.model.half()  # ~400MB instead of ~800MB
            self.labels = self.model.pathologies
            logger.info("X-ray model loaded")
        except Exception as e:
            logger.error("Failed to load X-ray model: %s", e)

    def unload(self):
        """Free RAM by unloading the model."""
        if self.model is not None:
            logger.info("Unloading XRay model to free RAM...")
            del self.model
            self.model  = None
            self.labels = []
            gc.collect()
            torch.cuda.empty_cache()

    def _preprocess(self, image_bytes: bytes) -> torch.Tensor:
        img       = Image.open(io.BytesIO(image_bytes)).convert("L")
        img_array = np.array(img.resize((224, 224))).astype(np.float32)
        img_array = (img_array / 255.0) * 2048 - 1024
        return torch.from_numpy(img_array).unsqueeze(0).unsqueeze(0).half()

    def analyze(self, image_bytes: bytes) -> dict:
        self._load_model()

        if self.model is None:
            raise RuntimeError("X-ray model failed to load.")

        tensor = self._preprocess(image_bytes)

        with torch.no_grad():
            outputs = self.model(tensor).squeeze().float().numpy()

        # Unload immediately after inference to free RAM
        self.unload()

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
            "model":        "DenseNet121 — densenet121-res224-rsna (half precision)",
            "disclaimer":   "AI-assisted only. Not a medical diagnosis. Consult a doctor.",
        }