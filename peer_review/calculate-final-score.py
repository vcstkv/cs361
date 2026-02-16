import pandas as pd
import argparse

def process_files(input_file, multiplier_score, assignment_number, output_file):
    main_df = pd.read_csv(input_file)
    multiplier_df = pd.read_csv(multiplier_score)

    email_multiplier = {}
    for row in multiplier_df.itertuples(index=True):
        email_multiplier[row.Email] = 0.6 if row.Q3 == "**NO SUBMISSION**" else row.PeerEvaluationScore
    
    col_name = None
    for x in list(main_df.columns):
        if f"CP-Assignment#{assignment_number}" in x:
            col_name = x

    flag = 0
    for index, row in main_df.iterrows():
        flag += 1
        if flag <= 2:
            continue
        main_df.at[index, col_name] = str(round(float(row[col_name]) * (email_multiplier.get(row["SIS Login ID"], 0)), 2))
    main_df.to_csv(output_file, index=False)

def main():
    parser = argparse.ArgumentParser(description="Process CSV scores")
    parser.add_argument("--input", required=True, help="Input CSV file")
    parser.add_argument("--multiplier_score",required=True, help="Score multiplier")
    parser.add_argument("--assignment_number", type=int, required=True, help="Assignment Number")
    parser.add_argument("--output", required=True, help="Output CSV file")

    args = parser.parse_args()
    input_file = args.input
    output_file = args.output
    multiplier_score = args.multiplier_score
    assignment_number = args.assignment_number

    process_files(input_file, multiplier_score, assignment_number, output_file)

if __name__ == "__main__":
    main()