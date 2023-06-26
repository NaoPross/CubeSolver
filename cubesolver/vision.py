import skimage
import cv2 as cv
import numpy as np

def process(frame):
    # Change to grayscale
    frame_gray = skimage.color.rgb2gray(frame)
    frame_gray_eq = skimage.exposure.equalize_adapthist(frame_gray)

    # Get edges and do morphology
    edges = skimage.feature.canny(frame_gray, 2)
    footprint = skimage.morphology.disk(7)
    edges_m = skimage.morphology.closing(edges, footprint)
    edges_m = skimage.morphology.remove_small_holes(edges_m, 150)

    # Find contours
    contours = skimage.measure.find_contours(edges_m, fully_connected="high")

    # Compute centroids
    centroids = []
    for contour in contours:
        c = np.mean(contour, axis=0, dtype=np.int32)
        centroids.append(c)
        
    # centroids = np.vstack(centroids)
    # distances = scipy.spatial.distance.squareform(scipy.spatial.distance.pdist(centroids))
    # orthos = np.matmul(centroids, centroids.T) / (np.linalg.norm(centroids) ** 2)

    for c in centroids:
        rr, cc = skimage.draw.disk(c, 5, shape=frame.shape)
        frame[rr, cc] = (0, 0, 255)

    return frame

if __name__ == '__main__':
    from time import time
    from .webcam import Webcam

    camera = Webcam(0, downscale=3, settings=None)
    alpha = 0.9
    fps = 15
    disp_fps = 15
    t1 = 0
    fps_refresh_interval = 0.5

    while 1:
        t = time()
        ret, frame = camera.get_frame()

        key = cv.waitKey(1) & 0xFF
        if key == ord('q') or key == 27:
            break

        frame = cv.putText(frame, f'{disp_fps:.1f} FPS', (20, 450),
                            cv.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255))
        frame = cv.cvtColor(frame, cv.COLOR_BGR2RGB)
        frame = process(frame)
        frame = cv.cvtColor(frame, cv.COLOR_RGB2BGR)

        cv.imshow('Image', frame)

        t2 = time()
        fps = alpha*fps + (1-alpha)/(t2-t)
        t = t2
        if (t - t1) > fps_refresh_interval:
            t1 = time()
            disp_fps = fps
    camera.close()
    print('Closed camera')