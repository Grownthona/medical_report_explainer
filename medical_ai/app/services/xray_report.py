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
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        # FP16 is only safe on CUDA — avg_pool2d and several other ops used by
        # DenseNet121 raise "not implemented for 'Half'" when run on CPU.
        self.dtype  = torch.float16 if self.device.type == "cuda" else torch.float32
        self.model  = None
        self.labels = []
        logger.info(
            "XRayService created — device=%s dtype=%s (model loads on first use)",
            self.device, self.dtype,
        )

    def _load_model(self):
        if self.model is not None:
            return
        try:
            logger.info("Loading DenseNet121 (device=%s, dtype=%s)...", self.device, self.dtype)
            model = xrv.models.DenseNet(weights="densenet121-res224-rsna")
            model.eval()
            model = model.to(device=self.device, dtype=self.dtype)
            self.model  = model
            # Capture labels NOW, before any possible unload()
            self.labels = list(model.pathologies)
            logger.info("X-ray model loaded — %d pathology labels", len(self.labels))
        except Exception as e:
            logger.error("Failed to load X-ray model: %s", e)
            self.model = None

    def unload(self):
        """Free RAM/VRAM by unloading the model after inference.
        Labels are intentionally kept so the next analyze() call can
        still reference them if needed before _load_model() runs again.
        """
        if self.model is not None:
            logger.info("Unloading XRayService model to free memory...")
            del self.model
            self.model = None
            # Do NOT clear self.labels here — they are needed in analyze()
            # after unload() is called.
            gc.collect()
            if self.device.type == "cuda":
                torch.cuda.empty_cache()

    @staticmethod
    def _pil_to_xrv_array(img: Image.Image) -> np.ndarray:
        """
        Convert a PIL image to the float32 array format torchxrayvision expects.

        torchxrayvision's xrv.utils.normalize() maps pixel values to [-1024, 1024].
        It expects a float32 array whose range matches the bit depth of the image:
          - 8-bit  images (PNG/JPEG): maxval=255
          - 16-bit images (DICOM/16-bit PNG): maxval=65535

        Feeding raw uint8 values to np.clip(score, 0, 1) later is WRONG because
        the model never saw properly normalised inputs.
        """
        img = img.convert("L")           # ensure single-channel grayscale

        # Detect bit depth
        mode_maxval = {"L": 255, "I;16": 65535, "I": 65535}
        maxval = mode_maxval.get(img.mode, 255)

        arr = np.array(img).astype(np.float32)

        # xrv.utils.normalize maps [0, maxval] → [-1024, 1024]
        arr = xrv.utils.normalize(arr, maxval)      # shape: (H, W)
        return arr

    @staticmethod
    def _resize_with_padding(arr: np.ndarray, target: int = 224) -> np.ndarray:
        """
        Resize a (H, W) float32 array to (target, target) while preserving
        aspect ratio by padding with the minimum pixel value (black border).

        Plain img.resize((224,224)) squashes non-square X-rays, distorting
        cardiac silhouette width — a major cause of cardiomegaly false positives.
        """
        h, w = arr.shape
        scale = target / max(h, w)
        new_h, new_w = int(round(h * scale)), int(round(w * scale))

        # Resize using PIL for clean bilinear interpolation
        pil_resized = Image.fromarray(arr).resize(
            (new_w, new_h), resample=Image.BILINEAR
        )
        resized = np.array(pil_resized)

        # Pad to square with the minimum value (background)
        pad_val = float(arr.min())
        canvas  = np.full((target, target), pad_val, dtype=np.float32)
        y_off   = (target - new_h) // 2
        x_off   = (target - new_w) // 2
        canvas[y_off:y_off + new_h, x_off:x_off + new_w] = resized
        return canvas

    def _preprocess(self, image_bytes: bytes) -> torch.Tensor:
        """
        Decode image bytes → normalised [1, 1, 224, 224] tensor.

        Pipeline:
          1. Open with PIL (handles PNG, JPEG, BMP, 16-bit PNG)
          2. Convert to float32 with proper bit-depth-aware normalisation
          3. Aspect-ratio-preserving resize + pad to 224×224
          4. Add batch + channel dims, move to device/dtype
        """
        img    = Image.open(io.BytesIO(image_bytes))
        arr    = self._pil_to_xrv_array(img)           # (H, W) float32 [-1024,1024]
        arr    = self._resize_with_padding(arr, 224)    # (224, 224) float32
        tensor = torch.from_numpy(arr).unsqueeze(0).unsqueeze(0)  # [1,1,224,224]
        return tensor.to(device=self.device, dtype=self.dtype)

    def analyze(self, image_bytes: bytes) -> dict:
        self._load_model()

        if self.model is None:
            raise RuntimeError("X-ray model failed to load.")

        # Snapshot labels BEFORE unload() wipes the model reference.
        # (unload() no longer clears labels, but snapshot here is belt-and-suspenders)
        labels = list(self.labels)

        tensor = self._preprocess(image_bytes)

        with torch.inference_mode():
            raw_output = self.model(tensor)             # [1, num_classes] — raw logits

        # Apply sigmoid: logits → probabilities in [0, 1]
        # np.clip(score, 0, 1) on raw logits is WRONG — logits can be negative
        # (meaning low probability) but clip treats negatives as 0%, masking findings.
        probs = torch.sigmoid(raw_output).squeeze().float().cpu().numpy()

        # Release model immediately to reclaim memory
        self.unload()

        findings = [
            {
                "condition":   label,
                "probability": round(float(probs[i]) * 100, 1),
            }
            for i, label in enumerate(labels)
            if label                                    # skip empty/None label slots
        ]
        findings.sort(key=lambda x: x["probability"], reverse=True)

        return {
            "success":      True,
            "findings":     findings,
            "top_findings": [f for f in findings if f["probability"] > 10],
            "model":        (
                f"DenseNet121 — densenet121-res224-rsna "
                f"({'half precision' if self.dtype == torch.float16 else 'full precision'})"
            ),
            "disclaimer": "AI-assisted only. Not a medical diagnosis. Consult a doctor.",
        }