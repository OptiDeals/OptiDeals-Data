import pandas as pd
import os

print("Starting to remove duplications and unwanted words")
def clean_csv_file(csv_file):
    # Check if the file exists
    print("Starting script to remove duplicates and unwanted words.")
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

    # If there are duplicates, remove them
    if not duplicates.empty:
        print("The following duplicate rows will be removed:")
        print(duplicates)

        # Remove duplicate rows
        df.drop_duplicates(inplace=True)

    # Define unwanted words
    unwanted_words = ['toilet', 'soap', 'bathroom', 'diaper']

    # Remove rows that contain unwanted words
    for word in unwanted_words:
        df = df[~df.apply(lambda row: row.astype(str).str.lower().str.contains(word).any(), axis=1)]

    try:
        # Write the DataFrame back to the CSV file
        df.to_csv(csv_file, index=False)
    except Exception as e:
        print(f"An error occurred while writing to the file {csv_file}: {e}")
        return

    print(f"Duplicates and rows with unwanted words have been successfully removed from {csv_file}.")

clean_csv_file(os.getenv('CSV_FILE_PATH'))
print("Script Finished!")
