# Peer Review Scripts

This directory contains Python scripts for managing team peer evaluations using Canvas and Qualtrics.

## Overview

These scripts automate the process of:
1. Generating Qualtrics contact lists from Canvas team data
2. Processing peer evaluation survey results and calculating grades

## Scripts

### 1. `generate-peer-eval-contacts.py`

Converts Canvas team/group data into a Qualtrics contact list format for peer evaluation surveys.

**Input:** Canvas team CSV file with fields:
- `name` - Student name (format: "Last, First")
- `canvas_user_id`
- `user_id`
- `login_id` - Student email
- `sections`
- `group_name` - Team name
- `canvas_group_id`
- `group_id`

**Output:** Qualtrics contact list CSV with fields:
- `Email` - Student email
- `First Name` - Extracted from name field
- `Last Name` - Extracted from name field
- `Team` - Team/group name
- `Team Member 1`, `Team Member 2`, ..., `Team Member N` - Emails of teammates (excluding self)

**Usage:**
```bash
python generate-peer-eval-contacts.py <input_file> <output_file>

# Example:
python generate-peer-eval-contacts.py data/CS362_S2025_Teams.csv data/qualtrics-contacts-2025.csv
```

**How it works:**
1. Reads Canvas team data
2. Determines the maximum team size
3. For each student, creates columns for all their teammates (excluding themselves)
4. Populates teammate emails so Qualtrics can send personalized survey links

---

### 2. `calculate-peer-review-grade.py`

Processes Qualtrics peer evaluation survey results and calculates peer review grades for each student.

**Survey Questions:**

The script expects a Qualtrics survey with the following structure:

**Question 1** (Likert scale questions for each team member):
- Q1_X_1: Does the member do an appropriate quantity of work?
- Q1_X_2: How about the quality of the member's work?
- Q1_X_3: Rate the member's attitude as a team player
- Q1_X_4: Rate the overall value of the member's technical contribution
- Q1_X_5: Would you want to work with this person on a project again?

**Question 2** (Point distribution):
- Q2_X_1: Divide 100 points among team members based on contribution

**Question 3** (Text answer):
- Q3: Free-form text self-evaluation (student's own reflection on their performance)

Note: The script extracts Q3 from each student's own survey response as their self-evaluation text.

**Usage:**
```bash
python calculate-peer-review-grade.py <groups_file> <survey_file> <output_file> [--plot-output <plot_file>]

# Example:
python calculate-peer-review-grade.py \
    data/CS362_S2025_Teams.csv \
    data/CS_362_001_S2025_Team_Peer_Evaluations.csv \
    data/CS_362_001_S2025_Peer_Review_Grades.csv \
    --plot-output data/peer_eval_distribution.png
```

**Arguments:**
- `groups_file` - Canvas team data CSV
- `survey_file` - Qualtrics survey results CSV
- `output_file` - Output CSV file with Name, Email, PeerEvaluationScore, Q3
- `--plot-output` - (Optional) Path for distribution visualization (default: `peer_evaluation_distribution.png`)

**How it works:**
1. Reads team sizes from Canvas data
2. Processes Qualtrics survey responses
3. For each student, aggregates peer evaluations from teammates
4. Calculates mean scores for each question (Q1_1 through Q1_5, and Q2)
5. Normalizes and shifts scores using the formulas:
   - Q1 questions (Likert scale): `(mean * 10) + 50` (normalized to ~50-100 scale)
   - Q2 (point distribution): `mean * team_size`, then shifted using a quadratic function to prevent extreme scores (clamped between 10-40, then transformed)
6. Calculates final `PeerEvaluationScore` as average of Q11-Q14 normalized scores and Q2_shifted (5 components total)
7. Extracts Q3 text response (self-evaluation) from each student's own survey submission
8. Generates a histogram comparing original vs shifted Q2 distributions
9. Outputs a simplified CSV with scores and Q3 text responses
10. Includes students from the groups file who didn't complete the survey (marked as "**NO SUBMISSION**" in Q3)

**Output Files:**
- CSV file with columns: Name, Email, PeerEvaluationScore, Q3
  - Name: Student name (Last, First format)
  - Email: Student email address
  - PeerEvaluationScore: Calculated peer evaluation score (typically 50-100 scale)
  - Q3: Self-evaluation text response from the student's own survey submission (or "**NO SUBMISSION**" if they didn't complete the survey)
