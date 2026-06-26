import numpy as np
import cv2
import base64
from typing import Optional, List, Tuple

# Graceful import check for InsightFace
try:
    from insightface.app import FaceAnalysis
    INSIGHTFACE_AVAILABLE = True
except ImportError:
    INSIGHTFACE_AVAILABLE = False

class FaceVerifierService:
    def __init__(self):
        self.app = None
        if INSIGHTFACE_AVAILABLE:
            try:
                # Initialize face analysis model (uses detection and recognition models)
                # It automatically downloads models to ~/.insightface/models/ on first run
                self.app = FaceAnalysis(name='buffalo_l')
                self.app.prepare(ctx_id=-1, det_size=(640, 640)) # ctx_id=-1 uses CPU; change to 0 for GPU
            except Exception as e:
                print(f"Failed to initialize InsightFace models: {str(e)}")
                self.app = None

    def _decode_image(self, base64_image: str) -> Optional[np.ndarray]:
        """
        Decodes a base64 image string into an OpenCV image (numpy array).
        """
        try:
            if "," in base64_image:
                base64_image = base64_image.split(",")[1]
            img_data = base64.b64decode(base64_image)
            nparr = np.frombuffer(img_data, np.uint8)
            img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            return img
        except Exception as e:
            print(f"Image decoding failed: {str(e)}")
            return None

    def extract_embedding(self, base64_image: str) -> Tuple[Optional[List[float]], Optional[str]]:
        """
        Extracts a 512-D face embedding vector from the base64 image.
        Returns (embedding_list, error_message).
        """
        img = self._decode_image(base64_image)
        if img is None:
            return None, "Invalid image formatting or failed decode."

        if not INSIGHTFACE_AVAILABLE or self.app is None:
            # Fallback mock embedding for development environments
            mock_emb = np.random.uniform(-0.1, 0.1, 512).tolist()
            return mock_emb, "InsightFace not available. Returned mock embedding."

        try:
            faces = self.app.get(img)
            if not faces:
                return None, "No face detected in the image."
            if len(faces) > 1:
                return None, "Multiple faces detected. Please ensure only one person is in the frame."

            # Get the embedding vector (numpy array) and cast to standard python float list
            embedding = faces[0].normed_embedding.tolist()
            return embedding, None
        except Exception as e:
            return None, f"Embedding extraction failed: {str(e)}"

    def verify_similarity(self, embedding_a: List[float], embedding_b: List[float]) -> float:
        """
        Calculates the Cosine Similarity score between two 512-D embedding vectors.
        Value ranges from -1.0 to 1.0 (higher is more similar).
        """
        vec_a = np.array(embedding_a, dtype=np.float32)
        vec_b = np.array(embedding_b, dtype=np.float32)
        
        # Cosine Similarity formula: dot(A, B) / (norm(A) * norm(B))
        dot_product = np.dot(vec_a, vec_b)
        norm_a = np.linalg.norm(vec_a)
        norm_b = np.linalg.norm(vec_b)
        
        if norm_a == 0 or norm_b == 0:
            return 0.0
            
        similarity = dot_product / (norm_a * norm_b)
        return float(similarity)

    def detect_spoofing(self, base64_image: str) -> Tuple[bool, float]:
        """
        Runs texture-based analysis using OpenCV to check for digital/print spoofs.
        Returns (is_spoof, spoof_score).
        """
        img = self._decode_image(base64_image)
        if img is None:
            return True, 1.0

        try:
            # Simple passive liveness analysis:
            # We convert the face region to Grayscale and analyze the Laplacian variance.
            # Photos of photos (spoofs) typically have lower variance (more blur, less high-frequency details)
            # than real live cameras.
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            laplacian_var = cv2.Laplacian(gray, cv2.CV_64F).var()
            
            # Laplacian threshold: values below ~100 are typically classified as blurry or re-photographed printouts
            is_spoof = laplacian_var < 80.0
            # Normalize confidence score: lower variance maps to higher spoof probability
            spoof_score = max(0.0, min(1.0, (150.0 - laplacian_var) / 150.0))
            
            return is_spoof, spoof_score
        except Exception as e:
            print(f"Liveness check exception: {str(e)}")
            return True, 0.9 # Flag as spoof if calculation fails to be safe
