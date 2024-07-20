from view import *
from match import *
from sfm import *
import numpy as np
import logging
import argparse


def run(root_dir,image_format):

    logging.basicConfig(level=logging.INFO)
    views = create_views(root_dir, image_format)
    matches = create_matches(views)
    K = np.loadtxt(os.path.join(root_dir, 'images', 'K.txt'))
    sfm = SFM(views, matches, K)
    sfm.reconstruct()
    sfm.write_mesh()
    sfm.visualize_points_and_mesh(root_dir)



if __name__ == '__main__':

    run('data/fountain-P11','jpg')
