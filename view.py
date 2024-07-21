import os
import sys
import pickle
import cv2
import numpy as np
import glob
import logging
import matplotlib as plt


class View:
    """Represents an image used in the reconstruction"""

    def __init__(self, image_path, root_path, feature_path):

        self.name = os.path.splitext(os.path.basename(image_path))[0]  # image name without extension
        self.image = cv2.imread(image_path)  # numpy array of the image
        self.gaussian_image = cv2.GaussianBlur(self.image, (15, 15), 0)
        self.keypoints = []  # list of keypoints obtained from feature extraction
        self.descriptors = []  # list of descriptors obtained from feature extraction
        self.root_path = root_path  # root directory containing the image folder
        self.R = np.zeros((3, 3), dtype=float)  # rotation matrix for the view
        self.t = np.zeros((3, 1), dtype=float)  # translation vector for the view

        if not feature_path:
            self.extract_features()
        else:
            self.read_features()

    def extract_features(self):
        """Extracts features from the image"""

        detector = cv2.SIFT_create()
        
        self.keypoints, self.descriptors = detector.detectAndCompute(self.image, None)
        logging.info("Computed features for image %s", self.name)

        self.write_features()

    def read_features(self):
        """Reads features stored in files. Feature files have filenames corresponding to image names without extensions"""

        # Logic to compute features for images that don't have pkl files
        try:
            features = pickle.load(open(os.path.join(self.root_path, 'features', self.name + '.pkl'), "rb"))
            logging.info("Read features from file for image %s", self.name)

            keypoints = []
            descriptors = []

            for point in features:
                keypoint = cv2.KeyPoint(x=point[0][0], y=point[0][1], size=point[1], angle=point[2],
                                        response=point[3], octave=point[4], class_id=point[5])
                descriptor = point[6]
                keypoints.append(keypoint)
                descriptors.append(descriptor)

            self.keypoints = keypoints
            self.descriptors = np.array(descriptors)  # convert descriptors into n x 128 numpy array

        except FileNotFoundError:
            logging.error("Pkl file not found for image %s. Computing from scratch", self.name)
            self.extract_features()

    def write_features(self):
        """Stores computed features to pkl files. The files are written inside a features directory inside the root directory"""

        if not os.path.exists(os.path.join(self.root_path, 'features')):
            os.makedirs(os.path.join(self.root_path, 'features'))

        temp_array = []
        for idx, point in enumerate(self.keypoints):
            temp = (point.pt, point.size, point.angle, point.response, point.octave, point.class_id,
                    self.descriptors[idx])
            temp_array.append(temp)

        features_file_path = os.path.join(self.root_path, 'features', self.name + '.pkl')
        with open(features_file_path, 'wb') as features_file:
            pickle.dump(temp_array, features_file)

        logging.info("Saved features to file for image %s", self.name)


def create_views(root_path, image_format='jpg'):
    """Loops through the images and creates an array of views"""

    feature_path = False

    # if features directory exists, the feature files are read from there
    logging.info("Created features directory")
    if os.path.exists(os.path.join(root_path, 'features')):
        feature_path = True

    image_names = sorted(glob.glob(os.path.join(root_path, 'images', '*.' + image_format)))

    logging.info("Computing features")
    views = []
    for image_name in image_names:
        views.append(View(image_name, root_path, feature_path=feature_path))

    return views
