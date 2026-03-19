// Demo graph data for Vercel deployment preview
export const DEMO_GRAPH = {
  nodes: [
    {
      id: 'img_mountain_lake',
      type: 'image',
      label: 'mountain_lake.jpg',
      file_path: 'demo/mountain_lake.jpg'
    },
    {
      id: 'img_city_night',
      type: 'image',
      label: 'city_night.jpg',
      file_path: 'demo/city_night.jpg'
    },
    {
      id: 'img_forest_path',
      type: 'image',
      label: 'forest_path.jpg',
      file_path: 'demo/forest_path.jpg'
    },
    {
      id: 'img_beach_sunset',
      type: 'image',
      label: 'beach_sunset.png',
      file_path: 'demo/beach_sunset.png'
    },
    {
      id: 'concept_water',
      type: 'concept',
      label: 'Water',
      normalized_label: 'water',
      concept_type: 'tag'
    },
    {
      id: 'concept_nature',
      type: 'concept',
      label: 'Nature',
      normalized_label: 'nature',
      concept_type: 'tag'
    },
    {
      id: 'concept_mountains',
      type: 'concept',
      label: 'Mountains',
      normalized_label: 'mountains',
      concept_type: 'tag'
    },
    {
      id: 'concept_sunset',
      type: 'concept',
      label: 'Sunset',
      normalized_label: 'sunset',
      concept_type: 'tag'
    },
    {
      id: 'concept_urban',
      type: 'concept',
      label: 'Urban',
      normalized_label: 'urban',
      concept_type: 'tag'
    },
    {
      id: 'concept_trees',
      type: 'concept',
      label: 'Trees',
      normalized_label: 'trees',
      concept_type: 'tag'
    }
  ],
  edges: [
    { id: 'e1', source: 'img_mountain_lake', target: 'concept_water', type: 'image_concept', weight: 0.9 },
    { id: 'e2', source: 'img_mountain_lake', target: 'concept_mountains', type: 'image_concept', weight: 0.85 },
    { id: 'e3', source: 'img_mountain_lake', target: 'concept_nature', type: 'image_concept', weight: 0.8 },
    { id: 'e4', source: 'img_beach_sunset', target: 'concept_water', type: 'image_concept', weight: 0.75 },
    { id: 'e5', source: 'img_beach_sunset', target: 'concept_sunset', type: 'image_concept', weight: 0.95 },
    { id: 'e6', source: 'img_beach_sunset', target: 'concept_nature', type: 'image_concept', weight: 0.7 },
    { id: 'e7', source: 'img_forest_path', target: 'concept_trees', type: 'image_concept', weight: 0.9 },
    { id: 'e8', source: 'img_forest_path', target: 'concept_nature', type: 'image_concept', weight: 0.85 },
    { id: 'e9', source: 'img_city_night', target: 'concept_urban', type: 'image_concept', weight: 0.9 },
    { id: 'e10', source: 'concept_nature', target: 'concept_trees', type: 'concept_concept', weight: 2.5 },
    { id: 'e11', source: 'concept_nature', target: 'concept_water', type: 'concept_concept', weight: 2.0 },
    { id: 'e12', source: 'concept_nature', target: 'concept_mountains', type: 'concept_concept', weight: 1.5 },
    { id: 'e13', source: 'img_mountain_lake', target: 'img_beach_sunset', type: 'image_image', similarity: 0.72 },
    { id: 'e14', source: 'img_mountain_lake', target: 'img_forest_path', type: 'image_image', similarity: 0.65 }
  ]
}
