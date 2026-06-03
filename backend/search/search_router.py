"""
VisionTraceAI — Search Router.

Routes text queries to either Vector Search (for known YOLO classes)
or Grounding DINO (for open-vocabulary objects).
"""

from typing import Literal

# COCO dataset classes commonly used by YOLOv8 models (80 classes)
YOLO_CLASSES = {
    "person", "bicycle", "car", "motorcycle", "airplane", "bus", "train", "truck", "boat",
    "traffic light", "fire hydrant", "stop sign", "parking meter", "bench", "bird", "cat", "dog",
    "horse", "sheep", "cow", "elephant", "bear", "zebra", "giraffe", "backpack", "umbrella",
    "handbag", "tie", "suitcase", "frisbee", "skis", "snowboard", "sports ball", "kite",
    "baseball bat", "baseball glove", "skateboard", "surfboard", "tennis racket", "bottle",
    "wine glass", "cup", "fork", "knife", "spoon", "bowl", "banana", "apple", "sandwich",
    "orange", "broccoli", "carrot", "hot dog", "pizza", "donut", "cake", "chair", "couch",
    "potted plant", "bed", "dining table", "toilet", "tv", "laptop", "mouse", "remote",
    "keyboard", "cell phone", "microwave", "oven", "toaster", "sink", "refrigerator", "book",
    "clock", "vase", "scissors", "teddy bear", "hair drier", "toothbrush"
}

class SearchRouter:
    """Routes text search queries to the appropriate engine."""

    @staticmethod
    def route_query(query: str) -> Literal["vector_search", "grounding_dino"]:
        """
        Determine the search backend for a given query.
        
        Args:
            query: The text query (e.g., 'person', 'red fire extinguisher').
            
        Returns:
            "vector_search" if the query is a known YOLO class.
            "grounding_dino" for open-vocabulary queries.
        """
        query_normalized = query.strip().lower()
        
        if query_normalized in YOLO_CLASSES:
            return "vector_search"
        return "grounding_dino"


def _run_validation() -> None:
    print("═" * 50)
    print("🔍 VisionTraceAI — Search Router Validation")
    print("═" * 50)
    
    queries = [
        "person",
        "car",
        "backpack",
        "red extinguisher"
    ]
    
    for q in queries:
        route = SearchRouter.route_query(q)
        print(f"Query: '{q}' -> Route: {route}")
        
    print("═" * 50)


if __name__ == "__main__":
    _run_validation()
