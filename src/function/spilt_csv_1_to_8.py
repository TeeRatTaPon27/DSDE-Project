import pandas as pd

chunksize = 100000
i = 1

for chunk in pd.read_csv("C:/Users/acer/OneDrive/Documents/Road-to-AI/Intro-Data-Science-S1/Project-DSDE/dataset/bangkok_traffy.csv", chunksize=chunksize):
    outname = f"C:/Users/acer/OneDrive/Documents/Road-to-AI/Intro-Data-Science-S1/Project-DSDE/dataset/bangkok_traffy_part_{i}.csv"
    chunk.to_csv(outname, index=False)
    print(f"Saved {outname} ({len(chunk)} rows)")
    i += 1