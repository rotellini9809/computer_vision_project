import cv2

# Lista delle immagini da caricare
image_paths = [r'C:\Users\casa\Desktop\camera_calibration prova\1.jpg', 
               r'C:\Users\casa\Desktop\camera_calibration prova\2.jpg',
               r'C:\Users\casa\Desktop\camera_calibration prova\3.jpg']


# Inizializza una lista per memorizzare i keypoints e i descrittori di ogni immagine
keypoints_list = []
descriptors_list = []

# Inizializza il detector SIFT
sift = cv2.SIFT_create()

# Rileva le feature e i descrittori per ciascuna immagine
for path in image_paths:
    # Carica l'immagine
    image = cv2.imread(path)
    # Converti l'immagine in scala di grigi
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    # Rileva i keypoints e i descrittori
    keypoints, descriptors = sift.detectAndCompute(gray, None)
    # Aggiungi i keypoints e i descrittori alla lista
    keypoints_list.append(keypoints)
    descriptors_list.append(descriptors)

# Inizializza il matcher per la ricerca delle corrispondenze
matcher = cv2.BFMatcher()

# Trova le corrispondenze tra i descrittori delle feature di tutte le immagini
matches_list = []
for i in range(len(descriptors_list) - 1):
    matches = matcher.match(descriptors_list[i], descriptors_list[i + 1])
    matches_list.append(matches)

# Filtra le corrispondenze utilizzando il nearest neighbor ratio (NNR)

# Disegna le corrispondenze sulle immagini

matched_images = []
for i in range(len(matches_list)):
    matched_image = cv2.drawMatches(cv2.imread(image_paths[i]), keypoints_list[i], 
                                    cv2.imread(image_paths[i + 1]), keypoints_list[i + 1], 
                                    matches_list[i], None)
    matched_images.append(matched_image)


# Disegna i keypoints su ogni immagine
images_with_keypoints = []
for i in range(len(image_paths)):
    image_with_keypoints = cv2.drawKeypoints(cv2.imread(image_paths[i]), keypoints_list[i], None)
    cv2.namedWindow("Image {} with Keypoints".format(i + 1), cv2.WINDOW_NORMAL)     
    images_with_keypoints.append(image_with_keypoints)

# Mostra tutte le immagini con i keypoints e le corrispondenze evidenziate
for i in range(len(images_with_keypoints)):
    cv2.imshow("Image {} with Keypoints".format(i + 1), images_with_keypoints[i])
for i in range(len(matched_images)):
     cv2.namedWindow("Matched Image {}".format(i + 1), cv2.WINDOW_NORMAL) 
     cv2.imshow("Matched Image {}".format(i + 1), matched_images[i])

cv2.waitKey(0)
cv2.destroyAllWindows()
