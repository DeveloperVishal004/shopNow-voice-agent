import os
os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"  # must be first line before torch
import torch
import torchaudio
import tempfile
import os
import numpy as np
from loguru import logger

classifier = None

def load_voice_sentiment_model():
    global classifier
    try:
        # fix OpenMP conflict on macOS
        os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"

        from speechbrain.inference.interfaces import foreign_class

        logger.info("Loading voice sentiment model — first run downloads ~100MB...")

        os.makedirs("./models/speechbrain_emotion", exist_ok=True)

        classifier = foreign_class(
            source        = "speechbrain/emotion-recognition-wav2vec2-IEMOCAP",
            pymodule_file = "custom_interface.py",
            classname     = "CustomEncoderWav2vec2Classifier",
            savedir       = "./models/speechbrain_emotion"
        )
        logger.info("Voice sentiment model loaded successfully")

    except ImportError:
        logger.error("SpeechBrain not installed — run: pip install speechbrain==1.0.0")
        classifier = None

    except Exception as e:
        logger.error(f"Voice sentiment model failed to load: {e}")
        import traceback
        traceback.print_exc()
        classifier = None

EMOTION_TO_SENTIMENT = {
    "ang": "angry",
    "hap": "positive",
    "neu": "neutral",
    "sad": "negative",
    "fru": "negative",
    "exc": "positive",
    "fea": "negative",
    "dis": "negative",
}

SENTIMENT_SCORE = {
    "angry":    -1.0,
    "negative": -0.5,
    "neutral":   0.0,
    "positive":  1.0,
}

def score_voice_sentiment(audio_bytes: bytes, sample_rate: int = 24000) -> dict:
    if not classifier:
        logger.warning("Voice sentiment model not loaded — returning neutral")
        return {
            "label":   "neutral",
            "score":   0.0,
            "source":  "voice",
            "success": False
        }

    try:
        audio_np     = np.frombuffer(audio_bytes, dtype=np.int16)
        audio_f32    = audio_np.astype(np.float32) / 32768.0
        audio_tensor = torch.tensor(audio_f32).unsqueeze(0)

        if sample_rate != 16000:
            resampler    = torchaudio.transforms.Resample(
                orig_freq = sample_rate,
                new_freq  = 16000
            )
            audio_tensor = resampler(audio_tensor)

        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
            tmp_path = tmp.name
            torchaudio.save(tmp_path, audio_tensor, 16000)

        out_prob, score, index, label = classifier.classify_file(tmp_path)
        os.remove(tmp_path)

        raw_label  = label[0].lower()
        sentiment  = EMOTION_TO_SENTIMENT.get(raw_label, "neutral")
        confidence = float(score[0])

        logger.info(
            f"Voice sentiment | emotion: {raw_label} | "
            f"sentiment: {sentiment} | confidence: {confidence:.2f}"
        )

        return {
            "label":      sentiment,
            "score":      SENTIMENT_SCORE[sentiment],
            "emotion":    raw_label,
            "confidence": confidence,
            "source":     "voice",
            "success":    True
        }

    except Exception as e:
        logger.error(f"Voice sentiment failed: {e}")
        return {
            "label":   "neutral",
            "score":   0.0,
            "source":  "voice",
            "success": False,
            "error":   str(e)
        }