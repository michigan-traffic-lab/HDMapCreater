# HDMapCreater

A streamlined pipeline for creating [Lanelet2](https://github.com/fzi-forschungszentrum-informatik/Lanelet2) HD map files from OpenStreetMap data. This tool supports the [Ann Arbor Near-miss Detection project] by enabling map creation for instrumented intersections, covering lane-level road geometry, traffic regulations, and crosswalk definitions.

The pipeline guides users through downloading OSM data, editing topological relationships, fine-tuning map elements, and verifying the final output — no prior HD map experience required.


## Installation

On an Ubuntu system (versions 20.04, 22.04, or 24.04 all work), install [Miniconda](https://www.anaconda.com/docs/getting-started/miniconda/install), then run the following commands:
```
conda create -n map python=3.10
conda activate map
pip install -r requirements.txt
```

## Procedures

The pipeline consists of four steps:
- [Download OSM Map](docs/download_osm_map.md)
- [Edit Topology](docs/edit_topology.md)
- [Fine-Tune Geometry](docs/fine_tune.md)
- [Verify Output](docs/verification.md)

The expected output folder structure is:

```
${map_folder_name}
├── background.png
├── configs.json
└── lanelet2.osm
```

## Contact

Tinghan Wang (tinghanw@umich.edu)
