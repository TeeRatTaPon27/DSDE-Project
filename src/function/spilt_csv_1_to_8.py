import pandas as pd
import os

chunksize = 100000
i = 1


current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, '..', '..'))
input_path = os.path.join(project_root, 'dataset', 'bangkok_traffy.csv')
# print(f"Reading data from: {input_path}

for chunk in pd.read_csv(input_path, chunksize=chunksize):
    # outname = f"C:/Users/acer/OneDrive/Documents/Road-to-AI/Intro-Data-Science-S1/Project-DSDE/dataset/bangkok_traffy_part_{i}.csv"
    OUTPUT_NAME = f"bangkok_traffy_part_{i}.csv"
    OUTPUT_CSV = os.path.join(project_root, 'dataset', OUTPUT_NAME)
    chunk.to_csv(OUTPUT_CSV, index=False)
    print(f"Saved {OUTPUT_CSV} ({len(chunk)} rows)")
    i += 1