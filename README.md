# Structure-from-Motion (SfM) Algorithm

Welcome to the Structure-from-Motion (SfM) Algorithm repository! This project implements a comprehensive SfM pipeline to reconstruct 3D structures from a set of 2D images. The implementation leverages OpenCV and Open3D for feature extraction, matching, and 3D reconstruction.

## Features

- **Camera Calibration**: gets the intrinsic parameters of a camera.
- **Feature Extraction**: Supports SIFT feature detectors.
- **Feature Matching**: Efficiently matches features between image pairs.
- **Pose Estimation**: Computes camera poses using baseline and Perspective-n-Point (PnP) methods.
- **Triangulation**: Reconstructs 3D points from matched features.
- **Mesh Generation**: Creates a 3D mesh from reconstructed points.
- **Visualization**: Visualizes the 3D points and meshes using Open3D.

## Installation

To get started, follow these steps:

### Clone the Repository

```bash
git clone https://github.com/rotellini9809/computer_vision_project

cd computer_vision_project
```

To install the necessary dependencies, use the following command:

```bash
pip install -r requirements.txt
```

## Usage

- To run the SfM algorithm on a dataset, use the `main.py` script. Ensure your dataset follows the structure shown below and contains a camera intrinsic matrix file `K.txt` in the `images` directory.
- To get the camera intrinsic parameters add the image of a checkboard in the folder `Scacchiera` and run the `cameracalibration.py` script

### Dataset Structure

```kotlin
data/
├── fountain-P11/
│   ├── images/
│   │   ├── image1.jpg
│   │   ├── image2.jpg
│   │   ├── ...
│   │   ├── K.txt
```

### Running the Algorithm
Run the main script with the following command:

``` bash
python main.py
```

The script will:

Create views from the images.
Compute feature matches between the views.
Estimate camera poses and reconstruct 3D points.
Generate and visualize the 3D mesh.

### files Overview
- **SFM**: Main class for the SfM reconstruction loop.
- **View**: Represents an individual image used in the reconstruction.
- **Match**: Represents feature matches between two views.
- **Utils**: varius functions that are used in the other files
- **Cameracalibration**: Script used to get intrinsic parameters of a camera

### Main Script (main.py)
``` python
Copia codice
from view import *
from match import *
from sfm import *
import numpy as np
import logging
import argparse

def run(root_dir, image_format):
    logging.basicConfig(level=logging.INFO)
    views = create_views(root_dir, image_format)
    matches = create_matches(views)
    K = np.loadtxt(os.path.join(root_dir, 'images', 'K.txt'))
    sfm = SFM(views, matches, K)
    sfm.reconstruct()
    sfm.write_mesh()
    sfm.visualize_points_and_mesh(root_dir)

if __name__ == '__main__':
    run('data/fountain-P11', 'jpg')
```

### Function Descriptions
- **create_views(root_path, image_format)**: Creates and returns a list of View objects from the images in the specified directory.
- **create_matches(views)**: Computes and returns a dictionary of Match objects between every possible pair of views.
- **SFM.reconstruct()**: Runs the main reconstruction loop.
- **SFM.write_mesh()**: Writes the reconstructed mesh to an OBJ file.
- **SFM.visualize_points_and_mesh(root_dir)**: Visualizes the 3D points and mesh.
