__author__ = 'oli'

#   A Demonstrator for showing the convolutional neural network
#   Further a web-cam can be used
#
# Taken from the piVision Projekt
#

import cv2
from convolutional_mlp_face import LeNet5State, LeNet5Topology
import LeNetPredictor as LeNetPredictor
import numpy as np
import time as time
import os as os
import Sources
from PIL import Image as Image
import Preprocessing
import csv

# Parameters
scale_fac = 0.2
borderProb = 0.85
show = True
createOverviewFigs = True
webcam = True
rocWriter = csv.writer(open('roc.csv', 'w'))


class FaceDetectorAll:

    def __init__(self, show = False):
        self.show = show
        self.faces = 0.0
        print('Trying to load face detector')
        self.face_cascade = cv2.CascadeClassifier()
        stat = self.face_cascade.load('models/haarcascade_frontalface_alt.xml')
        if (stat == False):
            print('Could not load the face detector')
        else:
            print('Loaded the face detector')
        #self.pred = LeNetPredictor.LeNetPredictor(stateIn='models/state_lbh_elip_K100_batch3', deepOut=True)
        #self.pred = LeNetPredictor.LeNetPredictor(stateIn='models/state_lbh_elip_K100_batch3_long_training', deepOut=True)
        #self.pred = LeNetPredictor.LeNetPredictor(stateIn='models/good_ones/state_lbh_elip_K100_batch3___Hat__Nur__2__Error_wenn_Ueber_90Prozent', deepOut=True)
        #self.pred = LeNetPredictor.LeNetPredictor(stateIn='models/good_ones/k20.p', deepOut=True)
        self.pred = LeNetPredictor.LeNetPredictor(stateIn='models/good_ones/paper21.gz', deepOut=True)

        #self.pred = LeNetPredictor.LeNetPredictor(stateIn='models/good_ones/k100_lr0.1_speckel.p', deepOut=True)
        self.ok = 0
        self.all = 1e-16
        self.wrong = 0
        print("Loaded the face predictor")

    # simply scale the image by a given factor
    def scale_image(self, image, scale_factor=scale_fac):
        if image is not None:
            new_size =  ( int(image.shape[1] * scale_factor), int(image.shape[0] * scale_factor) )
            return cv2.resize(image, new_size)
        else:
            return None

    def getFaces(self, image, scale_factor = scale_fac):
        if image is None:
            return None

        # if it is a color image - convert to grayscale for faster detection
        if len(image.shape)>2 :
            image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

        scaled_image = self.scale_image(image, scale_factor)
        faces_scaled = self.face_cascade.detectMultiScale(scaled_image)
        faces = None
        if faces_scaled is not None and len(faces_scaled)>0:
            faces = faces_scaled / scale_factor
            faces = faces.astype(int)
            pass

        return faces

    def preprocess(self, img_face):
        Size_For_Eye_Detection = (48, 48)
        img_face = cv2.resize(img_face, Size_For_Eye_Detection, Image.ANTIALIAS)
        img_norm = Preprocessing.LBH_Norm(img_face)
     #   img_norm = Preprocessing.mask_on_rect(img_norm)
        return img_norm, img_face

    def processImage(self, img, y=None, writer = None):
        img_org = img.copy()
        img = np.asarray(img)
        img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY) #Gray Scaled
        t_start_viola = time.time()
        face_list = fd.getFaces(img)
        time_viola_jones = time.time() - t_start_viola
        if self.show:
            import matplotlib.pyplot as plt
            plt.ion()
            fig = plt.figure("Hello Convolutional Networks", figsize=(18, 12))
        if face_list is not None and len(face_list)>0:
            self.faces += 1
            t_start = time.time()
            x_0, y_0, w, h = face_list[0]   # assume there is exactly one face
            x_1 = (x_0 + w)
            y_1 = (y_0 + h)
            img_face = img[y_0:y_1, x_0:x_1]

            X, img_face = self.preprocess(img_face)
            #X, img_face = self.preprocess2(img_face)
            #X = self.mask(X)

            if writer is not None:
                d = np.append(y, X.reshape(-1))
                writer.writerow(d)

            X = X / 255.

            #res = self.pred.getPrediction(X)
            res = self.pred.getPrediction(np.array(X, dtype=np.float32))
            time_cnn = time.time() - t_start

            pos = np.arange(6)+.5
            names = ('Dejan', 'Diego', 'Martin', 'Oliver', 'Rebekka', 'Ruedi')
            predY = int(res.argmax())
            predName   = str(names[predY])
            predPValue = res[0][predY]
            frame_width = 1
            wrong = False
            frame_col = (128,128,128)
            if y is not None:
                if y == predY:
                    if (predPValue > borderProb):
                        self.ok += 1
                    frame_col = (0,255,0)
                else:
                    frame_col = (128,0,0)
                    if (predPValue > borderProb):
                        frame_col = (255,0,0)
                        self.wrong += 1
                        print("Wrong")
                        wrong = True
            rocWriter.writerow((y, predY, predPValue))
            if (predPValue > borderProb):
                self.all += 1
                frame_width = 6
            if y is None:
                name = "Unknown"
            else:
                name = names[y]

            print("0.4242,%06.2f"%(time_viola_jones * 1000)  + ",%06.2f"%(time_cnn * 1000) + "\n")

            print(str(predName) + " (predicted): Time for detection (Viola & Jones) : " +  "%06.2f msec "%(time_viola_jones * 1000)  +
                  " Time for the classific. & prepros. (CNN) : " + "%06.2f msec "%(time_cnn * 1000) + " overall acc. " + str(float(self.ok) / self.all) + " wrong " + str(self.wrong))

            if self.show:
                plt.clf()
                ############## Stats
                #fig.text(0.02, 1.00, "Hello Convolutional Network" , fontsize=14, verticalalignment='top')
                fig.text(0.02, 1.00, "Total " + str(int(self.faces)) + " Called " +  str(int(self.all)) + " Right " + str(self.ok) + " Wrong " + str(self.wrong) + " Acc. " + str(round(1.0 * self.ok / self.all, 4))
                         , fontsize=18, verticalalignment='top')
                fig.text(0.02, 0.97, "Time for detection (Viola & Jones)    : " +  "%06.2f"%(time_viola_jones * 1000) + " msec" ,fontsize=12, verticalalignment='top')
                fig.text(0.02, 0.95, "Time for classific. & prepros. (CNN)  : " +  "%06.2f"%(time_cnn * 1000) + " msec" ,fontsize=12, verticalalignment='top')

                ############## Original Image with Box drawn
                plt.subplot(421)
                plt.title('Original Image : ' + str(img_org.shape))
                frame_col = (0,255,0)
                frame_width = 6
                cv2.rectangle(img_org,(x_0,y_0),(x_0+h,y_0+h), frame_col,frame_width)
                #cv2.putText(img_org,str(predName + " (" + str(round(predPValue,3)) + ")") ,(x_0,y_0+h), cv2.FONT_HERSHEY_SIMPLEX, 1, frame_col, 2)
                plt.imshow(img_org)

                ############## Logistic Regression
                plt.subplot(422)
                plt.yticks(pos, names)
                plt.barh(pos, np.asarray(res[0], dtype = float), align='center')
                plt.title("Final Layer (Multinomial Regression) " + predName + " " + str(round(predPValue,2)))

                plt.subplots_adjust(hspace = 0.3)
                ############## Faces
                plt.subplot(423)
                face = plt.imshow(img_face)
                plt.title("Detected Face " + str(img_face.shape))
                face.set_cmap('gray')

                plt.subplot(424)
                dd = plt.imshow(X)
                plt.title("Preprocessed Face " + str(X.shape))
                dd.set_cmap('gray')

                # Kernels of Layer 0
                #plt.subplot(425)
                plt.subplot2grid((4,2),(2,0), colspan=2)
                #d = self.pred.getPool0Out(X)
                #d = self.pred.getConv0Out(X)
                #plt.title('Result after first max-pooling layer ' + str(d.shape))
                #maxPool0 = d[0]
                # nkerns0 = maxPool0.shape[0]
                # s0 = maxPool0.shape[1]
                # ddd = plt.imshow(np.reshape(maxPool0, (s0, s0 * nkerns0)),interpolation="nearest")
                # ddd.set_cmap('gray')
                #
                # # Kernels of Layer 1
                # plt.subplot2grid((4,2),(3,0), colspan=2)
                # d = self.pred.getPool1Out(X)
                # maxPool1 = d[0]
                # nkerns1 = maxPool1.shape[0]
                # s1 = maxPool1.shape[1]
                # nkerns1 = min(nkerns1, 100)
                # plt.title('Result after second max-pooling layer. ' + str(d.shape))
                # dddd = plt.imshow(np.reshape(maxPool1[0:nkerns1], (s1, nkerns1 * s1)),interpolation="nearest")
                # dddd.set_cmap('gray')
                # plt.draw()

                # Creation of the Overviewfigure
                if createOverviewFigs:
                    plt.waitforbuttonpress()
                    fig.set_facecolor('white')
                    plt.clf()
                    plt.ioff()

                    # plt.subplot(341)
                    # d1 = plt.imshow(maxPool0[0],interpolation="nearest")
                    # d1.set_cmap('gray')
                    #
                    # plt.subplot(342)
                    # d2 = plt.imshow(maxPool1[0],interpolation="nearest")
                    # d2.set_cmap('gray')

                    plt.subplot(343)
                    d2 = plt.imshow(img_org,interpolation="nearest")

                    plt.subplot(3,4,10)
                    plt.yticks(pos, names)
                    d3 = plt.barh(pos, np.asarray(res[0], dtype = float), align='center')

                    plt.subplot(345)
                    d4 = plt.imshow(X,interpolation="nearest")
                    d4.set_cmap('gray')

                    plt.subplot(346)
                    d5 = plt.imshow(img_face,interpolation="nearest")
                    d5.set_cmap('gray')

                    plt.subplot(347)
                    dd = self.pred.getConv0Out(X)
                    d6 = plt.imshow(dd[0][0],interpolation="nearest")
                    d6.set_cmap('gray')

                    plt.subplot(348)
                    dd = self.pred.getConv1Out(X)
                    d7 = plt.imshow(dd[0][0],interpolation="nearest")
                    d7.set_cmap('gray')

                    plt.subplot(349)
                    dd = self.pred.w1
                    plt.title("w1")
                    d8 = plt.imshow(dd[0][0],interpolation="nearest")
                    d8.set_cmap('gray')


                    plt.subplot(3,4,4)
                    plt.title("w0")
                    dd = self.pred.w0
                    d9 = plt.imshow(dd[0][0],interpolation="nearest")
                    d9.set_cmap('gray')

                    plt.draw()
                    #plt.waitforbuttonpress()
                    from matplotlib.backends.backend_pdf import PdfPages

                    pp = PdfPages('/Users/oli/Proj_Large_Data/PiVision/pivision/trunk/EuroGraphics2015/Figures/stuffForFigure_rebekka.pdf')
                    pp.savefig(fig)

                    pp.close()


        print("Classified " + str(self.all) + " All " + " Acc " + str(round(1.0 * self.ok / self.all, 2)) + " Faces " + str(self.faces))
        #cv2.imshow('Original', img_org)
        #cv2.waitKey(1000000)


