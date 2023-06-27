import skimage
import scipy
import cv2 as cv
import numpy as np


def morphology(frame):
    # Change to grayscale
    frame_gray = skimage.color.rgb2gray(frame)
    frame_gray_eq = skimage.exposure.equalize_adapthist(frame_gray)

    # Get edges
    edges = skimage.feature.canny(frame_gray_eq, 1)

    # Process edges
    footprint = skimage.morphology.diamond(2)
    cubies = skimage.morphology.dilation(edges, footprint)
    cubies = skimage.util.invert(cubies)

    cubies = skimage.morphology.remove_small_objects(cubies, 200)
    cubies = skimage.segmentation.clear_border(cubies)

    # Find cubie looking regions
    cubie_labels, _ = scipy.ndimage.label(cubies, np.ones((3,3)))
    regions = []
    for region in skimage.measure.regionprops(cubie_labels):
        # Filter out big ares
        if region.area <= 2500 and region.extent > .5:
            minr, minc, maxr, maxc = region.bbox
            aratio = (maxr - minr) / (maxc - minc)
            # Take only square looking ones
            if np.abs(aratio - 1) < .3:
                regions.append(region)

    if not regions:
        return None

    # Create and apply mask
    cube = np.any(np.stack([cubie_labels == r.label for r in regions], axis=2), axis=2)

    footprint = skimage.morphology.disk(10)
    mask = skimage.morphology.closing(cube, footprint)

    mask_labels, mask_nlabels = scipy.ndimage.label(mask)
    area = lambda labels, l: np.sum(labels == l)
    biggest = np.max([area(mask_labels, l) for l in range(1, mask_nlabels + 1)])

    if biggest < 2000:
        return None

    mask = skimage.morphology.remove_small_objects(mask, biggest-1)
    cube = np.logical_and(cube, mask)

    return cube


def find_plane_ransac(centroids, camera_inv):
    # probability of getting the best
    p = .9999
    ncentroids = centroids.shape[0]

    if ncentroids <= 9:
        nruns = 10
    else:
        u = 9 / ncentroids  # FIXME: this is not very accurate
        nruns = int(np.log(1. - p) / np.log(1. - u ** 3)) + 1

    planes, errors = [], []
    for _ in range(nruns):
        # Get random samples
        idxs = np.random.choice(centroids.shape[0], size=3, replace=False)
        sample = centroids[idxs, :]
        
        # Unproject points in 3d space
        points = np.vstack([sample[:, 0], sample[:, 1], np.ones((1, sample.shape[0]))]).T
        points = points @ camera_inv

        # Perform a regression to find plane
        z = points[:, 2]
        a = np.linalg.pinv(points.T @ points) @ points.T @ z

        normal = np.array((a[0], a[1], -1)) / a[2]
        normal = normal / np.linalg.norm(normal)

        # Compute regression error
        err = np.sum(np.abs(points @ normal))
        
        # Save data
        planes.append(a)
        errors.append(err)
        
    planes = np.array(planes)
    best = planes[np.argmin(errors)]

    return best


def process(frame, cam):
    binary = morphology(frame)
    if binary is None:
        return frame

    # Draw found cube faces
    contours = skimage.measure.find_contours(binary)
    frame[binary] = (255, 0, 255)

    # Find contours and plane
    contours = skimage.measure.find_contours(cube)
    centroids = np.array([np.mean(c, axis=0) for c in contours])
    plane = find_plane_ransac(centroids, cam.inv_matrix)

    # Draw plane
    projected_centroids = centroids @ camera.matrix.T

    return frame


if __name__ == '__main__':
    from time import time
    from .webcam import Webcam

    camera = Webcam(0, downscale=3, settings=None)
    camera.calibrate((6,5))

    alpha = 0.9
    fps = 15
    disp_fps = 15
    t1 = 0
    fps_refresh_interval = 0.5

    # font = cv.freetype.createFreeType2()
    # font.loadFontData(fontFileName='unscii.ttf', id=0)

    while 1:
        t = time()
        ret, frame = camera.get_frame()

        key = cv.waitKey(1) & 0xFF
        if key == ord('q') or key == 27:
            break

        frame = cv.cvtColor(frame, cv.COLOR_BGR2RGB)
        frame = process(frame, cam)
        frame = cv.cvtColor(frame, cv.COLOR_RGB2BGR)
        # frame = font.putText(img=frame, text=f'{disp_fps:.1f} FPS', org=(20, 120),
        #             fontHeight=16, thickness=-1, line_type=cv.LINE_AA,
        #             color=(0, 0, 255), bottomLeftOrigin=True)

        frame = cv.putText(frame, f'{disp_fps:.1f} FPS', org=(20, 50),
                            fontScale=1, fontFace=cv.FONT_HERSHEY_SIMPLEX, 
                            thickness=2, color=(0, 0, 0))

        cv.imshow('Image', frame)

        t2 = time()
        fps = alpha*fps + (1-alpha)/(t2-t)
        t = t2
        if (t - t1) > fps_refresh_interval:
            t1 = time()
            disp_fps = fps

    camera.close()
    print('Closed camera')