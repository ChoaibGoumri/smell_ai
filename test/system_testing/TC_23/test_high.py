import pandas as pd
# High Density: d >= 0.05
# 1 smell / ~10 lines = 0.1

def high_density_func():
    # Smell: Unnecessary Iteration
    # This is very dense with smells relative to LOC
    df = pd.DataFrame({'A': [1, 2, 3]})
    total = 0
    for i in range(len(df)):
        total += df.iloc[i]['A']
    return total
