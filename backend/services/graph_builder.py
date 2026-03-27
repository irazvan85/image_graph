"""
Knowledge graph builder
"""
import pickle
import numpy as np
from typing import Dict, Any, List, Set
from collections import defaultdict
from pathlib import Path
import inflect
import re
import sys

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from database import Database


class GraphBuilder:
    """Builds knowledge graph from processed images"""
    
    def __init__(self, config, database):
        self.config = config
        self.db = database
        self.inflect_engine = inflect.engine()
        self.similarity_threshold = config.similarity_threshold
        self.confidence_threshold = config.confidence_threshold
        self.image_similarity_threshold = config.image_similarity_threshold
    
    async def build_graph(self):
        """Build complete knowledge graph"""
        # Get all images
        image_ids = await self.db.get_all_images()
        
        # Build image-concept edges
        for image_id in image_ids:
            await self._process_image_concepts(image_id)
        
        # Build concept-concept edges (co-occurrence)
        await self._build_concept_cooccurrence()
        
        # Build image-image edges (similarity)
        await self._build_image_similarity()
    
    async def _process_image_concepts(self, image_id: str):
        """Process concepts for a single image"""
        metadata = await self.db.get_image_metadata(image_id)
        if not metadata:
            return
        
        # Process tags from caption
        tags = metadata.get("tags", [])
        for tag in tags:
            normalized = self._normalize_concept(tag)
            if normalized:
                concept_id = await self.db.get_or_create_concept(tag, normalized, "tag")
                await self.db.create_image_concept_edge(image_id, concept_id, 0.7, "caption")
        
        # Process OCR entities
        ocr_entities = metadata.get("ocr_entities", [])
        for entity in ocr_entities:
            value = entity.get("value", "")
            entity_type = entity.get("type", "text_entity")
            normalized = self._normalize_concept(value)
            if normalized:
                concept_id = await self.db.get_or_create_concept(value, normalized, entity_type)
                await self.db.create_image_concept_edge(image_id, concept_id, 0.5, "ocr")
    
    def _normalize_concept(self, concept: str) -> str:
        """Normalize concept label"""
        if not concept:
            return None
        
        # Lowercase and trim
        normalized = concept.lower().strip()
        
        # Remove special characters (keep alphanumeric and spaces)
        normalized = re.sub(r'[^a-z0-9\s]', '', normalized)
        
        # Remove extra spaces
        normalized = re.sub(r'\s+', ' ', normalized).strip()
        
        # Basic singularization
        try:
            singular = self.inflect_engine.singular_noun(normalized)
            if singular:
                normalized = singular
        except:
            pass
        
        # Minimum length check
        if len(normalized) < 2:
            return None
        
        return normalized
    
    async def _build_concept_cooccurrence(self):
        """Build concept-concept edges based on co-occurrence"""
        # Get all image-concept edges
        async with self.db.conn.execute("""
            SELECT image_id, concept_id FROM image_concept_edges
        """) as cursor:
            image_concepts = await cursor.fetchall()
        
        # Group concepts by image
        image_to_concepts = defaultdict(set)
        for image_id, concept_id in image_concepts:
            image_to_concepts[image_id].add(concept_id)
        
        # Count co-occurrences
        cooccurrence = defaultdict(float)
        for concepts in image_to_concepts.values():
            concepts_list = list(concepts)
            for i, concept1 in enumerate(concepts_list):
                for concept2 in concepts_list[i+1:]:
                    pair = tuple(sorted([concept1, concept2]))
                    cooccurrence[pair] += 1.0
        
        # Create edges with decay
        decay = self.config.get("graph.co_occurrence_decay", 0.95)
        for (concept1, concept2), count in cooccurrence.items():
            weight = count * decay
            if weight >= self.config.get("graph.min_concept_weight", 0.1):
                await self.db.create_concept_concept_edge(concept1, concept2, weight)
    
    async def _build_image_similarity(self):
        """Build image-image edges based on embedding similarity"""
        # Get all embeddings
        embeddings_data = await self.db.get_all_embeddings()
        
        if len(embeddings_data) < 2:
            return
        
        # Load embeddings
        embeddings = {}
        for image_id, embedding_id, embedding_blob in embeddings_data:
            embedding = pickle.loads(embedding_blob)
            embeddings[image_id] = embedding
        
        # Compute pairwise similarities
        image_ids = list(embeddings.keys())
        for i, image1_id in enumerate(image_ids):
            embedding1 = embeddings[image1_id]
            for image2_id in image_ids[i+1:]:
                embedding2 = embeddings[image2_id]
                
                # Cosine similarity
                similarity = np.dot(embedding1, embedding2) / (
                    np.linalg.norm(embedding1) * np.linalg.norm(embedding2)
                )
                
                if similarity >= self.image_similarity_threshold:
                    await self.db.create_image_image_edge(image1_id, image2_id, float(similarity))
    
    async def get_graph(self, filters: Dict[str, Any] = None) -> Dict[str, Any]:
        """Get graph data with optional filters"""
        filters = filters or {}
        min_confidence = filters.get("min_confidence", self.confidence_threshold)
        min_similarity = filters.get("min_similarity", self.similarity_threshold)
        search_query = filters.get("search_query", "").lower()
        concept_types = filters.get("concept_types", [])
        
        nodes = []
        edges = []
        
        # Get images
        async with self.db.conn.execute("SELECT id, file_path FROM images") as cursor:
            image_rows = await cursor.fetchall()
            for image_id, file_path in image_rows:
                nodes.append({
                    "id": image_id,
                    "type": "image",
                    "label": Path(file_path).name,
                    "file_path": file_path
                })
        
        # Get concepts
        concept_query = "SELECT id, label, normalized_label, concept_type FROM concepts"
        if concept_types:
            placeholders = ",".join(["?"] * len(concept_types))
            concept_query += f" WHERE concept_type IN ({placeholders})"
        
        async with self.db.conn.execute(concept_query, concept_types if concept_types else []) as cursor:
            concept_rows = await cursor.fetchall()
            for concept_id, label, normalized_label, concept_type in concept_rows:
                # Filter by search query
                if search_query and search_query not in normalized_label.lower():
                    continue
                
                nodes.append({
                    "id": concept_id,
                    "type": "concept",
                    "label": label,
                    "normalized_label": normalized_label,
                    "concept_type": concept_type
                })
        
        # Create a set of valid node IDs for filtering edges
        valid_node_ids = {node["id"] for node in nodes}
        
        # Get image-concept edges
        async with self.db.conn.execute("""
            SELECT image_id, concept_id, weight, source
            FROM image_concept_edges
            WHERE weight >= ?
        """, (min_confidence,)) as cursor:
            edge_rows = await cursor.fetchall()
            for image_id, concept_id, weight, source in edge_rows:
                # Only include edge if both nodes exist in filtered nodes
                if image_id in valid_node_ids and concept_id in valid_node_ids:
                    edges.append({
                        "id": f"ic_{image_id}_{concept_id}",
                        "source": image_id,
                        "target": concept_id,
                        "type": "image_concept",
                        "weight": weight,
                        "source_type": source
                    })
        
        # Get concept-concept edges
        async with self.db.conn.execute("""
            SELECT source_concept_id, target_concept_id, weight
            FROM concept_concept_edges
            WHERE weight >= ?
        """, (min_confidence,)) as cursor:
            edge_rows = await cursor.fetchall()
            for source_id, target_id, weight in edge_rows:
                # Only include edge if both nodes exist in filtered nodes
                if source_id in valid_node_ids and target_id in valid_node_ids:
                    edges.append({
                        "id": f"cc_{source_id}_{target_id}",
                        "source": source_id,
                        "target": target_id,
                        "type": "concept_concept",
                        "weight": weight
                    })
        
        # Get image-image edges
        async with self.db.conn.execute("""
            SELECT source_image_id, target_image_id, similarity
            FROM image_image_edges
            WHERE similarity >= ?
        """, (min_similarity,)) as cursor:
            edge_rows = await cursor.fetchall()
            for source_id, target_id, similarity in edge_rows:
                # Only include edge if both nodes exist in filtered nodes
                if source_id in valid_node_ids and target_id in valid_node_ids:
                    edges.append({
                        "id": f"ii_{source_id}_{target_id}",
                        "source": source_id,
                        "target": target_id,
                        "type": "image_image",
                        "similarity": similarity
                    })
        
        # Compute depth (Z-layer) for 3D visualization
        # Images at depth 0 (concrete), concepts at depth 1+ based on connectivity
        self._compute_node_depths(nodes, edges)
        
        return {
            "nodes": nodes,
            "edges": edges
        }
    
    def _compute_node_depths(self, nodes: List[Dict], edges: List[Dict]):
        """Compute semantic depth for each node for 3D visualization.
        
        Depth represents semantic abstraction level:
        - Layer 0: Image nodes (most concrete)
        - Layer 1: Direct concept nodes (tags/entities with few connections)
        - Layer 2+: Hub/abstract concepts (highly connected concepts)
        
        The Z-axis encodes how abstract or central a concept is,
        creating a visual hierarchy from concrete images to abstract themes.
        """
        # Count connections per concept node
        concept_degree = {}
        for edge in edges:
            if edge.get("type") == "image_concept":
                target = edge["target"]
                concept_degree[target] = concept_degree.get(target, 0) + 1
            elif edge.get("type") == "concept_concept":
                src = edge["source"]
                tgt = edge["target"]
                concept_degree[src] = concept_degree.get(src, 0) + 1
                concept_degree[tgt] = concept_degree.get(tgt, 0) + 1
        
        # Find max degree for normalization
        max_degree = max(concept_degree.values()) if concept_degree else 1
        
        for node in nodes:
            if node["type"] == "image":
                node["depth"] = 0
            elif node["type"] == "concept":
                degree = concept_degree.get(node["id"], 0)
                # Normalize degree to [1, 2] range
                # depth=1 for leaf concepts, depth=2 for most connected hub concepts
                normalized = degree / max_degree if max_degree > 0 else 0
                node["depth"] = round(1 + normalized, 2)
            else:
                node["depth"] = 0
