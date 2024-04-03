import pandas as pd
import os


print("Starting to remove duplications")
def check_file_exists(file_path):
    # Check if the file exists
    if os.path.isfile(file_path):
        print(f"The file {file_path} exists.")
        return True
    else:
        print(f"The file {file_path} does not exist.")
        return False
def remove_duplicates_from_csv(csv_file):
    # Check if the file exists
    print("Starting script to remove duplicates.")
    if not os.path.isfile(csv_file):
        print(f"The file {csv_file} does not exist.")
        return

    try:
        # Read the CSV file
        df = pd.read_csv(csv_file)
    except Exception as e:
        print(f"An error occurred while reading the file {csv_file}: {e}")
        return

    # Find duplicate rows
    duplicates = df[df.duplicated()]

    # If there are no duplicates, print a message and return
    if duplicates.empty:
        print("No duplicate rows found.")
        return

    # Print duplicate rows
    print("The following duplicate rows will be removed:")
    print(duplicates)

    # Remove duplicate rows
    df.drop_duplicates(inplace=True)

    try:
        # Write the DataFrame back to the CSV file
        df.to_csv(csv_file, index=False)
    except Exception as e:
        print(f"An error occurred while writing to the file {csv_file}: {e}")
        return

    print(f"Duplicates have been successfully removed from {csv_file}.")




check_file_exists(os.getenv('CSV_FILE_PATH'))
remove_duplicates_from_csv(os.getenv('CSV_FILE_PATH'))
print("Script Finished!")
