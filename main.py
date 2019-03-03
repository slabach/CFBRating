# core modules
import sys, os, json, requests, re, datetime
from bs4 import BeautifulSoup

# other modules
import wikipedia


# from lxml import etree


class App:
    def __init__(self, teams_path):
        self.teamsPath = teams_path

    def get_weekly_games(self, week_num):
        
        year = 2018

        with open(self.teamsPath, "r") as t:
            teams_json = json.load(t)

        for t in teams_json:
            team = t["School"]

            if " " in team:
                team = team.replace(" ", "%20")

            if "&" in team:
                team = team.replace("&", "%26")

            if "Jose" in team:
                team = team.replace("Jose", "Jos%C3%A9")

            if week_num == 20:
                req_url = "https://api.collegefootballdata.com/games/teams?year={0}&seasonType=postseason&team={2}".format(year, week_num, team)
            else:
                req_url = "https://api.collegefootballdata.com/games/teams?year={0}&week={1}&seasonType=regular&team={2}".format(year, week_num, team)

            page_text = requests.get(req_url).text
            page_json = json.loads(page_text)

            weekly_result_path = "lib/2018/{0}/Week{1}.json".format(t["School"], week_num)

            with open(weekly_result_path, 'w') as output_file:
                json.dump(page_json, output_file, indent=2)

        print("Complete")

    def sval_calc(self, week_num):
        # region Model Values
        model_o_points_scored = 35
        model_o_yrds_rush = 6.5
        model_o_yrds_pass = 8
        model_o_yrds_total = 450
        model_o_possession_time = 35

        model_d_points_allow = 20
        model_d_yrds_rush = 4
        model_d_yrds_pass = 6
        model_d_yrds_total = 275
        model_d_possession_time = 25

        model_game_margin = 15
        model_game_penalties = 6
        model_game_turnover_margin = 1.5

        # endregion

        def opp_strength(name):

            with open(self.teamsPath, "r") as ostr:
                talent_json = json.load(ostr)

            for entry in talent_json:
                if any(entry['School'] == name for entry in talent_json):
                    
                    if name == entry['School']:
                        
                        return entry['Talent_Mod']
                else:
                    return 0.2

        with open(self.teamsPath, "r") as t:
            teams_json = json.load(t)

        for t in teams_json:
            team = t["School"]

            team_game_path = "lib/2018/{0}/Week{1}.json".format(team, week_num)

            with open(team_game_path, "r") as tm:
                game_json = json.load(tm)

            for gs in game_json:
                
                if gs["teams"][0]["school"] == team:
                    opponent = gs["teams"][1]["school"]
                    if "José" in opponent:
                        opponent = opponent.replace("José", "Jose")
                    opponent_str_mod = float(opp_strength(opponent))
                    # print(f"Team: {team}, Opp: {opponent}, Mod: {opponent_str_mod}")

                    team_o_points_scored = int(gs["teams"][0]["points"])
                    for i in gs["teams"][0]["stats"]:
                        if i['category'] == 'yardsPerRushAttempt':
                            team_o_yrds_rush = float(i["stat"])

                    for i in gs["teams"][0]["stats"]:
                        if i['category'] == 'yardsPerPass':
                            team_o_yrds_pass = float(i["stat"])

                    for i in gs["teams"][0]["stats"]:
                        if i['category'] == 'totalYards':
                            team_o_yrds_total = int(i["stat"])

                    for i in gs["teams"][0]["stats"]:
                        if i['category'] == 'possessionTime':
                            team_o_possession_time = float((i["stat"]).split(":")[0]) + \
                                                     (float((i["stat"]).split(":")[1]) / 60)

                    team_d_points_allow = int(gs["teams"][1]["points"])
                    for i in gs["teams"][1]["stats"]:
                        if i['category'] == 'yardsPerRushAttempt':
                            team_d_yrds_rush = float(i["stat"])

                    for i in gs["teams"][1]["stats"]:
                        if i['category'] == 'yardsPerPass':
                            team_d_yrds_pass = float(i["stat"])

                    for i in gs["teams"][1]["stats"]:
                        if i['category'] == 'totalYards':
                            team_d_yrds_total = int(i["stat"])

                    for i in gs["teams"][1]["stats"]:
                        if i['category'] == 'possessionTime':
                            team_d_possession_time = float((i["stat"]).split(":")[0]) + \
                                                     (float((i["stat"]).split(":")[1]) / 60)

                    team_game_margin = int(gs["teams"][0]["points"]) - int(gs["teams"][1]["points"])
                    for i in gs["teams"][1]["stats"]:
                        if i['category'] == 'totalPenaltiesYards':
                            team_game_penalties = int((i["stat"]).split("-")[0])

                    for i in gs["teams"][0]["stats"]:
                        if i['category'] == 'turnovers':
                            team_game_to = int(i["stat"])

                    for i in gs["teams"][1]["stats"]:
                        if i['category'] == 'turnovers':
                            opp_game_to = int(i["stat"])

                    team_game_turnover_margin = opp_game_to - team_game_to

                    # print(f"team: {gs['teams'][0]['school']} - time: {team_game_penalties}")

                else:
                    opponent = gs["teams"][0]["school"]
                    opponent_str_mod = float(opp_strength(opponent))
                    # print(f"Team: {team}, Opp: {opponent}, Mod: {opponent_str_mod}")

                    team_o_points_scored = int(gs["teams"][1]["points"])
                    for i in gs["teams"][1]["stats"]:
                        if i['category'] == 'yardsPerRushAttempt':
                            team_o_yrds_rush = float(i["stat"])

                    for i in gs["teams"][1]["stats"]:
                        if i['category'] == 'yardsPerPass':
                            team_o_yrds_pass = float(i["stat"])

                    for i in gs["teams"][1]["stats"]:
                        if i['category'] == 'totalYards':
                            team_o_yrds_total = int(i["stat"])

                    for i in gs["teams"][1]["stats"]:
                        if i['category'] == 'possessionTime':
                            team_o_possession_time = float((i["stat"]).split(":")[0]) + \
                                                     (float((i["stat"]).split(":")[1]) / 60)

                    team_d_points_allow = int(gs["teams"][0]["points"])
                    for i in gs["teams"][0]["stats"]:
                        if i['category'] == 'yardsPerRushAttempt':
                            if float(i["stat"]) == 0:
                                team_d_yrds_rush = 1.0
                            else:
                                team_d_yrds_rush = float(i["stat"])

                    for i in gs["teams"][0]["stats"]:
                        if i['category'] == 'yardsPerPass':
                            team_d_yrds_pass = float(i["stat"])

                    for i in gs["teams"][0]["stats"]:
                        if i['category'] == 'totalYards':
                            team_d_yrds_total = int(i["stat"])

                    for i in gs["teams"][0]["stats"]:
                        if i['category'] == 'possessionTime':
                            team_d_possession_time = float((i["stat"]).split(":")[0]) + \
                                                     (float((i["stat"]).split(":")[1]) / 60)

                    team_game_margin = int(gs["teams"][1]["points"]) - int(gs["teams"][0]["points"])
                    for i in gs["teams"][1]["stats"]:
                        if i['category'] == 'totalPenaltiesYards':
                            team_game_penalties = int((i["stat"]).split("-")[0])

                    for i in gs["teams"][1]["stats"]:
                        if i['category'] == 'turnovers':
                            team_game_to = int(i["stat"])

                    for i in gs["teams"][0]["stats"]:
                        if i['category'] == 'turnovers':
                            opp_game_to = int(i["stat"])

                    team_game_turnover_margin = opp_game_to - team_game_to

                    # print(f"team: {gs['teams'][1]['school']} - time: {team_game_penalties}")

                # region offense calculations
                if team_o_points_scored == 0:
                    o_sval_points = 0
                else:
                    o_sval_points = (.36 * (team_o_points_scored / model_o_points_scored))
                o_sval_ypr = (.18 * (team_o_yrds_rush / model_o_yrds_rush))
                o_sval_ypp = (.18 * (team_o_yrds_pass / model_o_yrds_pass))
                o_sval_yd_total = (.18 * (team_o_yrds_total / model_o_yrds_total))
                o_sval_possession = (.1 * (team_o_possession_time / model_o_possession_time))

                if (o_sval_points + o_sval_ypr + o_sval_ypp + o_sval_yd_total + o_sval_possession) > 1:
                    o_sval = 1.0
                else:
                    o_sval = (o_sval_points + o_sval_ypr + o_sval_ypp + o_sval_yd_total + o_sval_possession)
                # endregion

                # region defense calculations
                if team_d_points_allow == 0:
                    d_sval_points_allowed = (.4 * 1)
                else:
                    d_sval_points_allowed = (.4 * (1 / (team_d_points_allow / model_d_points_allow)))

                try:
                    if team_d_yrds_rush <= 0:
                        d_sval_ypr = (.15 * 1.0)
                    else:
                        d_sval_ypr = (.15 * (1 / (team_d_yrds_rush / model_d_yrds_rush)))
                except ZeroDivisionError:
                    d_sval_ypr = (.15 * 1.0)

                try:
                    d_sval_ypp = (.15 * (1 / (team_d_yrds_pass / model_d_yrds_pass)))
                except ZeroDivisionError:
                    d_sval_ypp = (.15 * 1.0)

                try:
                    if team_d_yrds_total <= 0:
                        d_sval_yd_given = (.15 * 1.0)
                    else:
                        d_sval_yd_given = (.2 * (1 / (team_d_yrds_total / model_d_yrds_total)))
                except ZeroDivisionError:
                    d_sval_yd_given = (.2 * 1.0)

                if team_d_possession_time < model_d_possession_time:
                    d_sval_pos_time_allowed = (.1 * (model_d_possession_time / team_d_possession_time))
                else:
                    d_sval_pos_time_allowed = (.1 * (1 / (team_d_possession_time / model_d_possession_time)))

                if (d_sval_points_allowed + d_sval_ypr + d_sval_ypp + d_sval_yd_given + d_sval_pos_time_allowed) > 1:
                    d_sval = 1.0
                else:
                    d_sval = (d_sval_points_allowed + d_sval_ypr + d_sval_ypp + d_sval_yd_given + d_sval_pos_time_allowed)
                # endregion

                # region misc calculations
                if (.2 * (team_game_margin / model_game_margin)) > 0.4:
                    m_sval_margin = 0.4
                elif (.2 * (team_game_margin / model_game_margin)) < -0.4:
                    m_sval_margin = -0.4
                else:
                    m_sval_margin = (.2 * (team_game_margin / model_game_margin))

                if team_game_penalties == 0:
                    m_sval_penalties = (.05 * 1)
                else:
                    m_sval_penalties = (.05 * (1 / (team_game_penalties / model_game_penalties)))

                if team_game_turnover_margin > 1:
                    m_sval_turnovers = (.1 * (.5 * (team_game_turnover_margin / model_game_turnover_margin)))
                elif team_game_turnover_margin == 1:
                    m_sval_turnovers = (.1 * 1)
                else:
                    m_sval_turnovers = (.1 * ((team_game_turnover_margin / model_game_turnover_margin) - 1))

                if (opponent_str_mod < 0.8) and week_num <= 3:
                    opponent_str = (.65 * 0)
                else:
                    opponent_str = (.65 * opponent_str_mod)

                if (opponent_str + m_sval_margin + m_sval_penalties + m_sval_turnovers) > 1:
                    m_sval = 1.0
                else:
                    m_sval = (opponent_str + m_sval_margin + m_sval_penalties + m_sval_turnovers)
                # endregion

                if ((.4 * o_sval) + (.4 * d_sval) + (.2 * m_sval)) > 1:
                    sval = 1.0000
                else:
                    sval = ((.4 * o_sval) + (.4 * d_sval) + (.2 * m_sval))

                key_var = "Week" + str(week_num)
                t['S-Val-History'][key_var] = sval

                acm_sval = 0.0
                i = 1
                
                while i <= week_num:
                    key_variable = "Week" + str(i)

                    if key_variable in t['S-Val-History']:
                        acm_sval = acm_sval + t['S-Val-History'][key_variable]
                        
                        i = i + 1
                    else:
                        i = i + 1

                t['S-Val'] = (acm_sval / len(t['S-Val-History']))
                print_sval = (acm_sval / len(t['S-Val-History']))

                # print(len(t['S-Val-History']))
                print(f"{team}, {print_sval}, {o_sval}, {d_sval}, {m_sval}")

        with open("lib/2018/output.json", "w") as output_file:
            json.dump(teams_json, output_file, indent=2)

    # region old code
    # def create_file_structure(self):
    #     with open(self.teamsPath, "r") as t:
    #         teams_json = json.load(t)
    #
    #     for t in teams_json:
    #         path = "lib/2018/"+t["School"]
    #
    #         try:
    #             os.mkdir(path)
    #         except OSError:
    #             print ("Creation of the directory %s failed" % path)
    #         else:
    #             print ("Successfully created the directory %s " % path)
    #
    #     print('Completed')
    #
    # def get_school_conferences(self):
    #     with open(self.teamsPath, "r") as t:
    #         teams_json = json.load(t)
    #
    #     for t in teams_json:
    #         # if str(t["School"]) == "Purdue":
    #         search_string = str(t["School"]+ " " + t["Mascot"] + " football")
    #         wiki_search = wikipedia.search(search_string)
    #         wiki_page = wikipedia.page(wiki_search[0])
    #         wiki_url = wiki_page.url
    #         page_text = requests.get(wiki_url).text
    #         req = BeautifulSoup(page_text, 'lxml')
    #
    #         infobox = req.find('table', {'class': 'infobox'})
    #         conferenceHTag = infobox.find('th', string='Conference')
    #         conferenceNameTag = conferenceHTag.find_next_sibling('td').text
    #
    #         t['Conference'] = conferenceNameTag
    #
    #     with open("CFBRating/lib/output.json", 'w') as output_file:
    #         json.dump(teams_json, output_file)
    #
    #     print('Complete')
    #
    # def update_teamsjson(self):
    #     with open(self.teamsPath, "r") as t:
    #         teams_json = json.load(t)
    #
    #     # def json_name(name):
    #     #     with open("lib/talentMod.json", "r") as tm:
    #     #         talent_json = json.load(tm)
    #
    #     #     for entry in talent_json:
    #     #         if name == entry['Team']:
    #     #             print(f"School: {entry['Team']}, Talent Mod: {entry['TalentMod']}")
    #     #             return entry['TalentMod']
    #
    #     for t in teams_json:
    #         school_name = t['School']
    #
    #         t['S-Val-History'] = {}
    #         t['S-Val'] = 0.0
    #
    #     with open("lib/2018/output.json", 'w') as output_file:
    #         json.dump(teams_json, output_file, indent=2)
    #
    #     print('Complete')
    # endregion


def main():
    # now = datetime.datetime.now()
    # year = now.year
    week_number = 21

    a = App("lib/2018/teams-fbs.json")
    # a.get_weekly_games(week_number)
    a.sval_calc(week_number)
    # a.update_teamsjson()


if __name__ == "__main__":
    main()
