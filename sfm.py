import os
from utils import *
import open3d as o3d
from baseline import Baseline

class SFM:
    """Represents the main reconstruction loop"""
    def __init__(self, views, matches, K):
        self.colors_3D = np.zeros((0,3))
        self.views = views  # list of views
        self.matches = matches  # dictionary of matches
        self.names = []  # image names
        self.done = []  # list of views that have been reconstructed
        self.K = K  # intrinsic matrix
        self.points_3D = np.zeros((0, 3))  # reconstructed 3D points
        self.point_counter = 0  # keeps track of the reconstructed points
        self.point_map = {}  # a dictionary of the 2D points that contributed to a given 3D point
        self.errors = []  # list of mean reprojection errors taken at the end of every new view being added

        for view in self.views:
            self.names.append(view.name)

        if not os.path.exists(self.views[0].root_path + '/points'):
            os.makedirs(self.views[0].root_path + '/points')

        # store results in a root_path/points
        self.results_path = os.path.join(self.views[0].root_path, 'points')

    def get_index_of_view(self, view):
        """Extracts the position of a view in the list of views"""
        return self.names.index(view.name)

    def remove_mapped_points(self, match_object, image_idx):
        """Removes points that have already been reconstructed in the completed views"""
        inliers1 = []
        inliers2 = []

        for i in range(len(match_object.inliers1)):
            if (image_idx, match_object.inliers1[i]) not in self.point_map:
                inliers1.append(match_object.inliers1[i])
                inliers2.append(match_object.inliers2[i])

        match_object.inliers1 = inliers1
        match_object.inliers2 = inliers2

    def compute_pose(self, view1, view2=None, is_baseline=False):
        """Computes the pose of the new view"""
        # procedure for baseline pose estimation
        if is_baseline and view2:

            match_object = self.matches[(view1.name, view2.name)]
            baseline_pose = Baseline(view1, view2, match_object)
            view2.R, view2.t = baseline_pose.get_pose(self.K)

            rpe1, rpe2 = self.triangulate(view1, view2)
            self.errors.append(np.mean(rpe1))
            self.errors.append(np.mean(rpe2))

            self.done.append(view1)
            self.done.append(view2)

        # procedure for estimating the pose of all other views
        else:

            view1.R, view1.t = self.compute_pose_PNP(view1)
            errors = []

            # reconstruct unreconstructed points from all of the previous views
            for i, old_view in enumerate(self.done):

                match_object = self.matches[(old_view.name, view1.name)]
                _ = remove_outliers_using_F(old_view, view1, match_object)
                self.remove_mapped_points(match_object, i)
                _, rpe = self.triangulate(old_view, view1)
                if rpe:
                    errors += rpe

            self.done.append(view1)
            self.errors.append(np.mean(errors))


    def triangulate(self, view1, view2):
        """Triangulates 3D points from two views whose poses have been recovered. Also updates the point_map dictionary"""
        K_inv = np.linalg.inv(self.K)
        P1 = np.hstack((view1.R, view1.t))
        P2 = np.hstack((view2.R, view2.t))

        match_object = self.matches[(view1.name, view2.name)]
        pixel_points1, pixel_points2 = get_keypoints_from_indices(keypoints1=view1.keypoints,
                                                                  keypoints2=view2.keypoints,
                                                                  index_list1=match_object.inliers1,
                                                                  index_list2=match_object.inliers2)
        if len(pixel_points1) == 0 or len(pixel_points2)==0:
            return None, None
        pixel_points1 = cv2.convertPointsToHomogeneous(pixel_points1)[:, 0, :]
        pixel_points2 = cv2.convertPointsToHomogeneous(pixel_points2)[:, 0, :]
        reprojection_error1 = []
        reprojection_error2 = []

        '''
        cv2.imshow("fratm",cv2.resize(view1.gaussian_image, (1024, 1024)))
                
        # Wait for a key press and close the window
        cv2.waitKey(0)
        cv2.destroyAllWindows()
        '''

        for i in range(len(pixel_points1)):
            #print("pixel_point: ", pixel_points1)
            u1 = pixel_points1[i, :]
            u2 = pixel_points2[i, :]

            u1_normalized = K_inv.dot(u1)
            u2_normalized = K_inv.dot(u2)

            point_3D = get_3D_point(u1_normalized, P1, u2_normalized, P2)
            self.points_3D = np.concatenate((self.points_3D, point_3D.T), axis=0)   

            color1 = view1.gaussian_image[int(u1[1]), int(u1[0]), :]  # Assumendo che view1.image sia l'immagine
            color2 = view2.gaussian_image[int(u2[1]), int(u2[0]), :]  # Assumendo che view2.image sia l'immagine
            color_bgr = (color1 + color2) / 2  # Media dei colori dei due punti in BGR

            # Converti da BGR a RGB
            color_rgb = cv2.cvtColor(np.uint8([[color_bgr]]), cv2.COLOR_BGR2RGB)[0, 0]

            self.colors_3D = np.concatenate((self.colors_3D, [color_rgb]), axis=0)
            error1 = calculate_reprojection_error(point_3D, u1[0:2], self.K, view1.R, view1.t)
            reprojection_error1.append(error1)
            error2 = calculate_reprojection_error(point_3D, u2[0:2], self.K, view2.R, view2.t)
            reprojection_error2.append(error2)

            # updates point_map with the key (index of view, index of point in the view) and value point_counter
            # multiple keys can have the same value because a 3D point is reconstructed using 2 points
            self.point_map[(self.get_index_of_view(view1), match_object.inliers1[i])] = self.point_counter
            self.point_map[(self.get_index_of_view(view2), match_object.inliers2[i])] = self.point_counter
            self.point_counter += 1
        return reprojection_error1, reprojection_error2

    def compute_pose_PNP(self, view):
        """Computes pose of new view using perspective n-point"""
        matcher = cv2.BFMatcher(cv2.NORM_L2, crossCheck=False)

        # collects all the descriptors of the reconstructed views
        old_descriptors = []
        for old_view in self.done:
            old_descriptors.append(old_view.descriptors)

        # match old descriptors against the descriptors in the new view
        matcher.add(old_descriptors)
        matcher.train()
        matches = matcher.match(queryDescriptors=view.descriptors)
        points_3D, points_2D = np.zeros((0, 3)), np.zeros((0, 2))

        # build corresponding array of 2D points and 3D points
        for match in matches:
            old_image_idx, new_image_kp_idx, old_image_kp_idx = match.imgIdx, match.queryIdx, match.trainIdx

            if (old_image_idx, old_image_kp_idx) in self.point_map:

                # obtain the 2D point from match
                point_2D = np.array(view.keypoints[new_image_kp_idx].pt).T.reshape((1, 2))
                points_2D = np.concatenate((points_2D, point_2D), axis=0)

                # obtain the 3D point from the point_map
                point_3D = self.points_3D[self.point_map[(old_image_idx, old_image_kp_idx)], :].T.reshape((1, 3))
                points_3D = np.concatenate((points_3D, point_3D), axis=0)

        # compute new pose using solvePnPRansac
        _, R, t, _ = cv2.solvePnPRansac(points_3D[:, np.newaxis], points_2D[:, np.newaxis], self.K, None,
                                        confidence=0.99, reprojectionError=8.0, flags=cv2.SOLVEPNP_DLS)
        R, _ = cv2.Rodrigues(R)
        return R, t

    def plot_points(self):
        """Saves the reconstructed 3D points to ply files using Open3D"""
        number = len(self.done)
        filename = os.path.join(self.results_path, str(number) + '_images.ply')
        pcd = o3d.geometry.PointCloud()
        pcd.points = o3d.utility.Vector3dVector(self.points_3D)

        if self.colors_3D.shape[0] > 0:
            pcd.colors=o3d.utility.Vector3dVector(self.colors_3D / 255.0)

        # Rimuovi i punti outliers utilizzando il filtro statistico
        cl, ind = pcd.remove_statistical_outlier(nb_neighbors=20, std_ratio=2.0)
        pcd = pcd.select_by_index(ind)

        o3d.io.write_point_cloud(filename, pcd)
        
    def write_mesh(self):
        filename = os.path.join(self.results_path, str(len(self.done)) + '_images.ply')
        pcd = o3d.io.read_point_cloud(filename)

        logging.info("creating mesh")
        # Stima delle normali
        pcd.estimate_normals()
        pcd.orient_normals_to_align_with_direction()

        # Creating a mesh from point cloud using Poisson Algorithm
        # mesh = o3d.geometry.TriangleMesh.create_from_point_cloud_poisson(pcd, depth=10, n_threads=1)[0]
        
        # Creating a mesh from point cloud using Alpha Shape
        mesh = o3d.geometry.TriangleMesh.create_from_point_cloud_alpha_shape(pcd, 0.1)
        
        # Creating mesh from point cloud using ball pivoting
        # distances = pcd.compute_nearest_neighbor_distance()
        # avg_dist = np.mean(distances)
        # radius = 3 * avg_dist
        # mesh = o3d.geometry.TriangleMesh.create_from_point_cloud_ball_pivoting(pcd, o3d.utility.DoubleVector([radius, radius * 2]))

        mesh = mesh.remove_unreferenced_vertices()
        mesh = mesh.remove_degenerate_triangles()
        mesh = mesh.remove_duplicated_triangles()
        mesh = mesh.remove_non_manifold_edges()
        
        # Ruota la mesh se necessario
        rotation = mesh.get_rotation_matrix_from_xyz((np.pi, 0, 0))
        mesh.rotate(rotation, center=(0, 0, 0))

        logging.info("writing mesh")
        o3d.io.write_triangle_mesh(os.path.join(self.results_path,"mesh.obj"),mesh)

    def visualize_points_and_mesh(self,root_dir):
        filename_pcd = os.path.join(self.results_path, str(count_files_in_directory(root_dir+"/images")-1) + '_images.ply')
        filename_mesh = os.path.join(self.results_path,"mesh.obj")

        pcd = o3d.io.read_point_cloud(filename_pcd)
        mesh = o3d.io.read_triangle_mesh(filename_mesh)

        # Visualizzation
        o3d.visualization.draw_geometries([pcd], window_name="Point Cloud Visualization")

        # Visualize the mesh.
        o3d.visualization.draw_geometries([mesh], window_name="Mesh Visualization", mesh_show_back_face=True)

    def reconstruct(self):
        """Starts the main reconstruction loop for a given set of views and matches"""
        # compute baseline pose
        baseline_view1, baseline_view2 = self.views[0], self.views[1]
        logging.info("Computing baseline pose and reconstructing points")
        self.compute_pose(view1=baseline_view1, view2=baseline_view2, is_baseline=True)
        logging.info("Mean reprojection error for 1 image is %f", self.errors[0])
        logging.info("Mean reprojection error for 2 images is %f", self.errors[1])
        self.plot_points()
        logging.info("Points plotted for %d views", len(self.done))

        for i in range(2, len(self.views)):

            logging.info("Computing pose and reconstructing points for view %d", i+1)
            self.compute_pose(view1=self.views[i])
            logging.info("Mean reprojection error for %d images is %f", i+1, self.errors[i])
            self.plot_points()
            logging.info("Points plotted for %d views", i+1)

def count_files_in_directory(directory_path):
    return len([name for name in os.listdir(directory_path) if os.path.isfile(os.path.join(directory_path, name))])