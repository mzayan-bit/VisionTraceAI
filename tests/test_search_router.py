import pytest
from backend.search.search_router import SearchRouter

def test_route_query_yolo_classes():
    # Exact COCO classes should route to vector_search
    assert SearchRouter.route_query("person") == "vector_search"
    assert SearchRouter.route_query("car") == "vector_search"
    assert SearchRouter.route_query("backpack") == "vector_search"
    assert SearchRouter.route_query("laptop") == "vector_search"

def test_route_query_open_vocab():
    # Non-COCO classes or complex descriptions should route to grounding_dino
    assert SearchRouter.route_query("red extinguisher") == "grounding_dino"
    assert SearchRouter.route_query("unknown object") == "grounding_dino"
    assert SearchRouter.route_query("red car") == "grounding_dino"

def test_route_query_formatting():
    # Whitespace and capitalization shouldn't matter for the core classes
    assert SearchRouter.route_query("  PERSON  ") == "vector_search"
    assert SearchRouter.route_query("Car") == "vector_search"
