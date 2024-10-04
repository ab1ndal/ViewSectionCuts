# Create a function to convert images to a PDF using Pillow library
# I pass the folder path, find all png images, sort them and convert them to a PDF
# Place images in "n" by "m" grid on a letter page in portrait or landscape mode

import os
import re
import math
from PIL import Image

def convert_images_to_pdf(folder_path, rows=2, columns=2, orientation='portrait', dpi=600):
    files = os.listdir(folder_path)
    png_files = [f for f in files if re.match(r'.*\.png$', f)]
    png_files.sort()

    if len(png_files) == 0:
        print('No PNG files found in the folder.')
        return

    # Filter "Overall" files and sort them in the required order
    overall_files = [f for f in png_files if 'Overkall' in f]

    # Get the rest of the files (non-overall)
    other_files = [f for f in png_files if f not in overall_files]

    # Function to create PDF from a list of images
    def create_pdf(image_files, output_pdf):
        if len(image_files) == 0:
            print(f"No images for {output_pdf}, skipping.")
            return

        # Define DPI scaling (1 point = 1/72 inch, so scale page size by DPI/72)
        scale_factor = dpi / 72.0

        # Define page dimensions (portrait or landscape)
        if orientation == 'portrait':
            page_width, page_height = int(612 * scale_factor), int(792 * scale_factor)  # 8.5 x 11 inches
        else:  # landscape
            page_width, page_height = int(792 * scale_factor), int(612 * scale_factor)

        # Calculate the number of pages required
        num_pages = math.ceil(len(image_files) / (rows * columns))
        print(f'Number of pages required for {output_pdf}: {num_pages}')

        # Calculate cell size based on grid layout
        cell_width = page_width // columns
        cell_height = page_height // rows

        pdf_pages = []

        for page in range(num_pages):
            pdf = Image.new('RGB', (page_width, page_height), 'white')

            for i in range(rows):
                for j in range(columns):
                    index = page * rows * columns + i * columns + j
                    if index >= len(image_files):
                        break

                    img_path = os.path.join(folder_path, image_files[index])
                    img = Image.open(img_path)

                    # Calculate scaling to fit the image into the cell while maintaining aspect ratio
                    img_aspect_ratio = img.width / img.height
                    cell_aspect_ratio = cell_width / cell_height

                    if img_aspect_ratio > cell_aspect_ratio:
                        # Image is wider relative to the cell, fit by width
                        new_width = cell_width
                        new_height = int(new_width / img_aspect_ratio)
                    else:
                        # Image is taller relative to the cell, fit by height
                        new_height = cell_height
                        new_width = int(new_height * img_aspect_ratio)

                    # Resize image to fit within the cell using high-quality downsampling only if necessary
                    if img.width > new_width or img.height > new_height:
                        img = img.resize((new_width, new_height), Image.LANCZOS)

                    # Calculate position to center the image in the cell
                    x_offset = j * cell_width + (cell_width - new_width) // 2
                    y_offset = i * cell_height + (cell_height - new_height) // 2

                    pdf.paste(img, (x_offset, y_offset))

            # Append each page
            pdf_pages.append(pdf)

        # Combine all the images into one single PDF
        first_image = pdf_pages[0]
        pdf_path = os.path.join(folder_path, output_pdf)
        first_image.save(pdf_path, save_all=True, append_images=pdf_pages[1:], resolution=dpi)
        print(f'PDF created: {pdf_path}')

    # Create the "Overall" ordered PDF
    #create_pdf(overall_files, '305-LB_Overall_SectioncutForces_SLE.pdf')

    # Create the "Other" PDF for the rest of the files
    create_pdf(other_files, '302_Gridline_SectionCutForces_MCE.pdf')


# Example usage
loc = r"C:\\Users\\abindal\\OneDrive - Nabih Youssef & Associates\\Documents\\00_Projects\\06_The Vault\\20240905_302\\New Run\\"
convert_images_to_pdf(loc, rows=2, columns=1, orientation='portrait')