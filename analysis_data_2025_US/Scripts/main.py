# from step0_collection import run_step0
from step1_analysis import run_step1
from step2_clean_data import run_step2
from step3_feature_engineering import run_step3
from step4_analysis import run_step4

def main():
    print("BẮT ĐẦU DỰ ÁN SPOTIFY ANALYSIS DATA 2025 US")
    # Step 0: Data Collection & Enrichment
    # run_step0()
    # Step 1: Data Analysis
    run_step1()
    # Step 2: Data Cleaning
    run_step2()
    # Step 3: Feature Engineering
    run_step3()
    # Step 4: Analysis & Insights
    run_step4()
    

    
if __name__ == "__main__":
    main()