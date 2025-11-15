#!/usr/bin/env python3
"""
Calculate peer review grades from Qualtrics survey data.

This script:
1. Reads team data and calculates team sizes
2. Reads Qualtrics peer evaluation survey results
3. Processes peer evaluation responses for each student
4. Calculates mean scores and normalizes them
5. Calculates final peer evaluation scores
6. Creates visualizations
7. Saves results with Name, Email, Score, and Q3 text responses
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import re
import argparse


def extract_digit(text):
    """Extract first digit from text using regex"""
    match = re.search(r'\d', str(text))
    return int(match.group(0)) if match else None


### Question 1 (Likert scale questions)
# X goes from 1 to 4, 1 is self, 2-4 are team members

# Does the member do an appropriate quantity of work?
# labels[,Q1_X_1]

# How about the quality of the member's work?
# labels[,Q1_X_2]

# Rate the member's attitude as a team player (eager to do assigned work, communicated with others, kept appointments, etc.).
# labels[,Q1_X_3]

# Rate the overall value of the member's technical contribution.
# labels[,Q1_X_4]

# Would you want to work with this person on a project again?
# labels[,Q1_X_5]

### Question 2 (Point distribution)
# Take 100 points, and divide them among the N team members, including yourself. Give points based on your opinion of what proportion of the credit each member deserves. You may consider quality and quantity of contributions, team-player attitude, and/or any aspects that you feel are relevant. You must give yourself at least 100/N points, whether you honestly feel you deserve them or not. (This is to avoid an unrealistic "self-incrimination" requirement.)
# X goes from 1 to 4, 1 is self, 2-4 are team members
# labels[,Q2_X_1]

### Question 3 (Text answer)
# Free-form text answer about each team member
# labels[,Q3]


def main():
    # Parse command-line arguments
    parser = argparse.ArgumentParser(
        description='Calculate peer review grades from Qualtrics survey data'
    )
    parser.add_argument(
        'groups_file',
        help='Path to the CSV file with team/group data'
    )
    parser.add_argument(
        'survey_file',
        help='Path to the Qualtrics peer evaluation survey CSV file'
    )
    parser.add_argument(
        'output_file',
        help='Path for the output CSV file with Name, LastName, Email, Score, Q3'
    )
    parser.add_argument(
        '--plot-output',
        default='peer_evaluation_distribution.png',
        help='Path for the distribution plot (default: peer_evaluation_distribution.png)'
    )
    
    args = parser.parse_args()
    
    # Read all students from groups file
    all_students = pd.read_csv(args.groups_file)
    
    # Extract name parts and create email column
    all_students['RecipientLastName'] = all_students['name'].str.split(',').str[0].str.strip()
    all_students['RecipientFirstName'] = all_students['name'].str.split(',').str[1].str.strip()
    all_students['RecipientEmail'] = all_students['login_id']
    all_students['Team'] = all_students['group_name']
    
    # Read team sizes
    team_sizes = all_students.groupby('group_name').size().reset_index(name='n')
    team_sizes.rename(columns={'group_name': 'Team'}, inplace=True)
    
    # Read survey data (keep_default_na=False to preserve "N/A" as text)
    dt = pd.read_csv(args.survey_file, keep_default_na=False)
    
    # Extract labels from first row
    labels = pd.DataFrame({
        'question_id': dt.columns,
        'question_label': dt.iloc[0].values
    })
    
    # Remove first two rows (headers)
    dt = dt.iloc[2:].reset_index(drop=True)
    
    # Clean up columns
    columns_to_drop = [
        'StartDate', 'EndDate', 'Status', 'IPAddress', 'Progress',
        'Duration (in seconds)', 'Finished', 'RecordedDate', 'ResponseId',
        'ExternalReference', 'LocationLatitude', 'LocationLongitude',
        'DistributionChannel', 'UserLanguage'
    ]
    dt = dt.drop(columns=[col for col in columns_to_drop if col in dt.columns])
    
    # Add team size
    dt = dt.merge(team_sizes, on='Team', how='left')
    
    # Initialize output dataframe
    output = dt[['RecipientLastName', 'RecipientFirstName', 'RecipientEmail', 'Team', 'n']].copy()
    output['Name'] = output['RecipientLastName'] + ', ' + output['RecipientFirstName']
    output['Email'] = output['RecipientEmail']
    
    # Add Team Member columns if they exist
    for i in range(1, 4):
        col_name = f'Team Member {i}'
        if col_name in dt.columns:
            output[col_name] = dt[col_name]
    
    # Reorder columns
    cols = ['Name', 'Email', 'Team', 'n']
    for i in range(1, 4):
        col_name = f'Team Member {i}'
        if col_name in output.columns:
            cols.append(col_name)
    output = output[cols]
    
    # Initialize lists for storing peer evaluations
    output['Q11'] = [[] for _ in range(len(output))]
    output['Q12'] = [[] for _ in range(len(output))]
    output['Q13'] = [[] for _ in range(len(output))]
    output['Q14'] = [[] for _ in range(len(output))]
    output['Q15'] = [[] for _ in range(len(output))]
    output['Q2'] = [[] for _ in range(len(output))]
    output['Q3'] = ""  # Q3 stores single self-evaluation text per student
    
    # Process each student's peer evaluations
    for i in range(len(output)):
        team = output.loc[i, 'Team']
        email = output.loc[i, 'Email']
        
        # Get the student's own survey response (for Q3 self-evaluation)
        self_response = dt[dt['RecipientEmail'] == email]
        if len(self_response) > 0:
            output.at[i, 'Q3'] = self_response.iloc[0].get('Q3', "")
        else:
            output.at[i, 'Q3'] = ""
        
        # Get all evaluations from teammates (excluding self)
        results = dt[(dt['Team'] == team) & (dt['RecipientEmail'] != email)].copy()
        
        if len(results) == 0:
            # If no results, leave lists empty (will become NA)
            continue
        
        q11, q12, q13, q14, q15, q2 = [], [], [], [], [], []
        
        for j in range(len(results)):
            # Find which team member X this is (which column contains the current email)
            result_row = results.iloc[j]
            
            # Find the column that contains this email
            x = None
            for col in result_row.index:
                if result_row[col] == email and 'Team Member' in str(col):
                    digit = extract_digit(col)
                    if digit is not None:
                        x = digit + 1  # Add 1 because first entry is self
                        break
            
            if x is None:
                q11.append(np.nan)
                q12.append(np.nan)
                q13.append(np.nan)
                q14.append(np.nan)
                q15.append(np.nan)
                q2.append(np.nan)
                continue
            
            # Extract the responses
            q11.append(result_row.get(f'Q1_{x}_1', np.nan))
            q12.append(result_row.get(f'Q1_{x}_2', np.nan))
            q13.append(result_row.get(f'Q1_{x}_3', np.nan))
            q14.append(result_row.get(f'Q1_{x}_4', np.nan))
            q15.append(result_row.get(f'Q1_{x}_5', np.nan))
            q2.append(result_row.get(f'Q2_{x}_1', np.nan))
        
        output.at[i, 'Q11'] = q11
        output.at[i, 'Q12'] = q12
        output.at[i, 'Q13'] = q13
        output.at[i, 'Q14'] = q14
        output.at[i, 'Q15'] = q15
        output.at[i, 'Q2'] = q2
    
    # Calculate means for each question
    def calculate_mean(values_list):
        """Calculate mean of numeric values in a list, ignoring NaN"""
        if not values_list or all(pd.isna(v) for v in values_list):
            return np.nan
        numeric_values = [float(v) for v in values_list if pd.notna(v) and v != '']
        if not numeric_values:
            return np.nan
        return np.mean(numeric_values)
    
    output['Q11_mean'] = output['Q11'].apply(calculate_mean)
    output['Q12_mean'] = output['Q12'].apply(calculate_mean)
    output['Q13_mean'] = output['Q13'].apply(calculate_mean)
    output['Q14_mean'] = output['Q14'].apply(calculate_mean)
    output['Q15_mean'] = output['Q15'].apply(calculate_mean)
    output['Q2_mean'] = output['Q2'].apply(calculate_mean)
    
    # Normalize scores
    output['Q11_normalized'] = (output['Q11_mean'] * 10) + 50
    output['Q12_normalized'] = (output['Q12_mean'] * 10) + 50
    output['Q13_normalized'] = (output['Q13_mean'] * 10) + 50
    output['Q14_normalized'] = (output['Q14_mean'] * 10) + 50
    output['Q15_normalized'] = (output['Q15_mean'] * 10) + 50
    output['Q2_normalized'] = output['Q2_mean'] * output['n']
    
    # Shift Q2 scores
    output['Q2_shifted'] = output['Q2_normalized'] / 5
    output.loc[output['Q2_shifted'] < 10, 'Q2_shifted'] = 10
    output.loc[output['Q2_shifted'] > 40, 'Q2_shifted'] = 40
    output['Q2_shifted'] = (0.65 + (0.0225 * output['Q2_shifted']) - 
                            (0.00025 * output['Q2_shifted'] ** 2)) * 100
    
    # Calculate final peer evaluation score
    output['PeerEvaluationScore'] = (
        output['Q11_normalized'] + 
        output['Q12_normalized'] + 
        output['Q13_normalized'] + 
        output['Q14_normalized'] + 
        output['Q2_shifted']
    ) / 500 + 0.05

    output['PeerEvaluationScore'] = output['PeerEvaluationScore'].round(2)
    
    # Add students from groups_file who didn't fill the survey
    survey_emails = set(output['Email'].values)
    all_student_emails = set(all_students['RecipientEmail'].values)
    missing_emails = all_student_emails - survey_emails
    
    if len(missing_emails) > 0:
        # Create rows for missing students
        missing_students = all_students[all_students['RecipientEmail'].isin(missing_emails)].copy()
        missing_students['Name'] = missing_students['RecipientLastName'] + ', ' + missing_students['RecipientFirstName']
        missing_students = missing_students.merge(team_sizes, on='Team', how='left')
        
        # Initialize with empty/default values
        missing_rows = pd.DataFrame({
            'RecipientLastName': missing_students['RecipientLastName'],
            'RecipientFirstName': missing_students['RecipientFirstName'],
            'RecipientEmail': missing_students['RecipientEmail'],
            'Team': missing_students['Team'],
            'n': missing_students['n'],
            'Name': missing_students['Name'],
            'Email': missing_students['RecipientEmail'],
            'Q11': [[] for _ in range(len(missing_students))],
            'Q12': [[] for _ in range(len(missing_students))],
            'Q13': [[] for _ in range(len(missing_students))],
            'Q14': [[] for _ in range(len(missing_students))],
            'Q15': [[] for _ in range(len(missing_students))],
            'Q2': [[] for _ in range(len(missing_students))],
            'Q3': "**NO SUBMISSION**",
            'Q11_mean': np.nan,
            'Q12_mean': np.nan,
            'Q13_mean': np.nan,
            'Q14_mean': np.nan,
            'Q15_mean': np.nan,
            'Q2_mean': np.nan,
            'Q11_normalized': np.nan,
            'Q12_normalized': np.nan,
            'Q13_normalized': np.nan,
            'Q14_normalized': np.nan,
            'Q15_normalized': np.nan,
            'Q2_normalized': np.nan,
            'Q2_shifted': np.nan,
            'PeerEvaluationScore': np.nan
        })
        
        # Add Team Member columns if they exist in output
        for i in range(1, 4):
            col_name = f'Team Member {i}'
            if col_name in output.columns:
                missing_rows[col_name] = ""
        
        # Reorder columns to match output
        missing_rows = missing_rows[output.columns]
        
        # Append missing students to output
        output = pd.concat([output, missing_rows], ignore_index=True)
    
    # Create final output dataframe
    final_output = output[['Name', 'Email', 'Team', 'PeerEvaluationScore', 'Q3']].copy()
    
    # Save simplified output
    final_output.to_csv(args.output_file, index=False)
    print(f"Peer review grades saved to: {args.output_file}")
    
    # Create visualization
    fig, ax = plt.subplots(figsize=(10, 6))
    
    # Plot final peer evaluation score histogram
    output['PeerEvaluationScore'].dropna().hist(
        bins=20, alpha=0.7, color='#4285F4', ax=ax, edgecolor='black'
    )
    
    ax.set_xlabel('Final Peer Evaluation Score', fontweight='bold')
    ax.set_ylabel('Count', fontweight='bold')
    ax.set_title('Distribution of Final Peer Evaluation Scores', 
                 fontweight='bold')
    
    # Add vertical lines for mean and median
    mean_score = output['PeerEvaluationScore'].mean()
    median_score = output['PeerEvaluationScore'].median()
    ax.axvline(mean_score, color='red', linestyle='--', alpha=0.7, label=f'Mean: {mean_score:.3f}')
    ax.axvline(median_score, color='orange', linestyle='--', alpha=0.7, label=f'Median: {median_score:.3f}')
    ax.legend(loc='upper right')
    
    plt.tight_layout()
    plt.savefig(args.plot_output, dpi=300, bbox_inches='tight')
    print(f"Distribution plot saved to: {args.plot_output}")
    plt.close()
    
    # Print summary statistics
    print("\n=== Summary Statistics ===")
    print(f"Total students: {len(output)}")
    print(f"Mean peer evaluation score: {output['PeerEvaluationScore'].mean():.2f}")
    print(f"Median peer evaluation score: {output['PeerEvaluationScore'].median():.2f}")
    print(f"Std deviation: {output['PeerEvaluationScore'].std():.2f}")
    print(f"Min score: {output['PeerEvaluationScore'].min():.2f}")
    print(f"Max score: {output['PeerEvaluationScore'].max():.2f}")


if __name__ == "__main__":
    main()

