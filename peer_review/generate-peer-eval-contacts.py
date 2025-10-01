#!/usr/bin/env python3
"""
This script is designed for the Qualtrics Team Peer Review Survey from Spring 2025.
This scripts takes the projects from Canvas with the following fields:
- name,
- canvas_user_id,
- user_id,
- login_id,
- sections,
- group_name,
- canvas_group_id,
- group_id
And creates a Qualtrics contact list with the following fields:
- Email,
- First Name,
- Last Name,
- Team Name,
- Team Member i, with i = 1, 2, ..., n (n being the largest team size)
"""

import pandas as pd
import re
import argparse

def main():
    # Parse command-line arguments
    parser = argparse.ArgumentParser(
        description='Generate Qualtrics contact list from Canvas team data'
    )
    parser.add_argument(
        'input_file',
        help='Path to the input CSV file (Canvas teams data)'
    )
    parser.add_argument(
        'output_file',
        help='Path to the output CSV file (Qualtrics contacts)'
    )
    
    args = parser.parse_args()
    
    # Read the input CSV file
    df = pd.read_csv(args.input_file)

    # Qualtrics Contact List Fields
    # - Email --> login_id
    # - First Name --> second part of name (after comma)
    # - Last Name --> first part of name (before comma)
    # - Team --> group_name
    # - Team Member i --> loop through group names and exclude current student

    # Extract first and last names from the name field
    def extract_first_name(name):
        """Extract first name (part after comma)"""
        match = re.search(r"(?<=,).+$", str(name))
        return match.group(0).strip() if match else ""

    def extract_last_name(name):
        """Extract last name (part before comma)"""
        match = re.search(r"^.+(?=,)", str(name))
        return match.group(0).strip() if match else ""

    # Create the contacts dataframe
    contacts = pd.DataFrame({
        'Email': df['login_id'],
        'First Name': df['name'].apply(extract_first_name),
        'Last Name': df['name'].apply(extract_last_name),
        'Team': df['group_name']
    })

    # Find the maximum team size (excluding self)
    team_sizes = df.groupby('group_name').size()
    max_n = team_sizes.max() - 1

    # Create columns for team members (excluding self)
    for i in range(1, max_n + 1):
        contacts[f'Team Member {i}'] = ""

    # Populate team member columns for each student
    for idx in range(len(contacts)):
        # Get current student's email and team
        current_email = contacts.loc[idx, 'Email']
        current_team = contacts.loc[idx, 'Team']
        
        # Get all team members except the current student
        team_members = df[
            (df['group_name'] == current_team) & 
            (df['login_id'] != current_email)
        ]['login_id'].tolist()
        
        # Fill in team member columns for this student
        for j, member_email in enumerate(team_members, start=1):
            contacts.loc[idx, f'Team Member {j}'] = member_email

    # Write the output CSV file
    contacts.to_csv(args.output_file, index=False)

    print(f"Successfully generated Qualtrics contacts list with {len(contacts)} students")
    print(f"Maximum team size: {max_n + 1} members")
    print(f"Output written to: {args.output_file}")


if __name__ == "__main__":
    main()

