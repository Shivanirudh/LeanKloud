import numpy as np
import pandas as pd

df = pd.read_csv('Student_marks_list.csv')

for col in df.columns[1:]:
    max_val = df[col].max()
    print("Topper in %s is %s" %(col, df[df[col]==max_val]['Name'].values[0]))


df['Total'] = df.sum(axis=1)

tops = df.nlargest(3, ['Total'])['Name'].values
print("Best students in the class are: %s-1st rank, %s-2nd rank, %s-3rd rank" %(tops[0], tops[1], tops[2]))

print("The time complexity of finding the best 3 students is O(n)")