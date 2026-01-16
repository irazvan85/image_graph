"""
Graph exporter for various formats
"""
from typing import Dict, Any
from pathlib import Path
import sys

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from database import Database


class GraphExporter:
    """Export graph in various formats"""
    
    def __init__(self, config, database):
        self.config = config
        self.db = database
    
    async def export_graphml(self) -> str:
        """Export graph as GraphML"""
        graph = await self._get_full_graph()
        
        graphml = '<?xml version="1.0" encoding="UTF-8"?>\n'
        graphml += '<graphml xmlns="http://graphml.graphdrawing.org/xmlns">\n'
        
        # Define attributes
        graphml += '  <key id="type" for="node" attr.name="type" attr.type="string"/>\n'
        graphml += '  <key id="label" for="node" attr.name="label" attr.type="string"/>\n'
        graphml += '  <key id="weight" for="edge" attr.name="weight" attr.type="double"/>\n'
        
        graphml += '  <graph id="G" edgedefault="directed">\n'
        
        # Add nodes
        for node in graph["nodes"]:
            graphml += f'    <node id="{node["id"]}">\n'
            graphml += f'      <data key="type">{node.get("type", "unknown")}</data>\n'
            graphml += f'      <data key="label">{self._escape_xml(node.get("label", ""))}</data>\n'
            graphml += '    </node>\n'
        
        # Add edges
        for edge in graph["edges"]:
            graphml += f'    <edge source="{edge["source"]}" target="{edge["target"]}">\n'
            graphml += f'      <data key="weight">{edge.get("weight", 1.0)}</data>\n'
            graphml += '    </edge>\n'
        
        graphml += '  </graph>\n'
        graphml += '</graphml>'
        
        return graphml
    
    async def export_cypher(self) -> str:
        """Export graph as Neo4j Cypher statements"""
        graph = await self._get_full_graph()
        
        cypher = []
        
        # Create nodes
        for node in graph["nodes"]:
            node_type = node.get("type", "Node")
            label = self._escape_cypher(node.get("label", ""))
            
            if node_type == "image":
                cypher.append(
                    f'CREATE (n:Image {{id: "{node["id"]}", file_path: "{self._escape_cypher(node.get("file_path", ""))}", label: "{label}"}})'
                )
            elif node_type == "concept":
                concept_type = node.get("concept_type", "Concept")
                cypher.append(
                    f'CREATE (n:Concept:{concept_type} {{id: "{node["id"]}", label: "{label}", normalized_label: "{self._escape_cypher(node.get("normalized_label", ""))}"}})'
                )
        
        # Create edges
        for edge in graph["edges"]:
            edge_type = edge.get("type", "RELATED")
            weight = edge.get("weight", 1.0)
            
            if edge_type == "image_concept":
                cypher.append(
                    f'MATCH (a:Image {{id: "{edge["source"]}"}}), (b:Concept {{id: "{edge["target"]}"}}) '
                    f'CREATE (a)-[:HAS_CONCEPT {{weight: {weight}, source: "{edge.get("source_type", "")}"}}]->(b)'
                )
            elif edge_type == "concept_concept":
                cypher.append(
                    f'MATCH (a:Concept {{id: "{edge["source"]}"}}), (b:Concept {{id: "{edge["target"]}"}}) '
                    f'CREATE (a)-[:CO_OCCURS {{weight: {weight}}}]->(b)'
                )
            elif edge_type == "image_image":
                similarity = edge.get("similarity", 0.0)
                cypher.append(
                    f'MATCH (a:Image {{id: "{edge["source"]}"}}), (b:Image {{id: "{edge["target"]}"}}) '
                    f'CREATE (a)-[:SIMILAR {{similarity: {similarity}}}]->(b)'
                )
        
        return "\n".join(cypher)
    
    async def _get_full_graph(self) -> Dict[str, Any]:
        """Get full graph without filters"""
        from services.graph_builder import GraphBuilder
        builder = GraphBuilder(self.config, self.db)
        return await builder.get_graph({})
    
    def _escape_xml(self, text: str) -> str:
        """Escape XML special characters"""
        return (text.replace("&", "&amp;")
                   .replace("<", "&lt;")
                   .replace(">", "&gt;")
                   .replace('"', "&quot;")
                   .replace("'", "&apos;"))
    
    def _escape_cypher(self, text: str) -> str:
        """Escape Cypher special characters"""
        return text.replace('"', '\\"').replace("\\", "\\\\")
