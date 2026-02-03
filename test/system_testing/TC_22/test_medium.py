
import pandas as pd
# Medium Density: 0.005 <= d < 0.05
# 1 smell / 50 lines = 0.02

def medium_density_func():
    # Some padding lines
    x = 1
    x = 2
    x = 3
    x = 4
    x = 5
    x = 6
    x = 7
    x = 8
    x = 9
    x = 10
    x = 11
    x = 12
    x = 13
    x = 14
    x = 15
    x = 16
    x = 17
    x = 18
    x = 19
    x = 20
    x = 21
    x = 22
    x = 23
    x = 24
    x = 25
    x = 26
    x = 27
    x = 28
    x = 29
    x = 30
    x = 31
    x = 32
    
    # Smell: Unnecessary Iteration
    df = pd.DataFrame({'A': [1, 2, 3]})
    total = 0
    for i in range(len(df)):
        total += df.iloc[i]['A']
    return total
