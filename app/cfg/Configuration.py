from PyQt5.QtGui import QColor

# 1. folder with raw images - images in initial state, all in one folder
INITIAL_IMAGES_FOLDER = r"C:\Users\wojte\OneDrive\Pulpit\pulpit\testowy"
#INITIAL_IMAGES_FOLDER = r"C:\Users\logix\Desktop\inzynierka\Inzynierka\klocki\milion_zdjec"
#INITIAL_IMAGES_FOLDER = r"C:\Users\logix\Desktop\inzynierka\Inzynierka\klocki\caly_set_pomieszane"
#INITIAL_IMAGES_FOLDER = r"C:\Users\logix\Desktop\inzynierka\Inzynierka\klocki\initial_images_folder"

# 2.folder with raw images but after first, general clusterization
INITIAL_CLUSTERIZED_FOLDER = r"C:\Users\wojte\OneDrive\Pulpit\pulpit\pliczki"
#INITIAL_CLUSTERIZED_FOLDER = r"D:\initial_clusterized_folder"
#INITIAL_CLUSTERIZED_FOLDER = r"C:\Users\logix\Desktop\inzynierka\Inzynierka\klocki\initial_clusterized_folder"

# 4. output folder for CreateResizedDataset. It contains resized images with "_small" at the end
RESIZED_IMAGES_PATH = r"C:\Users\wojte\OneDrive\Pulpit\pulpit\small"
#RESIZED_IMAGES_PATH  = r"D:\resized_images_path"
#RESIZED_IMAGES_PATH  = r"C:\Users\logix\Desktop\inzynierka\Inzynierka\klocki\resized_images_path"

# 5. path of file containing vectors
VECTORS_PATH = r"C:\Users\wojte\OneDrive\Pulpit\pulpit\xception2.hdf"
#VECTORS_PATH=r"D:\half_mln.hdf"
#VECTORS_PATH = r"C:\Users\logix\Desktop\inzynierka\xception2.hdf"

# 6. path of directory with final results
RESULTS_PATH = r"C:\Users\wojte\OneDrive\Pulpit\pulpit\wyniki"
#RESULTS_PATH = r"C:\Users\logix\Desktop\inzynierka\Inzynierka\klocki\results_path"

# 7. path of folder containing database snapshots 
DATABASE_SNAPSHOTS = r"C:\Users\wojte\OneDrive\Pulpit\pulpit\database_snapshots"
#DATABASE_SNAPSHOTS = r"C:\Users\logix\Desktop\inzynierka\Inzynierka\klocki\database_snapshots"

# Size of images in pixels after resizing
RESIZED_IMAGES_SIZE = 64

time = 0

# Variable used to decide whether create or load database
is_it_run_first_time = 0

color_mapping = {
    0: QColor(0, 0, 0),
    1: QColor(0, 255, 0),
    2: QColor(0, 0, 255),
    3: QColor(0, 125, 0),
    4: QColor(0, 125, 125),
    5: QColor(125, 125, 0),
    6: QColor(255, 255, 0),
    7: QColor(0, 255, 255),
    8: QColor(255, 125, 0),
    9: QColor(0, 125, 255),
    10: QColor(255, 125, 255),
    11: QColor(125, 0, 125),
    12: QColor(125, 255, 0),
    13: QColor(255, 0, 125),
    14: QColor(125, 0, 0),
    15: QColor(0, 0, 125),
    16: QColor(0, 255, 125),
    17: QColor(125, 125, 255),
    18: QColor(255, 0, 255),
    19: QColor(255, 255, 125),
    20: QColor(125, 255, 255),
    21: QColor(125, 125, 125),
    22: QColor(255, 125, 125),
    23: QColor(125, 255, 125),
    24: QColor(125, 125, 255),
    25: QColor(75, 0, 0),
    26: QColor(0, 75, 0),
    27: QColor(0, 0, 75),
    28: QColor(75, 75, 0),
    29: QColor(0, 75, 75),
    30: QColor(75, 0, 75)
}
color_state = 0
def get_next_color():
    global color_state
    color_id = color_state
    color_state = color_state +1
    if color_state >= len(color_mapping):
        color_state = 0
    return color_id

def print_memory_usage():
    # Get information about memory usage by your program
    import psutil
    process = psutil.Process()
    memory_info = process.memory_info()

    # Get the amount of memory currently used by your program in bytes
    memory_used = memory_info.rss

    # Get the total physical memory available on the system
    total_memory = psutil.virtual_memory().total

    # Get the amount of available memory on the system
    available_memory = psutil.virtual_memory().available

    print(f"Memory used by your program: {memory_used} bytes")
    print(f"Total physical memory on the system: {total_memory} bytes")
    print(f"Available memory on the system: {available_memory} bytes")