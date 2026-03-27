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


@pytest.mark.asyncio
async def test_compute_node_depths(test_config, test_db):
    """Test that depth is computed correctly for 3D visualization"""
    builder = GraphBuilder(test_config, test_db)
    
    # Test with image and concept nodes
    nodes = [
        {"id": "img1", "type": "image", "label": "photo.jpg"},
        {"id": "img2", "type": "image", "label": "photo2.jpg"},
        {"id": "concept1", "type": "concept", "label": "Nature"},
        {"id": "concept2", "type": "concept", "label": "Tree"},
        {"id": "concept3", "type": "concept", "label": "Water"},
    ]
    edges = [
        {"source": "img1", "target": "concept1", "type": "image_concept", "weight": 0.8},
        {"source": "img2", "target": "concept1", "type": "image_concept", "weight": 0.7},
        {"source": "img1", "target": "concept2", "type": "image_concept", "weight": 0.6},
        {"source": "concept1", "target": "concept2", "type": "concept_concept", "weight": 1.5},
        {"source": "concept1", "target": "concept3", "type": "concept_concept", "weight": 1.0},
    ]
    
    builder._compute_node_depths(nodes, edges)
    
    # Image nodes should always be at depth 0
    img_nodes = [n for n in nodes if n["type"] == "image"]
    for n in img_nodes:
        assert n["depth"] == 0
    
    # All concept nodes should have depth >= 1
    concept_nodes = [n for n in nodes if n["type"] == "concept"]
    for n in concept_nodes:
        assert n["depth"] >= 1
        assert n["depth"] <= 2
    
    # concept1 is the most connected (degree=4: 2 image_concept + 2 concept_concept)
    # so it should have depth = 2 (maximum)
    concept1 = next(n for n in nodes if n["id"] == "concept1")
    assert concept1["depth"] == 2.0
    
    # concept3 has degree=1 (only one concept_concept edge)
    # concept2 has degree=2 (1 image_concept + 1 concept_concept)
    concept3 = next(n for n in nodes if n["id"] == "concept3")
    concept2 = next(n for n in nodes if n["id"] == "concept2")
    assert concept3["depth"] < concept2["depth"]
    assert concept2["depth"] < concept1["depth"]


@pytest.mark.asyncio
async def test_compute_node_depths_empty(test_config, test_db):
    """Test depth computation with no edges"""
    builder = GraphBuilder(test_config, test_db)
    
    nodes = [
        {"id": "img1", "type": "image", "label": "photo.jpg"},
        {"id": "concept1", "type": "concept", "label": "Nature"},
    ]
    edges = []
    
    builder._compute_node_depths(nodes, edges)
    
    # Image should be depth 0
    assert nodes[0]["depth"] == 0
    # Concept with no edges should be depth 1 (base concept layer)
    assert nodes[1]["depth"] == 1


@pytest.mark.asyncio
async def test_get_graph_includes_depth(test_config, test_db):
    """Test that get_graph returns depth property on nodes"""
    # Add test data
    await test_db.save_image({
        "file_path": "/test/image1.jpg",
        "file_hash": "hash1",
        "created_time": 1000,
        "modified_time": 1000,
        "width": 100,
        "height": 100,
        "file_size": 1000
    })
    
    concept_id = await test_db.get_or_create_concept("nature", "nature", "tag")
    
    builder = GraphBuilder(test_config, test_db)
    graph = await builder.get_graph({})
    
    # All nodes should have a depth property
    for node in graph["nodes"]:
        assert "depth" in node
        if node["type"] == "image":
            assert node["depth"] == 0
        elif node["type"] == "concept":
            assert node["depth"] >= 1
