"""
Tests for the Kafka StreamingPipelineConsumer.

Covers message batch processing, retry mechanics, failure isolation, and 
downstream integrations (Redis, Qdrant, SigLIP, FastReID) using mocks.
"""

import json
from unittest.mock import MagicMock, patch

import pytest
from PIL import Image

from backend.streaming.kafka_consumer import StreamingPipelineConsumer


@pytest.fixture
def mock_consumer_deps():
    """Mocks all the heavy ML/DB dependencies for the consumer."""
    with patch("backend.streaming.kafka_consumer.SigLIPEmbeddingService") as mock_siglip, \
         patch("backend.streaming.kafka_consumer.QdrantService") as mock_qdrant, \
         patch("backend.streaming.kafka_consumer.TrajectoryStore") as mock_redis, \
         patch("backend.streaming.kafka_consumer.ReIDEngine") as mock_reid, \
         patch("backend.streaming.kafka_consumer.Image.open") as mock_image_open:
        
        # Setup mocks
        mock_siglip_inst = mock_siglip.return_value
        mock_siglip_inst.encode_image.return_value = MagicMock(tolist=lambda: [0.1, 0.2, 0.3])
        
        mock_qdrant_inst = mock_qdrant.return_value
        mock_redis_inst = mock_redis.return_value
        mock_reid_inst = mock_reid.return_value
        
        mock_image_open.return_value.convert.return_value = "mocked_rgb_image"
        
        yield {
            "siglip": mock_siglip_inst,
            "qdrant": mock_qdrant_inst,
            "redis": mock_redis_inst,
            "reid": mock_reid_inst,
            "image": mock_image_open
        }


@pytest.fixture
def consumer(mock_consumer_deps):
    """Returns a consumer instance with initialized mocks and mocked Kafka Consumer."""
    with patch("confluent_kafka.Consumer") as mock_kafka_consumer:
        c = StreamingPipelineConsumer(batch_size=2)
        c.connect()
        c.consumer = mock_kafka_consumer.return_value
        yield c


def test_consumer_initialization(consumer):
    """Test that services are initialized upon connect."""
    assert consumer.embedder is not None
    assert consumer.qdrant is not None
    assert consumer.trajectory_store is not None
    assert consumer.reid is not None
    
    # Check that qdrant was connected
    consumer.qdrant.connect.assert_called_once()
    consumer.trajectory_store.connect.assert_called_once()


def test_process_batch_with_missing_image(consumer, mock_consumer_deps):
    """Test processing an event when the crop image is missing on disk."""
    event = {
        "frame_id": 1,
        "track_id": 100,
        "camera_id": "cam_1",
        "timestamp": 0.5,
        "bbox": {"x1": 0, "y1": 0, "x2": 10, "y2": 10}
    }
    
    msg = MagicMock()
    msg.error.return_value = False
    msg.value.return_value = json.dumps(event).encode("utf-8")
    
    with patch.object(StreamingPipelineConsumer, "get_crop_path") as mock_path:
        # Mock path exists to return False
        mock_path.return_value.exists.return_value = False
        
        consumer._process_batch([msg])
        
        # Redis should be updated even if image is missing
        mock_consumer_deps["redis"].save_track.assert_called_once_with(
            track_id=100, camera_id="cam_1", timestamp=0.5, bbox=event["bbox"]
        )
        
        # Qdrant and SigLIP should NOT be called
        mock_consumer_deps["siglip"].encode_image.assert_not_called()
        mock_consumer_deps["qdrant"].insert_vector.assert_not_called()


def test_process_batch_with_valid_image(consumer, mock_consumer_deps):
    """Test full processing pipeline when crop image is present."""
    event = {
        "frame_id": 2,
        "track_id": 200,
        "camera_id": "cam_2",
        "timestamp": 1.0,
        "bbox": {"x1": 0, "y1": 0, "x2": 10, "y2": 10}
    }
    
    msg = MagicMock()
    msg.error.return_value = False
    msg.value.return_value = json.dumps(event).encode("utf-8")
    
    with patch.object(StreamingPipelineConsumer, "get_crop_path") as mock_path:
        # Mock path exists
        mock_path_obj = MagicMock()
        mock_path_obj.exists.return_value = True
        mock_path_obj.__str__.return_value = "/fake/path.jpg"
        mock_path.return_value = mock_path_obj
        
        consumer._process_batch([msg])
        
        # Redis updated
        mock_consumer_deps["redis"].save_track.assert_called_once()
        
        # Image opened
        mock_consumer_deps["image"].assert_called_once_with(mock_path_obj)
        
        # SigLIP and Qdrant called
        mock_consumer_deps["siglip"].encode_image.assert_called_once()
        mock_consumer_deps["qdrant"].insert_vector.assert_called_once()
        
        # FastReID called
        mock_consumer_deps["reid"].extract_features.assert_called_once()


def test_process_batch_failure_isolation(consumer):
    """Test that a bad JSON message doesn't crash the batch."""
    bad_msg = MagicMock()
    bad_msg.error.return_value = False
    bad_msg.value.return_value = b"{invalid_json"
    
    good_event = {"frame_id": 1, "track_id": 1, "camera_id": "cam_1"}
    good_msg = MagicMock()
    good_msg.error.return_value = False
    good_msg.value.return_value = json.dumps(good_event).encode("utf-8")
    
    with patch.object(consumer, "_process_event") as mock_process:
        consumer._process_batch([bad_msg, good_msg])
        # _process_event should only be called once for the good message
        mock_process.assert_called_once_with(good_event)


def test_process_batch_retry_mechanism(consumer):
    """Test that internal processing exceptions trigger retries."""
    event = {"frame_id": 1, "track_id": 1, "camera_id": "cam_1"}
    msg = MagicMock()
    msg.error.return_value = False
    msg.value.return_value = json.dumps(event).encode("utf-8")
    
    with patch.object(consumer, "_process_event") as mock_process:
        # Fail twice, succeed on third
        mock_process.side_effect = [Exception("Temporary DB glitch"), Exception("Glitch again"), None]
        
        with patch("time.sleep") as mock_sleep: # Don't actually sleep in tests
            consumer._process_batch([msg])
            
            # _process_event called 3 times
            assert mock_process.call_count == 3
            # Sleep called twice
            assert mock_sleep.call_count == 2
