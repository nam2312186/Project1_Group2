import pandas as pd
import glob
import os

parent_folder = "data\data-top50"
subfolders = [os.path.join(parent_folder, name) for name in os.listdir(parent_folder)
              if os.path.isdir(os.path.join(parent_folder, name))]

print("Số folder con:", len(subfolders))
print("Danh sách folder con:", subfolders)


for i in range(0, len(subfolders)):

    get_sub = subfolders[i]

    csv_files = glob.glob(f"{get_sub}/*.csv")


    try:
        index = 4
        print("Số thứ tự file CSV:", i)
        print("tên  file:", csv_files[index])
        df = pd.read_csv(csv_files[index])
        
            # Hiển thị thông tin về DataFrame
        print("\nThông tin DataFrame:" + "của file " + csv_files[index])
        print(f"Số cột: {len(df.columns)}")
        print(f"Tên các cột: {list(df.columns)}")
        
        print("\n 5 dòng đầu")
        print(df.head())       
        print("\n 5 dòng cuối")
        print(df.tail())       
        print("\nThông tin chi tiết về DataFrame:")
        print(df.info())       
        print("\n kích thước")
        print(df.shape)        
        print("\n----------------")

    except:
        print("Lỗi không đọc được file CSV")