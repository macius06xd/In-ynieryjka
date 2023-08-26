# 1. folder with raw images - images in initial state, all in one folder
#INITIAL_IMAGES_FOLDER = r"C:\Users\wojte\OneDrive\Pulpit\pulpit\klockitesty"
#INITIAL_IMAGES_FOLDER = r"C:\Users\logix\Desktop\inzynierka\Inzynierka\klocki\milion_zdjec"
#INITIAL_IMAGES_FOLDER = r"C:\Users\logix\Desktop\inzynierka\Inzynierka\klocki\caly_set_pomieszane"
INITIAL_IMAGES_FOLDER = r"C:\Users\logix\Desktop\inzynierka\Inzynierka\klocki\initial_images_folder"

# 2.folder with raw images but after first, general clusterization
#INITIAL_CLUSTERIZED_FOLDER = r"C:\Users\wojte\OneDrive\Pulpit\pulpit\pliczki"
#INITIAL_CLUSTERIZED_FOLDER = r"D:\initial_clusterized_folder"
INITIAL_CLUSTERIZED_FOLDER = r"C:\Users\logix\Desktop\inzynierka\Inzynierka\klocki\initial_clusterized_folder"

# 3. folder which contains original-sized images (equal to 2(???))
#DEFAULT_IMAGES_PATH = r"C:\Users\wojte\OneDrive\Pulpit\pulpit\klocki"
#DEFAULT_IMAGES_PATH = r"D:\initial_clusterized_folder"
DEFAULT_IMAGES_PATH = r"C:\Users\logix\Desktop\inzynierka\Inzynierka\klocki"

# 4. output folder for CreateResizedDataset. It contains resized images with "_small" at the end
#RESIZED_IMAGES_PATH = r"C:\Users\wojte\OneDrive\Pulpit\pulpit\small"
#RESIZED_IMAGES_PATH  = r"D:\resized_images_path"
RESIZED_IMAGES_PATH  = r"C:\Users\logix\Desktop\inzynierka\Inzynierka\klocki\resized_images_path"

# 5. path of file containing vectors
#VECTORS_PATH = r"C:\Users\wojte\OneDrive\Pulpit\pulpit\xception2.hdf"
#VECTORS_PATH=r"D:\half_mln.hdf"
VECTORS_PATH = r"C:\Users\logix\Desktop\inzynierka\xception2.hdf"

# 6. path of directory with final results
#RESULTS_PATH = r"C:\Users\wojte\OneDrive\Pulpit\pulpit\wyniki"
RESULTS_PATH = r"C:\Users\logix\Desktop\inzynierka\Inzynierka\klocki\results_path"

# Size of images in pixels after resizing
RESIZED_IMAGES_SIZE = 64

time = 0

# Variable used to decide whether create or load database
is_it_run_first_time = 0