"""
Unit tests for database
"""
import pytest
import tempfile
import os

from database import Database
from config import Config


@pytest.fixture
async def test_db():
    """Create test database"""
    config = Config()
    test_db_path = tempfile.mktemp(suffix='.db')
    config.config["storage"]["database_path"] = test_db_path
    
    db = Database(config)
    await db.initialize()
    yield db
    await db.close()
    if os.path.exists(test_db_path):
        os.remove(test_db_path)


@pytest.mark.asyncio
async def test_save_and_get_image(test_db):
    """Test saving and retrieving image"""
    image_data = {
        "file_path": "/test/image.jpg",
        "file_hash": "test_hash",
        "created_time": 1000.0,
        "modified_time": 1000.0,
        "width": 100,
        "height": 100,
        "file_size": 5000
    }
    
    image_id = await test_db.save_image(image_data)
    assert image_id is not None
    
    metadata = await test_db.get_image_metadata(image_id)
    assert metadata is not None
    assert metadata["file_path"] == image_data["file_path"]


@pytest.mark.asyncio
async def test_get_or_create_concept(test_db):
    """Test concept creation"""
    concept_id1 = await test_db.get_or_create_concept("Test", "test", "tag")
    concept_id2 = await test_db.get_or_create_concept("Test", "test", "tag")
    
    # Should return same ID for same normalized label
    assert concept_id1 == concept_id2


@pytest.mark.asyncio
async def test_create_edges(test_db):
    """Test edge creation"""
    image_id = await test_db.save_image({
        "file_path": "/test/image.jpg",
        "file_hash": "hash",
        "created_time": 1000,
        "modified_time": 1000,
        "width": 100,
        "height": 100,
        "file_size": 1000
    })
    
    concept_id = await test_db.get_or_create_concept("test", "test", "tag")
    
    # Create image-concept edge
    await test_db.create_image_concept_edge(image_id, concept_id, 0.7, "caption")
    
    # Verify edge exists
    async with test_db.conn.execute("""
        SELECT COUNT(*) FROM image_concept_edges
        WHERE image_id = ? AND concept_id = ?
    """, (image_id, concept_id)) as cursor:
        count = (await cursor.fetchone())[0]
        assert count == 1
