"""Shared demo data for Vercel serverless API functions."""

DEMO_GRAPH = {
    "nodes": [
        {
            "id": "abc123def456",
            "type": "image",
            "label": "vacation_photo.jpg",
            "file_path": "demo/vacation_photo.jpg"
        },
        {
            "id": "xyz789ghi012",
            "type": "image",
            "label": "beach_sunset.png",
            "file_path": "demo/beach_sunset.png"
        },
        {
            "id": "concept_car",
            "type": "concept",
            "label": "Car",
            "normalized_label": "car",
            "concept_type": "tag"
        },
        {
            "id": "concept_beach",
            "type": "concept",
            "label": "Beach",
            "normalized_label": "beach",
            "concept_type": "tag"
        },
        {
            "id": "concept_sunset",
            "type": "concept",
            "label": "Sunset",
            "normalized_label": "sunset",
            "concept_type": "tag"
        }
    ],
    "edges": [
        {
            "id": "ic_abc123def456_concept_car",
            "source": "abc123def456",
            "target": "concept_car",
            "type": "image_concept",
            "weight": 0.7,
            "source_type": "caption"
        },
        {
            "id": "ic_xyz789ghi012_concept_beach",
            "source": "xyz789ghi012",
            "target": "concept_beach",
            "type": "image_concept",
            "weight": 0.8,
            "source_type": "caption"
        },
        {
            "id": "ic_xyz789ghi012_concept_sunset",
            "source": "xyz789ghi012",
            "target": "concept_sunset",
            "type": "image_concept",
            "weight": 0.9,
            "source_type": "caption"
        },
        {
            "id": "cc_concept_beach_concept_sunset",
            "source": "concept_beach",
            "target": "concept_sunset",
            "type": "concept_concept",
            "weight": 1.0
        },
        {
            "id": "ii_abc123def456_xyz789ghi012",
            "source": "abc123def456",
            "target": "xyz789ghi012",
            "type": "image_image",
            "similarity": 0.87
        }
    ]
}
