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
    sfm.visualize_points_and_mesh()

    
def visualize_only(root_dir, image_format):
    logging.basicConfig(level=logging.INFO)
    views = create_views(root_dir, image_format)
    matches = create_matches(views)
    K = np.loadtxt(os.path.join(root_dir, 'images', 'K.txt'))
    sfm = SFM(views, matches, K)
    sfm.visualize_points_and_mesh()

if __name__ == '__main__':
    root_dir = 'data\fountain-P11'
    run(root_dir, 'jpg')
    #visualize_only(root_dir, 'jpg')
