#!/usr/bin/env python3
"""
Calculate peer review grades from Qualtrics survey data.

This script:
1. Reads team data and calculates team sizes
2. Reads Qualtrics peer evaluation survey results
3. Processes peer evaluation responses for each student
4. Calculates mean scores for 5 Likert criteria (converted to 60-100 scale)
5. Calculates 100-point distribution scores (normalized to 85-115% range)
6. Calculates final peer evaluation scores as average of all 6 components
7. Creates visualizations
8. Saves results with Name, Email, Score, and Q3 text responses

Scoring methodology:
- Five criteria (Q1): 1-5 scale → 60-100 scale, averaged across teammates
- Point distribution (Q2): Normalized for team size, clamped 10-40, formula applied
- Final score: Average of 5 criteria scores + point distribution score
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


### Question 1 (Five Likert scale criteria)
# X goes from 1 to 4, 1 is self, 2-4 are team members
# Scoring: Convert 1-5 scale to 60-100 scale (1=60, 2=70, 3=80, 4=90, 5=100)
# Final: Average ratings for each member (excluding self)

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

### Question 2 (100-point distribution)
# Take 100 points, and divide them among the N team members, including yourself. Give points based on your opinion of what proportion of the credit each member deserves. You may consider quality and quantity of contributions, team-player attitude, and/or any aspects that you feel are relevant. You must give yourself at least 100/N points, whether you honestly feel you deserve them or not. (This is to avoid an unrealistic "self-incrimination" requirement.)
# X goes from 1 to 4, 1 is self, 2-4 are team members
# labels[,Q2_X_1]
# 
# Scoring process:
# 1. Verify self-evaluation >= 100/N and total = 100
# 2. Average ratings for each member (excluding self)
# 3. Multiply by N, divide by 5 (normalize for team size)
# 4. Clamp between 10-40 (ensures 85%-115% range)
# 5. Apply formula: 0.65 + 0.022*x - 0.00025*x² then multiply by 100

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
    
    # Initialize output dataframe with ALL students from groups file
    output = all_students[['RecipientLastName', 'RecipientFirstName', 'RecipientEmail', 'Team']].copy()
    output = output.merge(team_sizes, on='Team', how='left')
    output['Name'] = output['RecipientLastName'] + ', ' + output['RecipientFirstName']
    output['Email'] = output['RecipientEmail']
    
    # Add Team Member columns from survey data if they exist
    survey_team_members = {}
    for i in range(1, 4):
        col_name = f'Team Member {i}'
        if col_name in dt.columns:
            # Create a mapping from RecipientEmail to Team Member info
            team_member_map = dt.set_index('RecipientEmail')[col_name].to_dict()
            survey_team_members[col_name] = team_member_map
    
    # Add Team Member columns to output
    for col_name, member_map in survey_team_members.items():
        output[col_name] = output['Email'].map(member_map).fillna("")
    
    # Reorder columns
    cols = ['Name', 'Email', 'Team', 'n']
    for col_name in survey_team_members.keys():
        cols.append(col_name)
    output = output[cols]
    
    # Identify students with valid submissions to ensure only their evaluations count
    valid_evaluators = set()
    for _, row in dt.iterrows():
        # Check if this respondent has provided meaningful evaluations
        # Count non-empty Q1 responses (Likert scale questions) for teammates (not self)
        valid_q1_responses = 0
        valid_q2_responses = 0
        
        for col in dt.columns:
            # Check Q1 responses for teammates (Q1_2, Q1_3, Q1_4 etc - not Q1_1 which is self)
            if col.startswith('Q1_') and not col.startswith('Q1_1_') and col.endswith(('_1', '_2', '_3', '_4', '_5')):
                if pd.notna(row[col]) and str(row[col]).strip() not in ['', 'N/A', 'nan']:
                    try:
                        # Check if it's a valid numeric response
                        value = float(row[col])
                        if 1 <= value <= 5:  # Valid Likert scale range
                            valid_q1_responses += 1
                    except (ValueError, TypeError):
                        pass
            
            # Check Q2 responses for teammates (point distribution)
            elif col.startswith('Q2_') and not col.startswith('Q2_1_'):
                if pd.notna(row[col]) and str(row[col]).strip() not in ['', 'N/A', 'nan']:
                    try:
                        value = float(row[col])
                        if value >= 0:  # Valid point allocation
                            valid_q2_responses += 1
                    except (ValueError, TypeError):
                        pass
        
        # Consider submission valid if they have at least some teammate evaluations
        if valid_q1_responses >= 3 or valid_q2_responses >= 1:
            valid_evaluators.add(row['RecipientEmail'])
    
    print(f"Found {len(valid_evaluators)} students with valid submissions out of {len(dt)} survey responses")
    
    # Show which students have invalid submissions (for transparency)
    all_survey_emails = set(dt['RecipientEmail'].values)
    invalid_evaluators = all_survey_emails - valid_evaluators
    if invalid_evaluators:
        print(f"Students with incomplete/invalid submissions (won't count as evaluators): {sorted(invalid_evaluators)}")
    
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
            output.at[i, 'Q3'] = "**NO SUBMISSION**"
        
        # Get all evaluations from teammates (excluding self) who have valid submissions
        results = dt[(dt['Team'] == team) & 
                    (dt['RecipientEmail'] != email) & 
                    (dt['RecipientEmail'].isin(valid_evaluators))].copy()
        
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
    
    # Convert Likert scale ratings to 60-100 scale (1=60, 2=70, 3=80, 4=90, 5=100)
    output['Q11_normalized'] = (output['Q11_mean'] * 10) + 50
    output['Q12_normalized'] = (output['Q12_mean'] * 10) + 50
    output['Q13_normalized'] = (output['Q13_mean'] * 10) + 50
    output['Q14_normalized'] = (output['Q14_mean'] * 10) + 50
    output['Q15_normalized'] = (output['Q15_mean'] * 10) + 50
    
    # Process 100-point distribution scores
    # Step 1: Multiply by team size N, then divide by 5
    output['Q2_adjusted'] = (output['Q2_mean'] * output['n']) / 5
    
    # Step 2: Clamp between 10 and 40
    output['Q2_clamped'] = output['Q2_adjusted'].copy()
    output.loc[output['Q2_clamped'] < 10, 'Q2_clamped'] = 10
    output.loc[output['Q2_clamped'] > 40, 'Q2_clamped'] = 40
    
    # Step 3: Apply the formula: 0.65 + 0.022 * x - 0.00025 * x^2, then convert to percentage
    output['Q2_score'] = (0.65 + (0.022 * output['Q2_clamped']) - 
                          (0.00025 * output['Q2_clamped'] ** 2)) * 100
    
    # Calculate final peer evaluation score as average of 5 criteria and point distribution score
    output['PeerEvaluationScore'] = (
        output['Q11_normalized'] + 
        output['Q12_normalized'] + 
        output['Q13_normalized'] + 
        output['Q14_normalized'] + 
        output['Q15_normalized'] + 
        output['Q2_score']
    ) / 600 + 0.05

    output['PeerEvaluationScore'] = output['PeerEvaluationScore'].round(2)
    
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
    print(f"Students with peer evaluation scores: {output['PeerEvaluationScore'].notna().sum()}")
    print(f"Students without scores (no valid evaluations received): {output['PeerEvaluationScore'].isna().sum()}")
    
    # Calculate evaluation counts
    evaluation_counts = []
    for i, row in output.iterrows():
        count = len([x for x in row['Q11'] if pd.notna(x)])
        evaluation_counts.append(count)
    output['EvaluationsReceived'] = evaluation_counts
    
    print(f"Average evaluations received per student: {np.mean(evaluation_counts):.1f}")
    
    if output['PeerEvaluationScore'].notna().any():
        valid_scores = output['PeerEvaluationScore'].dropna()
        print(f"Mean peer evaluation score: {valid_scores.mean():.2f}")
        print(f"Median peer evaluation score: {valid_scores.median():.2f}")
        print(f"Std deviation: {valid_scores.std():.2f}")
        print(f"Min score: {valid_scores.min():.2f}")
        print(f"Max score: {valid_scores.max():.2f}")
    else:
        print("No valid peer evaluation scores calculated")


if __name__ == "__main__":
    main()

