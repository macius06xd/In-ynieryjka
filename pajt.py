import h5py

def create_new_hdf_file(input_file_path, output_file_path):
    # Open the input HDF file for reading
    with h5py.File(input_file_path, 'r') as input_file:
        # Create a new HDF file for writing
        with h5py.File(output_file_path, 'w') as output_file:
            # Iterate over the second folder names
            for second_folder_name in input_file.keys():
                second_folder = input_file[second_folder_name]
                # Iterate over the file names in the second folder
                for file_name in second_folder.keys():
                    feature_vector = second_folder[file_name][:]
                    # Write the feature vector to the new HDF file
                    output_file.create_dataset(file_name, data=feature_vector)

# Usage example
input_file_path = 'xception.hdf'
output_file_path = 'xception2.hdf'
create_new_hdf_file(input_file_path, output_file_path)