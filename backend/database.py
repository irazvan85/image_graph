"""
Database layer for ImageGraph
"""
import aiosqlite
import json
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime
import hashlib


class Database:
    """SQLite database manager"""
    
    def __init__(self, config):
        self.config = config
        self.db_path = Path(config.database_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.conn = None
    
    async def initialize(self):
        """Initialize database and create tables"""
        self.conn = await aiosqlite.connect(self.db_path)
        await self._create_tables()
    
    async def close(self):
        """Close database connection"""
        if self.conn:
            await self.conn.close()
    
    async def _create_tables(self):
        """Create database tables"""
        await self.conn.execute("""
            CREATE TABLE IF NOT EXISTS images (
                id TEXT PRIMARY KEY,
                file_path TEXT UNIQUE NOT NULL,
                file_hash TEXT,
                created_time REAL,
                modified_time REAL,
                width INTEGER,
                height INTEGER,
                file_size INTEGER,
                thumbnail_path TEXT,
                processed_at REAL
            )
        """)
        
        await self.conn.execute("""
            CREATE TABLE IF NOT EXISTS image_metadata (
                image_id TEXT PRIMARY KEY,
                caption TEXT,
                tags TEXT,  -- JSON array
                ocr_text TEXT,
                ocr_entities TEXT,  -- JSON array
                embedding_id INTEGER,
                FOREIGN KEY (image_id) REFERENCES images(id)
            )
        """)
        
        await self.conn.execute("""
            CREATE TABLE IF NOT EXISTS concepts (
                id TEXT PRIMARY KEY,
                label TEXT NOT NULL,
                normalized_label TEXT UNIQUE NOT NULL,
                concept_type TEXT,  -- tag, entity, text_entity
                description TEXT,
                created_at REAL
            )
        """)
        
        await self.conn.execute("""
            CREATE TABLE IF NOT EXISTS image_concept_edges (
                id TEXT PRIMARY KEY,
                image_id TEXT NOT NULL,
                concept_id TEXT NOT NULL,
                weight REAL,
                source TEXT,  -- caption, ocr, detection, etc.
                FOREIGN KEY (image_id) REFERENCES images(id),
                FOREIGN KEY (concept_id) REFERENCES concepts(id),
                UNIQUE(image_id, concept_id, source)
            )
        """)
        
        await self.conn.execute("""
            CREATE TABLE IF NOT EXISTS concept_concept_edges (
                id TEXT PRIMARY KEY,
                source_concept_id TEXT NOT NULL,
                target_concept_id TEXT NOT NULL,
                weight REAL,
                FOREIGN KEY (source_concept_id) REFERENCES concepts(id),
                FOREIGN KEY (target_concept_id) REFERENCES concepts(id),
                UNIQUE(source_concept_id, target_concept_id)
            )
        """)
        
        await self.conn.execute("""
            CREATE TABLE IF NOT EXISTS image_image_edges (
                id TEXT PRIMARY KEY,
                source_image_id TEXT NOT NULL,
                target_image_id TEXT NOT NULL,
                similarity REAL,
                FOREIGN KEY (source_image_id) REFERENCES images(id),
                FOREIGN KEY (target_image_id) REFERENCES images(id),
                UNIQUE(source_image_id, target_image_id)
            )
        """)
        
        await self.conn.execute("""
            CREATE TABLE IF NOT EXISTS embeddings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                image_id TEXT,
                embedding BLOB,  -- Serialized numpy array
                FOREIGN KEY (image_id) REFERENCES images(id)
            )
        """)
        
        # Create indexes
        await self.conn.execute("CREATE INDEX IF NOT EXISTS idx_image_path ON images(file_path)")
        await self.conn.execute("CREATE INDEX IF NOT EXISTS idx_concept_normalized ON concepts(normalized_label)")
        await self.conn.execute("CREATE INDEX IF NOT EXISTS idx_image_concept_image ON image_concept_edges(image_id)")
        await self.conn.execute("CREATE INDEX IF NOT EXISTS idx_image_concept_concept ON image_concept_edges(concept_id)")
        
        await self.conn.commit()
    
    def _generate_id(self, *args) -> str:
        """Generate a deterministic ID from arguments"""
        combined = "|".join(str(arg) for arg in args)
        return hashlib.md5(combined.encode()).hexdigest()
    
    async def save_image(self, image_data: Dict[str, Any]) -> str:
        """Save image record"""
        image_id = self._generate_id(image_data["file_path"])
        
        await self.conn.execute("""
            INSERT OR REPLACE INTO images 
            (id, file_path, file_hash, created_time, modified_time, width, height, file_size, thumbnail_path, processed_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            image_id,
            image_data["file_path"],
            image_data.get("file_hash"),
            image_data.get("created_time"),
            image_data.get("modified_time"),
            image_data.get("width"),
            image_data.get("height"),
            image_data.get("file_size"),
            image_data.get("thumbnail_path"),
            datetime.now().timestamp()
        ))
        
        await self.conn.commit()
        return image_id
    
    async def save_image_metadata(self, image_id: str, metadata: Dict[str, Any]):
        """Save image metadata"""
        await self.conn.execute("""
            INSERT OR REPLACE INTO image_metadata
            (image_id, caption, tags, ocr_text, ocr_entities, embedding_id)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            image_id,
            metadata.get("caption"),
            json.dumps(metadata.get("tags", [])),
            metadata.get("ocr_text"),
            json.dumps(metadata.get("ocr_entities", [])),
            metadata.get("embedding_id")
        ))
        
        await self.conn.commit()
    
    async def save_embedding(self, image_id: str, embedding: bytes) -> int:
        """Save image embedding"""
        cursor = await self.conn.execute("""
            INSERT INTO embeddings (image_id, embedding) VALUES (?, ?)
        """, (image_id, embedding))
        
        await self.conn.commit()
        return cursor.lastrowid
    
    async def get_image_metadata(self, image_id: str) -> Optional[Dict[str, Any]]:
        """Get image metadata"""
        async with self.conn.execute("""
            SELECT i.*, im.caption, im.tags, im.ocr_text, im.ocr_entities, im.embedding_id
            FROM images i
            LEFT JOIN image_metadata im ON i.id = im.image_id
            WHERE i.id = ?
        """, (image_id,)) as cursor:
            row = await cursor.fetchone()
            if not row:
                return None
            
            return {
                "id": row[0],
                "file_path": row[1],
                "file_hash": row[2],
                "created_time": row[3],
                "modified_time": row[4],
                "width": row[5],
                "height": row[6],
                "file_size": row[7],
                "thumbnail_path": row[8],
                "caption": row[10],
                "tags": json.loads(row[11]) if row[11] else [],
                "ocr_text": row[12],
                "ocr_entities": json.loads(row[13]) if row[13] else [],
                "embedding_id": row[14]
            }
    
    async def get_or_create_concept(self, label: str, normalized_label: str, concept_type: str = "tag") -> str:
        """Get or create a concept"""
        concept_id = self._generate_id(normalized_label)
        
        await self.conn.execute("""
            INSERT OR IGNORE INTO concepts (id, label, normalized_label, concept_type, created_at)
            VALUES (?, ?, ?, ?, ?)
        """, (concept_id, label, normalized_label, concept_type, datetime.now().timestamp()))
        
        await self.conn.commit()
        return concept_id
    
    async def create_image_concept_edge(self, image_id: str, concept_id: str, weight: float, source: str):
        """Create image-concept edge"""
        edge_id = self._generate_id(image_id, concept_id, source)
        
        await self.conn.execute("""
            INSERT OR REPLACE INTO image_concept_edges (id, image_id, concept_id, weight, source)
            VALUES (?, ?, ?, ?, ?)
        """, (edge_id, image_id, concept_id, weight, source))
        
        await self.conn.commit()
    
    async def create_concept_concept_edge(self, source_concept_id: str, target_concept_id: str, weight: float):
        """Create or update concept-concept edge"""
        edge_id = self._generate_id(source_concept_id, target_concept_id)
        
        await self.conn.execute("""
            INSERT INTO concept_concept_edges (id, source_concept_id, target_concept_id, weight)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(id) DO UPDATE SET weight = weight + ?
        """, (edge_id, source_concept_id, target_concept_id, weight, weight))
        
        await self.conn.commit()
    
    async def create_image_image_edge(self, source_image_id: str, target_image_id: str, similarity: float):
        """Create image-image edge"""
        edge_id = self._generate_id(source_image_id, target_image_id)
        
        await self.conn.execute("""
            INSERT OR REPLACE INTO image_image_edges (id, source_image_id, target_image_id, similarity)
            VALUES (?, ?, ?, ?)
        """, (edge_id, source_image_id, target_image_id, similarity))
        
        await self.conn.commit()
    
    async def get_processed_files(self) -> List[str]:
        """Get list of already processed file paths"""
        async with self.conn.execute("SELECT file_path FROM images") as cursor:
            rows = await cursor.fetchall()
            return [row[0] for row in rows]
    
    async def get_all_images(self) -> List[str]:
        """Get all image IDs"""
        async with self.conn.execute("SELECT id FROM images") as cursor:
            rows = await cursor.fetchall()
            return [row[0] for row in rows]
    
    async def get_all_embeddings(self) -> List[tuple]:
        """Get all embeddings (image_id, embedding_id, embedding)"""
        async with self.conn.execute("SELECT image_id, id, embedding FROM embeddings") as cursor:
            return await cursor.fetchall()