- Histogram visualization comparing original vs shifted Q2 score distributions

**Summary Statistics:**
The script prints summary statistics including:
- Total students (including those who didn't submit)
- Mean, median, standard deviation of peer evaluation scores
- Minimum and maximum scores

---

## Installation

### Requirements

- Python 3.7 or higher
- Required packages (see `requirements.txt`)

### Setup

1. Create a virtual environment (recommended):
```bash
cd peer_review
python -m venv venv
source venv/bin/activate  # On macOS/Linux
# or
venv\Scripts\activate  # On Windows
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

## Workflow

### Complete Peer Evaluation Process

1. **Export team data from Canvas**
   - Navigate to your Canvas course
   - Go to Groups
   - Export group membership data as CSV

2. **Generate Qualtrics contact list**
   ```bash
   python generate-peer-eval-contacts.py \
       data/canvas_teams.csv \
       data/qualtrics_contacts.csv
   ```

3. **Import contact list to Qualtrics**
   - In Qualtrics, go to your directory
   - Import the generated CSV as a new mailing list

4. **Send peer evaluation survey**
   - Use the Qualtrics contact list to send personalized surveys
   - Each student receives teammate information via piped text

5. **Export survey results**
   - After survey closes, export results from Qualtrics as CSV
   - Include all response data

6. **Calculate peer review grades**
   ```bash
   python calculate-peer-review-grade.py \
       data/canvas_teams.csv \
       data/qualtrics_survey_results.csv \
       data/peer_review_grades.csv \
       --plot-output data/score_distribution.png
   ```
   
   Note: The script will include all students from the teams file, even if they didn't complete the survey. Non-submitters will have "**NO SUBMISSION**" in the Q3 column and NaN for PeerEvaluationScore.

7. **Review results**
   - Check the output CSV file for scores and Q3 responses
   - Review the distribution plot
   - Examine summary statistics
   - Identify students who didn't submit (marked with "**NO SUBMISSION**")

8. **Import grades to Canvas**
   - Use the PeerEvaluationScore column from the output CSV to manually enter or import peer evaluation grades
   - Review individual Q3 self-evaluation responses if needed for student feedback
   - Handle students with NaN scores (non-submitters) according to your course policy

## Data Privacy

⚠️ **Important:** These scripts handle student data. Always:
- Keep data files in a secure location (e.g., in a `data/` directory that's gitignored)
- Never commit student data to version control
- Follow your institution's data privacy policies
- Delete temporary files when done

## Troubleshooting

### Common Issues

**Issue:** "Column not found" error
- **Solution:** Verify that your input CSV files have the expected column names. Check the Canvas/Qualtrics export settings.

**Issue:** Scores seem incorrect
- **Solution:** Verify that the survey questions are properly mapped (Q1_X_1 through Q1_X_5, Q2_X_1, Q3). Check that team sizes match.

**Issue:** Empty peer evaluations or NaN scores
- **Solution:** Students who didn't complete the survey will have "**NO SUBMISSION**" in Q3 and NaN for PeerEvaluationScore. Students whose teammates didn't complete the survey will also have NaN scores. Check the summary statistics to see how many students are affected.

**Issue:** Plot doesn't generate
- **Solution:** Ensure matplotlib is installed correctly. Try running with a different output path.

## License

These scripts are part of the cs361_scripts repository. See the LICENSE file in the root directory.

## Contributing

If you find bugs or have suggestions for improvements, please open an issue or submit a pull request.

