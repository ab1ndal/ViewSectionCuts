import cv2
import os
import sys

def save_frames(video_path, save_path, target_fps=1):
    # Open the video file
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        print('Error: Could not open video file')
        sys.exit()

    # Get the frames per second of the video
    original_fps = cap.get(cv2.CAP_PROP_FPS)

    # Calculate the interval between frames to save
    frame_interval = int(original_fps // target_fps)
    
    # Check if the save_path exists, create if it doesn't
    if not os.path.exists(save_path):
        os.makedirs(save_path)

    frame_count = 0
    saved_frame_count = 0

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        # Save the frame if it is at the desired interval
        if frame_count % frame_interval == 0:
            frame_filename = os.path.join(save_path, f'frame_{saved_frame_count:04d}.jpg')
            cv2.imwrite(frame_filename, frame)
            saved_frame_count += 1
        
        frame_count += 1

    # Release the VideoCapture object
    cap.release()

    print(f'Saved {saved_frame_count} frames successfully')


def updateFrames(save_path):
    # Add file name to the top of each image
    for file in os.listdir(save_path):
        if file.endswith('.jpg'):
            img = cv2.imread(os.path.join(save_path, file))
            if img is None:
                print(f"Error: Could not read image {file}")
                continue

            font = cv2.FONT_HERSHEY_SIMPLEX
            font_scale = 4
            font_color = (255, 255, 255)
            line_type = 2

            # Calculate text size
            text_size = cv2.getTextSize('L'+file.strip('.jpg'), font, font_scale, line_type)[0]

            # Define text position and background
            text_x = 10
            text_y = text_size[1] + 10
            background_topleft = (text_x - 5, text_y - text_size[1] - 5)
            background_bottomright = (text_x + text_size[0] + 5, text_y + 5)

            # Draw background rectangle
            cv2.rectangle(img, background_topleft, background_bottomright, (0, 0, 0), -1)

            # Put text on the image
            cv2.putText(img, 'L'+file.strip('.jpg'), (text_x, text_y), font, font_scale, font_color, line_type)

            # Save the updated image
            cv2.imwrite(os.path.join(save_path, file), img)

    print('Updated frames with filenames')

def createVideo(save_path):
    # Ceate a video from the frames. The video will be saved in the same directory as the frames
    # The frames are assumed to be in the format xxx.jpg
    # The video will be saved as output.mp4
    # The video will have a frame rate of 30 fps
    
    # The order of reading file should start from G01 and then follow 001, 002, etc
    fileName = []
    for file in os.listdir(save_path):
        if file.endswith('.jpg'):
            fileName.append(file)
    fileName = [fileName[-1]] + fileName[:-1]
    print(fileName)

    for file in fileName:
        if file.endswith('.jpg'):
            img = cv2.imread(os.path.join(save_path, file))
            if img is None:
                print(f"Error: Could not read image {file}")
                continue

            height, width, _ = img.shape

            # Check if the video writer object has been created
            if 'video_writer' not in locals():
                video_writer = cv2.VideoWriter(os.path.join(save_path, 'output.mp4'), cv2.VideoWriter_fourcc(*'mp4v'), 2, (width, height))

            video_writer.write(img)


# Path to the video file
video_path = r'C:\\Users\\abindal\\OneDrive - Nabih Youssef & Associates\\The Vault Files\\Drift_SLE-Y.mp4'
save_path = r'C:\\Users\\abindal\\OneDrive - Nabih Youssef & Associates\\The Vault Files\\frames'
#save_frames(video_path, save_path)
#updateFrames(save_path)
createVideo(save_path)