if __name__ == "__main__":
    print("Hallo Gallo")
    fd = FaceDetectorAll(show = show)
    if (webcam): #Using the webcam
        from utils import ImageCapturer
        cap = ImageCapturer.ImageCapturer()
        if not cap:
            print "Error opening capture device"
        else:
            print "successfully imported video capture"
        while True:
            rval, frame = cap.get_image()
            fd.processImage(frame)


    if (True):
        img_path = os.path.abspath('/Users/oli/Proj_Large_Data/PiVision/pivision/images/session_30_july_2014')
        [y, block, names, filenames] = Sources.read_images_2(img_path, useBatch=2, maxNum=1500)

        w = None
        #import csv
        #w = csv.writer(open("../../data/" + 'batch2_46_gamma_dog.csv', 'w'))
        d = "/Users/oli/Proj_Large_Data/PiVision/pivision/images/session_30_july_2014/Oliver_2/Oliver-2-41.png"
        d = "/Users/oli/Proj_Large_Data/PiVision/pivision/images/session_30_july_2014/Dejan_1/Dejan-1-1.png"
        d = "/Users/oli/Proj_Large_Data/PiVision/pivision/images/session_30_july_2014/Rebekka_2/Rebekka-2-3.png"
        d = "/Users/oli/Proj_Large_Data/PiVision/pivision/images/session_30_july_2014/Rebekka_2/Rebekka-2-31.png"
        d = "/Users/oli/Proj_Large_Data/PiVision/pivision/images/session_30_july_2014/Rebekka_2/Rebekka-2-5.png"

        fd.processImage(cv2.imread(d), 0, w)
        # cv2.imshow("Gallo ", img);
        # import matplotlib.pyplot as plt
        # plt.ion()
        # fig = plt.figure("Hello Convolutional World", figsize=(18, 12))
        # plt.imshow(img)
        # cv2.waitKey(1000000)


        # for (idx, file_name) in enumerate(filenames):
        #     img = cv2.imread(file_name)
        #     #if y[idx] == 3: #Only images from me
        #     print("\n Checking Filename " + str(file_name) + " y " + str(y[idx]) )
        #     fd.processImage(img, y[idx], w)
        #     print(len(filenames))


