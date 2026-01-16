"""
Unit tests for graph builder
"""
import pytest
import asyncio
from pathlib import Path
import tempfile
import os

from services.graph_builder import GraphBuilder
from database import Database
from config import Config


@pytest.fixture
async def test_db():
    """Create test database"""
    config = Config()
    # Use temporary database
    test_db_path = tempfile.mktemp(suffix='.db')
    config.config["storage"]["database_path"] = test_db_path
    
    db = Database(config)
    await db.initialize()
    yield db
    await db.close()
    # Cleanup
    if os.path.exists(test_db_path):
        os.remove(test_db_path)


@pytest.fixture
def test_config():
    """Create test config"""
    config = Config()
    config.config["processing"]["similarity_threshold"] = 0.7
    config.config["processing"]["confidence_threshold"] = 0.3
    config.config["processing"]["image_similarity_threshold"] = 0.85
    return config


@pytest.mark.asyncio
async def test_normalize_concept(test_config, test_db):
    """Test concept normalization"""
    builder = GraphBuilder(test_config, test_db)
    
    assert builder._normalize_concept("Car") == "car"
    assert builder._normalize_concept("  Multiple   Words  ") == "multiple words"
    assert builder._normalize_concept("Test@#$%") == "test"
    assert builder._normalize_concept("a") is None
    assert builder._normalize_concept("") is None


@pytest.mark.asyncio
async def test_get_graph_empty(test_config, test_db):
    """Test getting empty graph"""
    builder = GraphBuilder(test_config, test_db)
    graph = await builder.get_graph({})
    
    assert graph["nodes"] == []
    assert graph["edges"] == []


@pytest.mark.asyncio
async def test_get_graph_with_filters(test_config, test_db):
    """Test graph filtering"""
    # Add test data
    image_id = "test_image_1"
    await test_db.save_image({
        "file_path": "/test/image1.jpg",
        "file_hash": "hash1",
        "created_time": 1000,
        "modified_time": 1000,
        "width": 100,
        "height": 100,
        "file_size": 1000
    })
    
    concept_id = await test_db.get_or_create_concept("test", "test", "tag")
    await test_db.create_image_concept_edge(image_id, concept_id, 0.5, "caption")
    
    builder = GraphBuilder(test_config, test_db)
    
    # Test with high confidence threshold (should filter out edge)
    graph = await builder.get_graph({"min_confidence": 0.8})
    assert len(graph["edges"]) == 0
    
    # Test with low confidence threshold (should include edge)
    graph = await builder.get_graph({"min_confidence": 0.3})
    assert len(graph["edges"]) > 0
