"""
Cross-camera person matching logic.
"""

import numpy as np
from typing import List, Tuple, Dict, Optional

class CrossCameraMatcher:
    """
    Handles cross-camera matching by comparing ReID embeddings.
    Workflow: Person exits Camera 1 -> Person enters Camera 2 -> Compare embeddings -> Determine identity
    """
    
    def __init__(self, distance_threshold: float = 0.4):
        """
        Initialize the matcher.
        
        Args:
            distance_threshold: Maximum cosine distance (1 - cosine_similarity)
                                to consider two embeddings a match.
        """
        self.distance_threshold = distance_threshold

    def compute_cosine_similarity(self, emb1: np.ndarray, emb2: np.ndarray) -> float:
        """
        Compute cosine similarity between two embeddings.
        Supports unnormalized embeddings as it computes the norm.
        """
        e1 = np.asarray(emb1).flatten()
        e2 = np.asarray(emb2).flatten()
        
        norm1 = np.linalg.norm(e1)
        norm2 = np.linalg.norm(e2)
        
        if norm1 == 0 or norm2 == 0:
            return 0.0
            
        return float(np.dot(e1, e2) / (norm1 * norm2))

    def rank_candidates(self, query_emb: np.ndarray, gallery: Dict[str, np.ndarray]) -> List[Tuple[str, float, float]]:
        """
        Rank all candidates in the gallery against a query embedding.
        
        Args:
            query_emb: Embedding of the person to match (e.g., from Camera 2).
            gallery: Dict of candidate_id -> embedding (e.g., exits from Camera 1).
            
        Returns:
            List of (candidate_id, similarity, distance) sorted by highest similarity (lowest distance).
        """
        results = []
        for cand_id, cand_emb in gallery.items():
            sim = self.compute_cosine_similarity(query_emb, cand_emb)
            dist = 1.0 - sim
            results.append((cand_id, sim, dist))
            
        # Rank by highest similarity
        results.sort(key=lambda x: x[1], reverse=True)
        return results

    def get_top_k(self, query_emb: np.ndarray, gallery: Dict[str, np.ndarray], k: int = 1) -> List[Tuple[str, float]]:
        """
        Retrieve the top-k matches that fall within the distance threshold.
        
        Args:
            query_emb: The query embedding.
            gallery: Dict of candidate_id -> embedding.
            k: Number of top matches to retrieve.
            
        Returns:
            List of (candidate_id, distance) for the top-k matches within threshold.
        """
        ranked = self.rank_candidates(query_emb, gallery)
        
        # Filter by threshold
        valid_matches = [(cand_id, dist) for cand_id, sim, dist in ranked if dist <= self.distance_threshold]
        
        return valid_matches[:k]

    def determine_identity(self, query_emb: np.ndarray, gallery: Dict[str, np.ndarray]) -> Optional[str]:
        """
        Determine the identity of a person entering a camera by matching against a gallery of previous exits.
        
        Args:
            query_emb: The embedding of the person currently entering.
            gallery: Dict of candidate_id -> embedding from other cameras.
            
        Returns:
            The ID of the best match, or None if no match meets the threshold.
        """
        top_matches = self.get_top_k(query_emb, gallery, k=1)
        if top_matches:
            return top_matches[0][0]
        return None
