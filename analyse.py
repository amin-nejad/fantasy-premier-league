"This file generates data by GameWeek for a given League ID"

import json
from pathlib import Path
import requests
import fire
import pandas as pd

FPL_URL = "https://fantasy.premierleague.com/api/"
LOGIN_URL = "https://users.premierleague.com/accounts/login/"
USER_SUMMARY_SUBURL = "element-summary/"
LEAGUE_CLASSIC_STANDING_SUBURL = "leagues-classic/"
LEAGUE_H2H_STANDING_SUBURL = "leagues-h2h/"
TEAM_ENTRY_SUBURL = "entry/"
PLAYERS_INFO_SUBURL = "bootstrap-static/"
PLAYERS_INFO_FILENAME = "all_players_info.json"
USERNAME = "fantasy@netmail3.net"
PASSWORD = "FPLshow#123"

USER_SUMMARY_URL = FPL_URL + USER_SUMMARY_SUBURL
PLAYERS_INFO_URL = FPL_URL + PLAYERS_INFO_SUBURL
START_PAGE = 1

Path("output").mkdir(parents=True, exist_ok=True)


def get_session(username, password):
    """Open and return session with FPL"""
    payload = {
        "login": username,
        "password": password,
        "redirect_uri": "https://fantasy.premierleague.com/",
        "app": "plfpl-web",
    }
    session = requests.session()
    session.post(LOGIN_URL, data=payload)
    return session


def get_players_data(session):
    """Dump all player info as json file"""
    data = session.get(PLAYERS_INFO_URL)
    json_data = data.json()
    with open(PLAYERS_INFO_FILENAME, "w") as outfile:
        json.dump(json_data, outfile)


def get_user_ids(session, league_id, league_standing_url):
    """Get ID, team name and player first name for all players in league"""
    entry_ids, names, team_names = [], [], []
    page = START_PAGE
    while True:
        league_url = (
            league_standing_url
            + str(league_id)
            + "/standings/"
            + "?page_new_entries=1&page_standings="
            + str(page)
            + "&phase=1"
        )
        response = session.get(league_url)
        json_data = response.json()
        league_name = json_data["league"]["name"]
        managers = json_data["standings"]["results"]

        if not managers:
            break
        for player in managers:
            entry_ids.append(player["entry"])
            team_names.append(player["entry_name"])
            names.append(player["player_name"].split(" ", 1)[0])
        page += 1

    print("League name:", league_name)
    print("Total managers:", len(entry_ids))

    return entry_ids, names, team_names


def get_players_picked_for_entry(session, entry_id, gw_number):
    """Return player IDs, captain IDs, and points for each player in the league for the given GW"""
    event_suburl = "event/" + str(gw_number) + "/picks/"
    player_gw_url = FPL_URL + TEAM_ENTRY_SUBURL + str(entry_id) + "/" + event_suburl
    response = session.get(player_gw_url)
    json_data = response.json()
    points = json_data["entry_history"]["total_points"]

    try:
        picks = json_data["picks"]
    except:
        if json_data["detail"]:
            print("Entry_ID " + str(entry_id) + " has no info for gameweek " + str(gw_number))
        return None, None, None
    elements = []
    captain_id = 1
    for pick in picks:
        elements.append(pick["element"])
        if pick["is_captain"]:
            captain_id = pick["element"]

    return elements, captain_id, points


