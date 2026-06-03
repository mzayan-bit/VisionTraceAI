import numpy as np
import pytest
from backend.reid.matcher import CrossCameraMatcher

def test_cosine_similarity():
    matcher = CrossCameraMatcher()
    emb1 = np.array([1.0, 0.0, 0.0])
    emb2 = np.array([1.0, 0.0, 0.0])
    emb3 = np.array([0.0, 1.0, 0.0])
    
    # Same vector -> similarity 1.0
    assert np.isclose(matcher.compute_cosine_similarity(emb1, emb2), 1.0)
    # Orthogonal vectors -> similarity 0.0
    assert np.isclose(matcher.compute_cosine_similarity(emb1, emb3), 0.0)

def test_candidate_ranking():
    matcher = CrossCameraMatcher()
    query = np.array([1.0, 0.0])
    
    gallery = {
        "person_A": np.array([0.0, 1.0]),  # Orthogonal, sim = 0.0, dist = 1.0
        "person_B": np.array([1.0, 0.1]),  # Very close, high sim
        "person_C": np.array([0.7, 0.7])   # Medium sim
    }
    
    ranked = matcher.rank_candidates(query, gallery)
    assert len(ranked) == 3
    # Top match should be person_B
    assert ranked[0][0] == "person_B"
    # Second should be person_C
    assert ranked[1][0] == "person_C"
    # Last should be person_A
    assert ranked[2][0] == "person_A"

def test_top_k_retrieval_and_threshold():
    # Set threshold to 0.1 (must be very similar to match)
    matcher = CrossCameraMatcher(distance_threshold=0.1)
    
    query = np.array([1.0, 0.0])
    
    gallery = {
        "person_A": np.array([0.0, 1.0]),   # dist = 1.0
        "person_B": np.array([1.0, 0.01]),  # dist ~ 0.00005 (match)
        "person_C": np.array([1.0, 0.1]),   # dist ~ 0.005 (match)
        "person_D": np.array([0.8, 0.6])    # dist = 0.2 (no match)
    }
    
    top_2 = matcher.get_top_k(query, gallery, k=2)
    assert len(top_2) == 2
    # person_B and person_C are both within the 0.1 threshold
    # D is excluded because dist > 0.1
    # B is closer than C
    assert top_2[0][0] == "person_B"
    assert top_2[1][0] == "person_C"

def test_determine_identity():
    matcher = CrossCameraMatcher(distance_threshold=0.3)
    
    # Person leaving Camera 1
    person1_exit = np.array([0.8, 0.6])
    person2_exit = np.array([-0.5, 0.5])
    
    gallery = {
        "person1_cam1": person1_exit,
        "person2_cam1": person2_exit
    }
    
    # Person entering Camera 2 (same person, slight variation)
    cam2_entry_match = np.array([0.81, 0.59])
    
    # Unrelated person entering Camera 2
    cam2_entry_unknown = np.array([-0.8, -0.6])
    
    # Identify match
    identity = matcher.determine_identity(cam2_entry_match, gallery)
    assert identity == "person1_cam1"
    
    # Identify unknown
    identity_unknown = matcher.determine_identity(cam2_entry_unknown, gallery)
    assert identity_unknown is None
