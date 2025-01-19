from flask import Flask, request, jsonify
from flask_cors import CORS
import pandas as pd
import numpy as np


app = Flask(__name__)
CORS(app)  # Enable CORS for frontend communication

def extract_year_from_match_id(match_id):
    """
    Extract year from match ID based on the number of matches per year
    """
    matches_per_year = {
        2008: 50, 2009: 57, 2010: 60, 2011: 74, 2012: 76, 2013: 76,
        2014: 60, 2015: 59, 2016: 60, 2017: 60, 2018: 60, 2019: 60,
        2020: 60, 2021: 70, 2022: 74, 2023: 74
    }
    
    cumulative_matches = 0
    for year, matches in matches_per_year.items():
        cumulative_matches += matches
        if match_id <= cumulative_matches:
            return year
    return 2023

def get_first_half_matches(match_data, year, total_matches):
    """
    Filter matches to get only first half matches for the given year
    """
    year_matches = match_data[match_data['year'] == year]
    first_half_matches = total_matches // 2
    return year_matches[year_matches['match_id'].isin(year_matches['match_id'].unique()[:first_half_matches])]

def calculate_player_scores(match_data, team1, team2):
    """
    Calculate performance scores for players from specified teams based on first-half matches
    """
    match_data['year'] = match_data['match_id'].apply(extract_year_from_match_id)
    
    team_data = match_data[
        (match_data['batting_team'].isin([team1, team2])) |
        (match_data['bowling_team'].isin([team1, team2]))
    ]
    
    all_player_stats = pd.DataFrame()
    
    matches_per_year = {
        2008: 59, 2009: 57, 2010: 60, 2011: 74, 2012: 76, 2013: 76,
        2014: 60, 2015: 59, 2016: 60, 2017: 60, 2018: 60, 2019: 60,
        2020: 60, 2021: 70, 2022: 74, 2023: 74
    }
    
    for year in team_data['year'].unique():
        first_half_data = get_first_half_matches(team_data, year, matches_per_year[year])
        
        batting_stats = first_half_data.groupby(['batter', 'batting_team']).agg({
            'batsman_runs': 'sum',
            'match_id': 'nunique',
            'ball': 'count'
        }).reset_index()
        
        batting_stats.columns = ['player', 'team', 'total_runs', 'matches', 'balls_faced']
        batting_stats['strike_rate'] = (batting_stats['total_runs'] / batting_stats['balls_faced']) * 100
        
        bowling_stats = first_half_data.groupby(['bowler', 'bowling_team']).agg({
            'total_runs': 'sum',
            'match_id': 'nunique',
            'ball': 'count'
        }).reset_index()
        
        wickets = first_half_data[first_half_data['is_wicket'] == 1].groupby('bowler')['is_wicket'].count().reset_index()
        wickets.columns = ['bowler', 'wickets']
        
        bowling_stats = pd.merge(bowling_stats, wickets, left_on='bowler', right_on='bowler', how='left')
        bowling_stats['wickets'] = bowling_stats['wickets'].fillna(0)
        bowling_stats.columns = ['player', 'team', 'runs_conceded', 'matches', 'balls_bowled', 'wickets']
        
        bowling_stats['economy'] = (bowling_stats['runs_conceded'] / (bowling_stats['balls_bowled']/6))
        
        max_runs = batting_stats['total_runs'].max() if not batting_stats.empty else 1
        max_sr = batting_stats['strike_rate'].max() if not batting_stats.empty else 1
        
        batting_stats['batting_score'] = (
            (batting_stats['total_runs'] / max_runs) * 60 +
            (batting_stats['strike_rate'] / max_sr) * 40
        ).clip(0, 100)
        
        min_economy = bowling_stats['economy'].min() if not bowling_stats.empty else 1
        max_wickets = bowling_stats['wickets'].max() if not bowling_stats.empty else 1
        
        bowling_stats['bowling_score'] = (
            (min_economy / bowling_stats['economy']) * 50 +
            (bowling_stats['wickets'] / max_wickets) * 50
        ).clip(0, 100)
        
        year_stats = pd.merge(batting_stats, bowling_stats[['player', 'wickets', 'economy', 'bowling_score']], 
                            on='player', how='outer')
        year_stats['year'] = year
        year_stats = year_stats.fillna(0)
        
        year_stats['all_rounder_score'] = np.where(
            (year_stats['total_runs'] >= 100) & (year_stats['wickets'] >= 5),
            np.sqrt(year_stats['batting_score'] * year_stats['bowling_score']),
            0
        )
        
        all_player_stats = pd.concat([all_player_stats, year_stats])
    
    final_stats = all_player_stats.groupby('player').agg({
        'team': 'last',
        'batting_score': 'mean',
        'bowling_score': 'mean',
        'all_rounder_score': 'mean',
        'total_runs': 'mean',
        'wickets': 'mean'
    }).reset_index()
    
    def classify_player(row):
        if row['all_rounder_score'] > 50:
            return 'All-rounder'
        elif row['batting_score'] > row['bowling_score']:
            return 'Batsman'
        else:
            return 'Bowler'
    
    final_stats['role'] = final_stats.apply(classify_player, axis=1)
    return final_stats

def select_best_players(player_stats):
    """
    Select top 16 players (7 batsmen, 7 bowlers, 2 all-rounders)
    """
    top_batsmen = player_stats[player_stats['role'] == 'Batsman'].nlargest(7, 'batting_score')
    top_bowlers = player_stats[player_stats['role'] == 'Bowler'].nlargest(7, 'bowling_score')
    top_allrounders = player_stats[player_stats['role'] == 'All-rounder'].nlargest(2, 'all_rounder_score')
    
    return pd.concat([top_batsmen, top_bowlers, top_allrounders])

@app.route('/analyze-teams', methods=['POST'])
def analyze_teams():
    try:
        data = request.get_json()
        team1 = data.get('team1')
        team2 = data.get('team2')
        
        if not team1 or not team2:
            return jsonify({'error': 'Both team names are required'}), 400
            
        # Read match data - Update this path to your actual data file location
        

        file_url = r"https://drive.google.com/uc?export=download&id=1hUcdLAE2SAzuBE3CgD9CtVbI3S4VclI6"  # Replace FILE_ID with the file ID from the shareable link
        match_data = pd.read_csv(file_url)

        
        # Calculate player scores
        player_stats = calculate_player_scores(match_data, team1, team2)
        
        # Select best players
        selected_players = select_best_players(player_stats)
        
        # Convert to dictionary format grouped by role
        result = {
            'batsmen': [],
            'bowlers': [],
            'allrounders': []
        }
        
        for _, player in selected_players.iterrows():
            player_dict = {
                'name': player['player'],
                'team': player['team'],
                'battingScore': round(float(player['batting_score']), 2),
                'bowlingScore': round(float(player['bowling_score']), 2),
                'averageRuns': round(float(player['total_runs']), 2),
                'averageWickets': round(float(player['wickets']), 2)
            }
            
            if player['role'] == 'Batsman':
                result['batsmen'].append(player_dict)
            elif player['role'] == 'Bowler':
                result['bowlers'].append(player_dict)
            else:
                player_dict['allRounderScore'] = round(float(player['all_rounder_score']), 2)
                result['allrounders'].append(player_dict)
        
        return jsonify(result)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
