# Create a function to convert images to a PDF using Pillow library
# I pass the folder path, find all png images, sort them and convert them to a PDF
# Place images in "n" by "m" grid on a letter page in portrait or landscape mode

import os
import re
import math
from PIL import Image
import PyPDF2

def convert_images_to_pdf(folder_path, rows=2, columns=2, orientation='portrait', dpi=600):
    files = os.listdir(folder_path)
    png_files = [f for f in files if re.match(r'.*\.png$', f)]
    png_files.sort()

    if len(png_files) == 0:
        print('No PNG files found in the folder.')
        return

    # Filter "Overall" files and sort them in the required order
    overall_files = [f for f in png_files if 'Overall' in f]

    # Get the rest of the files (non-overall)
    other_files = [f for f in png_files if f not in overall_files]

    # Create the "Overall" ordered PDF
    create_pdf(overall_files, '305-LB_Overall_SectioncutForces_MCE.pdf', orientation, dpi, rows, columns, folder_path)

    # Create the "Other" PDF for the rest of the files
    #create_pdf(other_files, '305_UB_Gridline_SectionCutForces_MCE.pdf', orientation, dpi, rows, columns, folder_path)


# Function to create PDF from a list of images
def create_pdf(image_files, output_pdf, orientation='portrait', dpi=600, rows=2, columns=2, folder_path='.'):
    if len(image_files) == 0:
        print(f"No images for {output_pdf}, skipping.")
        return

    # Define DPI scaling (1 point = 1/72 inch, so scale page size by DPI/72)
    scale_factor = dpi / 72.0

    # Define page dimensions (portrait or landscape)
    page_width, page_height = int(8.5 * 72 * scale_factor), int(11 * 72 * scale_factor)  # 8.5 x 11 inches
    
    if orientation == 'landscape':
        page_width, page_height = page_height, page_width

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
                #print(f'Image aspect ratio: {img_aspect_ratio}')
                cell_aspect_ratio = cell_width / cell_height
                #print(f'Cell aspect ratio: {cell_aspect_ratio}')

                if img_aspect_ratio > cell_aspect_ratio:
                    # Image is wider relative to the cell, fit by width
                    new_width = cell_width
                    new_height = int(new_width / img_aspect_ratio)
                else:
                    # Image is taller relative to the cell, fit by height
                    new_height = cell_height
                    new_width = int(new_height * img_aspect_ratio)
                    #print(f'New width: {new_width}, new height: {new_height}')
                    #print(f'old width: {img.width}, old height: {img.height}')

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
    
    # Return the combined PDF
    return output_pdf


def convert_disp_drift_to_pdf(folder_path, rows=2, columns=2, orientation='landscape', dpi=600, 
                              gridline = [], plot_type = ['Drift', 'Disp'], gm_type = [], prefix='', suffix=''):
    files = os.listdir(folder_path)
    
    for p in plot_type:
        GridfileList = []
        GMfileList = []
        for g in gridline:
            fileName = os.path.join(folder_path, f'{g}_{p}.png')
            if os.path.exists(fileName):
                GridfileList.append(fileName)
        for g in gm_type:
            fileName = os.path.join(folder_path, f'{g}_{p}.png')
            if os.path.exists(fileName):
                GMfileList.append(fileName)
        pdfs = []
        if len(GridfileList) > 0:
            pdfs.append(create_pdf(GridfileList, f'{p}_Gridline.pdf', orientation, dpi, rows, columns, folder_path))
        if len(GMfileList) > 0:
            pdfs.append(create_pdf(GMfileList, f'{p}_GM.pdf', orientation, dpi, rows, columns, folder_path))

        # I know names of two pdf files. I can combine them into one
        combine_pdfs(folder_path, pdfs, f'{prefix}_{p}_{suffix}.pdf')


def combine_pdfs(file_loc, pdf_files, output_pdf):
    # Create a PDF merger object
    merger = PyPDF2.PdfMerger()

    # Iterate over all the files in the list and append them
    for pdf_file in pdf_files:
        with open(os.path.join(file_loc, pdf_file), 'rb') as file:
            merger.append(file)

    # Write the combined PDF to the output path
    output_path = os.path.join(file_loc, output_pdf)
    with open(output_path, 'wb') as output_file:
        merger.write(output_file)

    print(f"All PDFs combined and saved as: {output_path}")


# Example usage
loc = r"C:\\Users\\abindal\\OneDrive - Nabih Youssef & Associates\\Documents - The Vault\\Calculations\\2025 -  Stage 3C\\305 - Model Results\\20250207_305_FineMesh_LB\SectionCuts\\"
convert_images_to_pdf(loc, rows=2, columns=1, orientation='portrait')

#loc = r"C:\\Users\\abindal\\Downloads\\205-LB_DispDrift_MCE-avg\\"
#gridline = ['N12A', 'N12B', 'N12C', 'N12D', 'N12', 'N13A', 'N13B', 'N13C', 'N13D', 'N13E', 'N13F', 'N13G', 'N13H']
#gmlist = ['1.0D+0.5L', 'SC - TP', 'SC -TN', 'SLE - 1% Damped - U1', 'SLE - 1% Damped - U2', f'1.0D+.75T+Lexp+Env(100%+30% SLE)']
#gmlist = ['1.0D+0.5L', 'SC - TP', 'SC -TN', 'MCE-All GM Average', 'D+0.5L+0.5T+MCEavg']
#convert_disp_drift_to_pdf(loc, rows=2, columns=2, orientation='landscape', gridline=gridline, gm_type=gmlist, prefix='205-LB', suffix='MCE-Avg')