def main(league_id=339021, max_game_week=29, head_to_head=False):
    """Main function which creates CSV files for points, players and captains"""

    session = get_session(USERNAME, PASSWORD)
    get_players_data(session)
    player_names, pl_team_names, player_id_to_pl_team_name = {}, {}, {}

    with open(PLAYERS_INFO_FILENAME) as json_data:
        all_player_ids = json.load(json_data)

    # GET PLAYER NAMES AND TEAM CODES
    for element in all_player_ids["elements"]:
        player_names[element["id"]] = (element["web_name"], element["team_code"])

    # GET CLUB NAMES
    for team in all_player_ids["teams"]:
        pl_team_names[team["code"]] = team["short_name"]

    # CREATE DICTIONARY TO LINK PLAYER ID TO CLUB NAME
    for id_num in list(player_names):
        player_id_to_pl_team_name[id_num] = pl_team_names[player_names[id_num][1]]

    # DIFFERENT URL DEPENDING ON H2H LEAGUE OR CLASSIC LEAGUE
    if head_to_head:
        league_standing_url = FPL_URL + LEAGUE_H2H_STANDING_SUBURL
    else:
        league_standing_url = FPL_URL + LEAGUE_CLASSIC_STANDING_SUBURL

    # GET ENTRY IDS, NAMES AND TEAM NAMES FOR EVERYONE IN LEAGUE
    entry_ids, names, team_names = get_user_ids(session, league_id, league_standing_url)
    players, captains, points = {}, {}, {}

    # LOOP THROUGH RESULTS FOR EVERY GAME WEEK
    for gw_number in range(1, max_game_week + 1):
        players_gw, captains_gw = {}, {}
        points_gw = []
        for entry in entry_ids:
            elements, captain_id, num_points = get_players_picked_for_entry(
                session, entry, gw_number
            )
            points_gw.append(num_points)
            if not elements:
                continue
            for element in elements:
                if element in players_gw:
                    players_gw[element] += 1
                else:
                    players_gw[element] = 1

            if captain_id in captains_gw:
                captains_gw[captain_id] += 1
            else:
                captains_gw[captain_id] = 1

        if gw_number > 1:
            for element in players[gw_number - 1]:
                if element in players_gw:
                    players_gw[element] += players[gw_number - 1][element]
                else:
                    players_gw[element] = players[gw_number - 1][element]

            for element in captains[gw_number - 1]:
                if element in captains_gw:
                    captains_gw[element] += captains[gw_number - 1][element]
                else:
                    captains_gw[element] = captains[gw_number - 1][element]

        players[gw_number] = players_gw
        captains[gw_number] = captains_gw
        points[gw_number] = points_gw


    # OUTPUT CSV FOR POINTS BY GAMEWEEK
    points = pd.DataFrame(points)
    points.insert(0, "Team", team_names)
    points.insert(0, "Name", names)
    points.to_csv("output/points_" + str(league_id) + ".csv", index=False)

    # ALL PLAYERS
    all_player_ids = []
    for i in players:
        all_player_ids.extend(list(players[i]))
    all_player_ids = list(set(all_player_ids))
    print("Different number of players:", len(all_player_ids))
    all_player_names = []
    all_player_clubs = []
    for id_num in all_player_ids:
        all_player_names.append(player_names[id_num][0])
        all_player_clubs.append(player_id_to_pl_team_name[id_num])

    # OUTPUT CSV FOR PLAYER PICKS BY GAMEWEEK
    players_dict = {}
    for game_week in list(players):
        player_counts = []
        for player in all_player_ids:
            if player in list(players[game_week]):
                player_counts.append(players[game_week][player])
            else:
                player_counts.append(0)
        players_dict[game_week] = player_counts

    players_df = pd.DataFrame(players_dict)
    players_df.insert(0, "Club", all_player_clubs)
    players_df.insert(0, "Name", all_player_names)
    players_df.to_csv("output/players_" + str(league_id) + ".csv", index=False)

    # OUTPUT CSV FOR CAPTAINS BY GAMEWEEK
    captains_dict = {}
    for game_week in list(captains):
        captain_counts = []
        for player in all_player_ids:
            if player in list(captains[game_week]):
                captain_counts.append(captains[game_week][player])
            else:
                captain_counts.append(0)
        captains_dict[game_week] = captain_counts

    captains_df = pd.DataFrame(captains_dict)
    captains_df.insert(0, "Club", all_player_clubs)
    captains_df.insert(0, "Name", all_player_names)
    captains_df.to_csv("output/captains_" + str(league_id) + ".csv", index=False)


if __name__ == "__main__":
    fire.Fire(main)
