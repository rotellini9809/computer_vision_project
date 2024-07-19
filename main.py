from view import *
from match import *
from sfm import *
import numpy as np
import logging


def run(root_dir, image_format):

    logging.basicConfig(level=logging.INFO)
    views = create_views(root_dir, image_format)
    matches = create_matches(views)
    K = np.loadtxt(os.path.join(root_dir, 'images', 'K.txt'))
    sfm = SFM(views, matches, K)
    sfm.reconstruct()
    sfm.visualize_points()

    


if __name__ == '__main__':
    run('data\fountain-P11\images', 'jpg')

