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
7. Merges results with gradebook
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


### Question 2
# X goes from 1 to 4, 1 is self, 2-4 are team members

# Does the member do an appropriate quantity of work?
# labels[,Q2_X_1]

# How about the quality of the member’s work?
# labels[,Q2_X_2]

# Rate the member’s attitude as a team player (eager to do assigned work, communicated with others, kept appointments, etc.).
# labels[,Q2_X_3]

# Rate the overall value of the member’s technical contribution.
# labels[,Q2_X_4]

# Would you want to work with this person on a project again?
# labels[,Q2_X_5]

### Question 3
# Take 100 points, and divide them among the N team members, including yourself. Give points based on your opinion of what proportion of the credit each member deserves. You may consider quality and quantity of contributions, team-player attitude, and/or any aspects that you feel are relevant. You must give yourself at least 100/N points, whether you honestly feel you deserve them or not. (This is to avoid an unrealistic “self-incrimination” requirement.)
# X goes from 1 to 4, 1 is self, 2-4 are team members
# labels[,Q3_X]


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
        'gradebook_file',
        help='Path to the gradebook CSV file'
    )
    parser.add_argument(
        'output_file',
        help='Path for the output peer review grades CSV file'
    )
    parser.add_argument(
        'gradebook_output_file',
        help='Path for the output gradebook CSV file with peer review scores'
    )
    parser.add_argument(
        '--plot-output',
        default='peer_evaluation_distribution.png',
        help='Path for the distribution plot (default: peer_evaluation_distribution.png)'
    )
    
    args = parser.parse_args()
    
    # Read team sizes
    team_sizes = pd.read_csv(args.groups_file)
    team_sizes = team_sizes.groupby('group_name').size().reset_index(name='n')
    team_sizes.rename(columns={'group_name': 'Team'}, inplace=True)
    
    # Read survey data
    dt = pd.read_csv(args.survey_file)
    
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
    output['Q21'] = [[] for _ in range(len(output))]
    output['Q22'] = [[] for _ in range(len(output))]
    output['Q23'] = [[] for _ in range(len(output))]
    output['Q24'] = [[] for _ in range(len(output))]
    output['Q25'] = [[] for _ in range(len(output))]
    output['Q3'] = [[] for _ in range(len(output))]
    
    # Process each student's peer evaluations
    for i in range(len(output)):
        team = output.loc[i, 'Team']
        email = output.loc[i, 'Email']
        
        # Get all evaluations from teammates (excluding self)
        results = dt[(dt['Team'] == team) & (dt['RecipientEmail'] != email)].copy()
        
        if len(results) == 0:
            # If no results, leave lists empty (will become NA)
            continue
        
        q21, q22, q23, q24, q25, q3 = [], [], [], [], [], []
        
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
                q21.append(np.nan)
                q22.append(np.nan)
                q23.append(np.nan)
                q24.append(np.nan)
                q25.append(np.nan)
                q3.append(np.nan)
                continue
            
            # Extract the responses
            q21.append(result_row.get(f'Q2_{x}_1', np.nan))
            q22.append(result_row.get(f'Q2_{x}_2', np.nan))
            q23.append(result_row.get(f'Q2_{x}_3', np.nan))
            q24.append(result_row.get(f'Q2_{x}_4', np.nan))
            q25.append(result_row.get(f'Q2_{x}_5', np.nan))
            q3.append(result_row.get(f'Q3_{x}', np.nan))
        
        output.at[i, 'Q21'] = q21
        output.at[i, 'Q22'] = q22
        output.at[i, 'Q23'] = q23
        output.at[i, 'Q24'] = q24
        output.at[i, 'Q25'] = q25
        output.at[i, 'Q3'] = q3
    
    # Calculate means for each question
    def calculate_mean(values_list):
        """Calculate mean of numeric values in a list, ignoring NaN"""
        if not values_list or all(pd.isna(v) for v in values_list):
            return np.nan
        numeric_values = [float(v) for v in values_list if pd.notna(v) and v != '']
        if not numeric_values:
            return np.nan
        return np.mean(numeric_values)
    
    output['Q21_mean'] = output['Q21'].apply(calculate_mean)
    output['Q22_mean'] = output['Q22'].apply(calculate_mean)
    output['Q23_mean'] = output['Q23'].apply(calculate_mean)
    output['Q24_mean'] = output['Q24'].apply(calculate_mean)
    output['Q25_mean'] = output['Q25'].apply(calculate_mean)
    output['Q3_mean'] = output['Q3'].apply(calculate_mean)
    
    # Normalize scores
    output['Q21_normalized'] = (output['Q21_mean'] * 10) + 50
    output['Q22_normalized'] = (output['Q22_mean'] * 10) + 50
    output['Q23_normalized'] = (output['Q23_mean'] * 10) + 50
    output['Q24_normalized'] = (output['Q24_mean'] * 10) + 50
    output['Q25_normalized'] = (output['Q25_mean'] * 10) + 50
    output['Q3_normalized'] = output['Q3_mean'] * output['n']
    
    # Shift Q3 scores
    output['Q3_shifted'] = output['Q3_normalized'] / 5
    output.loc[output['Q3_shifted'] < 10, 'Q3_shifted'] = 10
    output.loc[output['Q3_shifted'] > 40, 'Q3_shifted'] = 40
    output['Q3_shifted'] = (0.65 + (0.0225 * output['Q3_shifted']) - 
                            (0.00025 * output['Q3_shifted'] ** 2)) * 100
    
    # Calculate final peer evaluation score
    output['PeerEvaluationScore'] = (
        output['Q21_normalized'] + 
        output['Q22_normalized'] + 
        output['Q23_normalized'] + 
        output['Q24_normalized'] + 
        output['Q3_shifted']
    ) / 5
    
    # Save output
    output.to_csv(args.output_file, index=False)
    print(f"Peer review grades saved to: {args.output_file}")
    
    # Create visualization
    fig, ax = plt.subplots(figsize=(10, 6))
    
    # Plot histograms
    output['Q3_normalized'].dropna().hist(
        bins=20, alpha=0.5, label='Original', color='#4285F4', ax=ax
    )
    output['Q3_shifted'].dropna().hist(
        bins=20, alpha=0.5, label='Shifted', color='#DB4437', ax=ax
    )
    
    ax.set_xlabel('Peer Evaluation Score', fontweight='bold')
    ax.set_ylabel('Count', fontweight='bold')
    ax.set_title('Distribution of Peer Evaluation Scores\nOriginal vs Shifted (min = 50) distribution', 
                 fontweight='bold')
    ax.legend(loc='upper right')
    ax.text(0.5, -0.15, 'Data from Qualtrics Team Peer Review Survey',
            transform=ax.transAxes, ha='center', fontsize=9, style='italic')
    
    plt.tight_layout()
    plt.savefig(args.plot_output, dpi=300, bbox_inches='tight')
    print(f"Distribution plot saved to: {args.plot_output}")
    plt.close()
    
    # Merge with gradebook
    gradebook = pd.read_csv(args.gradebook_file)
    
    output['SIS Login ID'] = output['Email']
    
    # Merge peer evaluation scores into gradebook
    gradebook = gradebook.merge(
        output[['SIS Login ID', 'PeerEvaluationScore']],
        on='SIS Login ID',
        how='left'
    )
    
    # Find the Project Peer-Evaluation column (might have different ID)
    peer_eval_col = None
    for col in gradebook.columns:
        if 'Project Peer-Evaluation' in col:
            peer_eval_col = col
            break
    
    if peer_eval_col is None:
        # If column doesn't exist, create it
        peer_eval_col = 'Project Peer-Evaluation (10042163)'
        gradebook[peer_eval_col] = gradebook['PeerEvaluationScore']
    else:
        gradebook[peer_eval_col] = gradebook['PeerEvaluationScore']
    
    gradebook.drop(columns=['PeerEvaluationScore'], inplace=True)
    
    # Set default score of 60 for students with no peer evaluation
    gradebook[peer_eval_col].fillna(60, inplace=True)
    
    # Save gradebook
    gradebook.to_csv(args.gradebook_output_file, index=False)
    print(f"Updated gradebook saved to: {args.gradebook_output_file}")
    
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

