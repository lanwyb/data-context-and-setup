import os
import pandas as pd


class Olist:
    def get_data(self):
        """
        This function returns a Python dict.
        Its keys should be 'sellers', 'orders', 'order_items' etc...
        Its values should be pandas.DataFrames loaded from csv files
        """
        # Hints 1: Build csv_path as "absolute path" in order to call this method from anywhere.
            # Do not hardcode your path as it only works on your machine ('Users/username/code...')
            # Use __file__ instead as an absolute path anchor independant of your usename
            # Make extensive use of `breakpoint()` to investigate what `__file__` variable is really
        # Hint 2: Use os.path library to construct path independent of Mac vs. Unix vs. Windows specificities
        project_path = os.path.dirname(__file__)
        csv_path = os.path.join(project_path, '..', 'data','csv')
        file_names = os.listdir(csv_path)
        file_names = [file for file in file_names if file.endswith('.csv')]
        key_names = []
        for file in file_names:
            if file[:5] == 'olist':
                file = file[6:]
            if "_dataset.csv" in file:
                file=file.replace("_dataset.csv", "")
            if ".csv" in file:
                file=file.replace(".csv", "")
            key_names.append(file)
        data = {}
        for (key, file_name) in zip(key_names, file_names):
            data[key] = pd.read_csv(os.path.join(csv_path, file_name))
        return data



    def ping(self):
        """
        You call ping I print pong.
        """
        print("pong")

ol = Olist()
print(ol.get_data())
