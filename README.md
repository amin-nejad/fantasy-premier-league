# FPL League Results

This repository is used to produce results from Leagues that you are part of that can be converted to Bar Chart Races from [Flourish](https://flourish.studio/). Currently this repo produces 3 CSV files:

  1. **Points**: a matrix of number of teams in the league by the number of game weeks where each cell is the number of points that team has cumulatively achieved by that game week
  2. **Players**: a matrix of number of all players by the number of game weeks where each cell is the number of times that player has been cumulatively selected by that game week
  3. **Captains**: a matrix of number of all players by the number of game weeks where each cell is the number of times that player has been cumulatively captained by that game week
  
  ## Usage
  
  ### Create CSVs
  
  This utiliy can be used from the command line as such:
  
  ```bash
  python analyse.py --league_id=696380 --max_game_week=30 --head_to_head=False
  ```
  
  where `league_id` is the ID of the league you want to analyse, `max_game_week` is the maximum game week you want this analysis to go up to and `head_to_head` is determines whether the league is a H2H league or a classic league. (If you're not sure, it's probably a classic league). To find out your `league_id`, go to https://fantasy.premierleague.com/leagues and click on the league you want to analyse. The URL should look something like https://fantasy.premierleague.com/leagues/339021/standings/c. Your `league_id` is the number in the URL (339021 in this case)
 
 Running this command should create the 3 CSV files in an `output` folder with the `league_id` in the name of the CSV file:
 
  - `points_339021.csv`
  - `players_339021.csv`
  - `captains_339021.csv`
