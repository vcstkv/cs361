#!/usr/bin/env python3
"""
Script to invite students from Canvas CSV export to a GitHub organization.
Uses the 'SIS Login ID' field (email addresses) to send invitations.
"""

import os
import sys
import pandas as pd
from github import Github, GithubException
from dotenv import load_dotenv
import time
import requests

# Load environment variables
load_dotenv()


def load_csv(csv_path):
    """Load student data from CSV file."""
    try:
        df = pd.read_csv(csv_path)
        print(f"✓ Loaded {len(df)} rows from {csv_path}")
        print(f"  Columns: {', '.join(df.columns.tolist())}")
        return df
    except FileNotFoundError:
        print(f"✗ Error: File not found: {csv_path}")
        sys.exit(1)
    except Exception as e:
        print(f"✗ Error loading CSV: {e}")
        sys.exit(1)


def get_student_emails(df):
    """
    Extract student emails from the dataframe.
    Uses the 'SIS Login ID' column from Canvas exports.
    """
    email_column = 'SIS Login ID'
    
    if email_column not in df.columns:
        print(f"\n✗ Could not find '{email_column}' column.")
        print(f"  Available columns: {', '.join(df.columns.tolist())}")
        print(f"\nPlease specify the column name that contains student emails:")
        email_column = input("Column name: ").strip()
        
        if email_column not in df.columns:
            print(f"✗ Column '{email_column}' not found in CSV")
            sys.exit(1)
    
    print(f"✓ Using column '{email_column}' for student emails")
    
    # Extract emails and filter out empty values
    emails = df[email_column].dropna().astype(str).str.strip()
    # Filter out empty values, 'nan', and the header row if it got included
    emails = [e for e in emails if e and e != 'nan' and e != '' and '@' in e]
    
    print(f"✓ Found {len(emails)} student emails")
    return emails


def invite_to_organization(github_token, org_name, emails, dry_run=False):
    """
    Invite users to the GitHub organization by email.
    
    Args:
        github_token: GitHub authentication token
        org_name: Name of the GitHub organization
        emails: List of email addresses to invite
        dry_run: If True, don't actually send invitations
    """
    success_count = 0
    already_member_count = 0
    error_count = 0
    
    print(f"\n{'[DRY RUN] ' if dry_run else ''}Inviting {len(emails)} users to {org_name}...\n")
    
    headers = {
        'Authorization': f'token {github_token}',
        'Accept': 'application/vnd.github.v3+json',
        'Content-Type': 'application/json'
    }
    
    for i, email in enumerate(emails, 1):
        try:
            if dry_run:
                print(f"  [{i}/{len(emails)}] → {email} - Would invite")
                success_count += 1
            else:
                # Use GitHub API directly for email-based invitations
                # Endpoint: POST /orgs/{org}/invitations
                url = f'https://api.github.com/orgs/{org_name}/invitations'
                payload = {
                    'email': email,
                    'role': 'direct_member'  # Can be 'direct_member', 'admin', or 'billing_manager'
                }
                
                response = requests.post(url, json=payload, headers=headers)
                
                if response.status_code == 201:
                    print(f"  [{i}/{len(emails)}] ✓ {email} - Invited successfully")
                    success_count += 1
                elif response.status_code == 422:
                    error_data = response.json()
                    error_msg = error_data.get('message', '')
                    errors = error_data.get('errors', [])
                    
                    # Check for specific error types
                    is_already_member = any('already' in str(err).lower() for err in errors) or 'already' in error_msg.lower()
                    
                    if is_already_member:
                        print(f"  [{i}/{len(emails)}] ⊙ {email} - Already invited or member")
                        already_member_count += 1
                    else:
                        # Show more detailed error info
                        if errors:
                            error_detail = errors[0].get('message', error_msg) if isinstance(errors[0], dict) else str(errors[0])
                        else:
                            error_detail = error_msg
                        print(f"  [{i}/{len(emails)}] ✗ {email} - {error_detail}")
                        error_count += 1
                elif response.status_code == 404:
                    print(f"  [{i}/{len(emails)}] ✗ {email} - Organization not found or insufficient permissions")
                    error_count += 1
                elif response.status_code == 403:
                    print(f"  [{i}/{len(emails)}] ✗ {email} - Forbidden: Check token permissions")
                    error_count += 1
                else:
                    error_msg = response.json().get('message', response.text) if response.text else f"HTTP {response.status_code}"
                    print(f"  [{i}/{len(emails)}] ✗ {email} - {error_msg}")
                    error_count += 1
                
                # Rate limiting: sleep briefly between invitations
                time.sleep(0.5)
                
        except requests.exceptions.RequestException as e:
            print(f"  [{i}/{len(emails)}] ✗ {email} - Network error: {e}")
            error_count += 1
        except Exception as e:
            print(f"  [{i}/{len(emails)}] ✗ {email} - Unexpected error: {e}")
            error_count += 1
    
    # Summary
    print(f"\n{'='*60}")
    print(f"{'DRY RUN ' if dry_run else ''}Summary:")
    print(f"  Total processed: {len(emails)}")
    print(f"  {'Would invite' if dry_run else 'Successfully invited'}: {success_count}")
    print(f"  Already members/invited: {already_member_count}")
    print(f"  Errors: {error_count}")
    print(f"{'='*60}\n")


def main():
    """Main function."""
    print("="*60)
    print("GitHub Organization Student Inviter")
    print("="*60 + "\n")
    
    # Check for required environment variables
    github_token = os.getenv('GITHUB_TOKEN')
    org_name = os.getenv('GITHUB_ORG')
    
    if not github_token:
        print("✗ Error: GITHUB_TOKEN environment variable not set")
        print("  Please create a .env file with your GitHub Personal Access Token")
        print("  Example: GITHUB_TOKEN=ghp_your_token_here")
        sys.exit(1)
    
    if not org_name:
        print("ℹ GitHub organization name not set in .env file")
        org_name = input("Enter GitHub organization name: ").strip()
        if not org_name:
            print("✗ Organization name is required")
            sys.exit(1)
    
    # Get CSV file path
    if len(sys.argv) < 2:
        print("Usage: python invite_students.py <canvas_export.csv> [--dry-run]")
        print("\nOr enter the CSV file path:")
        csv_path = input("CSV file path: ").strip()
        if not csv_path:
            print("✗ CSV file path is required")
            sys.exit(1)
    else:
        csv_path = sys.argv[1]
    
    # Check for dry-run flag
    dry_run = '--dry-run' in sys.argv or '-n' in sys.argv
    
    # Load CSV
    df = load_csv(csv_path)
    
    # Extract student emails
    emails = get_student_emails(df)
    
    if not emails:
        print("✗ No student emails found in CSV")
        sys.exit(1)
    
    # Authenticate with GitHub
    print(f"\n✓ Authenticating with GitHub...")
    try:
        github_client = Github(github_token)
        user = github_client.get_user()
        print(f"✓ Authenticated as: {user.login}")
    except Exception as e:
        print(f"✗ Authentication failed: {e}")
        sys.exit(1)
    
    # Confirm before proceeding
    if not dry_run:
        print(f"\n⚠ About to invite {len(emails)} users to '{org_name}' by email")
        confirm = input("Continue? (yes/no): ").strip().lower()
        if confirm not in ['yes', 'y']:
            print("Cancelled.")
            sys.exit(0)
    
    # Invite users
    invite_to_organization(github_token, org_name, emails, dry_run)
    
    if dry_run:
        print("ℹ This was a dry run. Use without --dry-run flag to actually send invitations.")


if __name__ == "__main__":
    main()

