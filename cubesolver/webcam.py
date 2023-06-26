#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Simple wrapper to open a webcam stream with opencv
"""
import time
import cv2 as cv
import numpy as np
from skimage.transform import downscale_local_mean


class Webcam:
    """
        Class to read from a video stream (camera or video file)

        Args:
            port (int or string): Video port or file to open
            settings (dict or string)): Camera settings
            downscale (float): downscaling factor for streamed images
    """

    def __init__(self, port=0, settings=None, downscale=1):
        super(Webcam, self).__init__()
        self.matrix = None
        self.opened = False

        self.port = port
        self.scale = (downscale,)*2 + (1,)

         # FIXME: this is unused
        self.settings = settings
        if settings is None:
            self.settings = {'frame_width': 2048, 'frame_height': 1536,
                        'exposure': -4, 'gain': 0}

        self.open()

    def open(self):
        if self.opened:
            return

        # Open the device at location 'port'
        print('Try to open camera...')
        self.cap = cv.VideoCapture(self.port)

        # Check whether user selected video stream opened successfully.
        if not (self.cap.isOpened()):
            raise IOError("Could not open camera at port {}".format(self.port))
        print('Camera opened successfully')
        self.opened = True

    def get_frame(self):
        """ Get next frame (image) from stream
        """
        if not self.opened:
            self.open()

        ret, frame = self.cap.read()
        frame = np.round(downscale_local_mean(frame, self.scale)).astype('uint8')
        return ret, frame

    def close(self):
        """ Close connection to video stream
        """
        self.opened = False
        self.cap.release()
        cv.destroyAllWindows()

    def calibrate(self, chessboard=(7,6), width_mm=30):
        nrows, ncols = chessboard

        # termination criteria
        criteria = (cv.TERM_CRITERIA_EPS + cv.TERM_CRITERIA_MAX_ITER, 30, 0.01)

        # prepare object points, like (0,0,0), (1,0,0), (2,0,0) ....,(6,5,0)
        objp = np.zeros((nrows*ncols,3), np.float32)
        objp[:,:2] = np.mgrid[0:nrows,0:ncols].T.reshape(-1,2)

        # Arrays to store object points and image points from all the images.
        objpoints = [] # 3d point in real world space
        imgpoints = [] # 2d points in image plane.

        done = False

        self.open()
        # TODO: add max number of attempts
        while not done:
            ret, img = self.get_frame()

            gray = cv.cvtColor(img, cv.COLOR_BGR2GRAY)
            cv.imshow('img', gray)
            cv.waitKey(1000)

            # Find the chess board corners
            ret, corners = cv.findChessboardCorners(gray, chessboard, None)

            # If found, add object points, image points (after refining them)
            if ret == True:
                objpoints.append(objp)
                corners2 = cv.cornerSubPix(gray, corners, (11,11), (-1,-1), criteria)
                imgpoints.append(corners2)

                # Draw and display the corners
                cv.drawChessboardCorners(img, chessboard, corners2, ret)
                cv.imshow('img', img)
                cv.waitKey(500)

                done = True

            else:
                print("failed to find chessboard")
        self.close()

        ret, mtx, dist, rvecs, tvecs = cv.calibrateCamera(objpoints, imgpoints, gray.shape[::-1], None, None)
        if not ret:
            print("failed to calibrate camera")
            return False

        w, h = img.shape[:2]
        self.matrix, roi = cv.getOptimalNewCameraMatrix(mtx, dist, (w,h), 1, (w,h))
        return True


if __name__ == '__main__':
    from time import time

    camera = Webcam(0, downscale=1, settings=None)
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
                            cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255))
        f = cv.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        cv.imshow('Image', frame)

        t2 = time()
        fps = alpha*fps + (1-alpha)/(t2-t)
        t = t2
        if (t - t1) > fps_refresh_interval:
            t1 = time()
            disp_fps = fps
    camera.close()
    print('Closed camera')
