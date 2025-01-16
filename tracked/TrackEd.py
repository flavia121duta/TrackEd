'''
Author: Jamie McGrath

Designed to detect emotions from live video using a trained deep learning model. 
The class captures video frames from the web cam, detects faces using Haar cascade 
classifier, predicts the emotion of each detected face using a pre-trained Keras 
model, and saves images from the frame every 5 seconds, as well as the session 
stream to the corresponding folders. It also displays the emotion counts in 
real-time on the video frame.

Params:
~ 'model_weights.h5': 
    file path to the pre-trained Keras model weights.
~ 'haarcascade_frontalface_default.xml':
    file path to the Haar cascade classifier for face detection.
~ 'img_path':
    directory path images will be saved for each emotion label.
~ 'picture_interval':
    interval (in seconds) at which images will be captured and saved.
~ 'emotion_labels'':
    list of emotion labels used for detecting and counting emotions.
Output:
~ Video stream:
    Live video stream captured from the web camera and processed to detect 
        emotions.
~ Images:
    Images of detected faces with emotion labels, saved in corresponding 
        folders for each emotion label.
~ Video file:
    Session Stream saved in the session_stream directory, containing the 
        recorded stream.
~ Real-time emotion counts:
    Emotion counts displayed in real-time on the video frame.
'''

import cv2
import time
import numpy as np
from keras.models import load_model
import os
from pathlib import Path

class EmotionDetector:
    def __init__(self):
        # Load the best model
        self.model = load_model(Path('plots') / '1.Model' / 'model_weights.h5')

        # Initialise the camera
        self.cap = cv2.VideoCapture(0)
        self.timestamp = time.strftime("%d%b%Y_%H%M%S")

        # Get the size of the frames
        self.frame_width = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        self.frame_height = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

        # Create a VideoWriter object
        self.out = cv2.VideoWriter(f'session_stream/session_{self.timestamp}.mp4',
                                    cv2.VideoWriter_fourcc('M', 'P', '4', 'V'), 10,
                                    (self.frame_width, self.frame_height))

        # Initialise button positions and dimensions
        self.button1_pos = (20, 20)
        self.button1_dim = (60, 40)

        self.button2_pos = (100, 20)
        self.button2_dim = (60, 40)

        self.button1_pressed = False
        self.button2_pressed = False

    def check_button_click(self, pos, dim, mouse_pos):
        x, y = pos
        w, h = dim
        mx, my = mouse_pos
        if x <= mx <= x + w and y <= my <= y + h:
            return True
        return False

    def draw_buttons(self, frame):
        button1_color = (135, 206, 250) if self.button1_pressed else (70, 130, 180)
        button2_color = (135, 206, 250) if self.button2_pressed else (70, 130, 180)

        cv2.rectangle(frame, self.button1_pos, (self.button1_pos[0] + self.button1_dim[0],
                                                self.button1_pos[1] + self.button1_dim[1]), button1_color, -1)
        cv2.putText(frame, "Play", (self.button1_pos[0] + 10, self.button1_pos[1] + 30),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 2)

        cv2.rectangle(frame, self.button2_pos, (self.button2_pos[0] + self.button2_dim[0],
                                                self.button2_pos[1] + self.button2_dim[1]), button2_color, -1)
        cv2.putText(frame, "Quit", (self.button2_pos[0] + 10, self.button2_pos[1] + 30),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 2)

    def handle_mouse_events(self, event, x, y, flags, param):
        if event == cv2.EVENT_LBUTTONDOWN:
            if self.check_button_click(self.button1_pos, self.button1_dim, (x, y)):
                self.button1_pressed = not self.button1_pressed
            elif self.check_button_click(self.button2_pos, self.button2_dim, (x, y)):
                self.button2_pressed = not self.button2_pressed

    def run(self):
        # emotion labels
        self.emotion_labels = [
            'Angry',
            'Disgust',
            'Fear',
            'Happy',
            'Neutral',
            'Sad',
            'Surprise'
        ]

        # path to store images
        self.img_path = Path('emotion_class')
        self.last_picture_time = time.time()
        self.picture_interval = 5  # Take picture every 5 seconds

        # create directories for each emotion label if they don't exist
        for label in self.emotion_labels:
            dir_path = os.path.join(self.img_path, label.lower())
            os.makedirs(dir_path, exist_ok=True)

        # initialise counts for each emotion
        self.emotion_counts = {}
        for label in self.emotion_labels:
            self.emotion_counts[label] = 0

        cv2.namedWindow('Emotion Detector')
        cv2.setMouseCallback('Emotion Detector', self.handle_mouse_events)

        while True:
            # capture frame-by-frame
            ret, frame = self.cap.read()
            frame = cv2.flip(frame, 1)

            self.draw_buttons(frame)

            if self.button1_pressed:
                # detect face
                face_cascade = cv2.CascadeClassifier('haarcascade_frontalface_default.xml')
                gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                faces = face_cascade.detectMultiScale(gray, 1.3, 5)

                for (x, y, w, h) in faces:
                    # resize and reshape array
                    roi_gray = gray[y:y + h, x:x + w]
                    roi_gray = cv2.resize(roi_gray, (48, 48))
                    roi_gray = roi_gray.reshape(1, 48, 48, 1)
                    roi_gray = roi_gray / 255

                    # predict the emotion with the highest probability
                    emotion_predicted = self.model.predict(roi_gray)
                    emotion_predicted_index = np.argmax(emotion_predicted)

                    # draw a frame around the face
                    cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 0, 0), 1)

                    emote = self.emotion_labels[emotion_predicted_index]

                    # display emotion counts
                    counts_str = ''
                    for label, count in self.emotion_counts.items():
                        counts_str += f'{label}: {count}  '
                    cv2.putText(frame, counts_str, (10, self.frame_height - 50),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 0), 2, cv2.LINE_AA)

                    # display emotion label
                    cv2.putText(frame, emote, (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX,
                                1, (0, 0, 0), 2, cv2.LINE_AA)

                    # save image to corresponding folder
                    if time.time() - self.last_picture_time > self.picture_interval:
                        timestamp = time.strftime("%d%b%Y_%H%M%S")
                        image_path = self.img_path / emote.lower() / f'{emote.lower()}_{timestamp}.jpg'
                        cv2.imwrite(str(image_path), frame)
                        self.emotion_counts[emote] += 1
                        self.last_picture_time = time.time()

            # display the frame
            cv2.imshow('Emotion Detector', frame)

            # exit on 'q' key press
            if cv2.waitKey(1) & 0xFF == ord('q') or self.button2_pressed:
                break

        # release the camera and close all windows
        self.cap.release()
        self.out.release()
        cv2.destroyAllWindows()


if __name__ == '__main__':
    detector = EmotionDetector()
    detector.run()