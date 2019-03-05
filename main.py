# core modules
import sys, os, json, requests, re, datetime, statistics
from bs4 import BeautifulSoup

# other modules
import wikipedia
import numpy as np


class App:
    def __init__(self, teams_path, output_path, cur_year, week_num):
        self.teamsPath = teams_path
        self.output_path = output_path
        self.cur_year = cur_year
        self.week_num = week_num
        self.model_o_points_scored = 35
        self.model_o_yrds_rush = 6.5
        self.model_o_yrds_pass = 8
        self.model_o_yrds_total = 450
        self.model_o_possession_time = 35

        self.model_d_points_allow = 20
        self.model_d_yrds_rush = 4
        self.model_d_yrds_pass = 6
        self.model_d_yrds_total = 275
        self.model_d_possession_time = 25

        self.model_game_margin = 15
        self.model_game_penalties = 6
        self.model_game_turnover_margin = 1.5

    def get_weekly_games(self):

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

            if self.week_num == 20:
                req_url = "https://api.collegefootballdata.com/games/teams?year={0}&seasonType=postseason&team={2}".format(
                    self.cur_year, self.week_num, team)
            else:
                req_url = "https://api.collegefootballdata.com/games/teams?year={0}&week={1}&seasonType=regular&team={2}".format(
                    self.cur_year, self.week_num, team)

            page_text = requests.get(req_url).text
            page_json = json.loads(page_text)

            weekly_result_path = "lib/2018/{0}/Week{1}.json".format(t["School"], self.week_num)

            with open(weekly_result_path, 'w') as output_file:
                json.dump(page_json, output_file, indent=2)

        print("Complete")

    def recalc_talent_mod(self):
        with open(self.output_path, "r") as t:
            teams_json = json.load(t)

        max_sval = max(x["S-Val"] for x in teams_json)

        for t in teams_json:
            perc_from_top = (t['S-Val'] / max_sval)
            # updated_talent_mod = 0.0
            multiplier = 0.0
            power5_conf = ['SEC', 'Pac-12', 'Big 12', 'ACC', 'Big Ten']

            #region set multiplier
            if perc_from_top == 1:
                multiplier = 2.0
            elif 0.950 <= perc_from_top < 1.000:
                multiplier = 1.950
            elif 0.925 <= perc_from_top < 0.950:
                multiplier = 1.90
            elif 0.920 <= perc_from_top < 0.925:
                multiplier = 1.85
            elif 0.910 <= perc_from_top < 0.920:
                multiplier = 1.8
            elif 0.900 <= perc_from_top < 0.910:
                multiplier = 1.75
            elif 0.890 <= perc_from_top < 0.900:
                multiplier = 1.7
            elif 0.880 <= perc_from_top < 0.890:
                multiplier = 1.65
            elif 0.870 <= perc_from_top < 0.880:
                multiplier = 1.55
            elif 0.850 <= perc_from_top < 0.870:
                multiplier = 1.45
            elif 0.750 <= perc_from_top < 0.850:
                multiplier = 1.35
            elif 0.690 <= perc_from_top < 0.750:
                multiplier = 1.30
            elif 0.05 <= perc_from_top < 0.690:
                multiplier = 1.25
            else:
                pass
            #endregion

            if multiplier != 0:
                if self.week_num <= 2:
                    updated_talent_mod = (perc_from_top * multiplier)
                else:
                    updated_talent_mod = (((perc_from_top * multiplier) + t['Talent_Mod']) / 2)
                # updated_talent_mod = (perc_from_top * multiplier)
            else:
                updated_talent_mod = t['Talent_Mod']

            if (t['Conference'] not in power5_conf) and (t['School'] != 'Notre Dame'):
                updated_talent_mod = updated_talent_mod * .65

            t['Talent_Mod'] = updated_talent_mod

        with open(self.output_path, "w") as output_file:
            json.dump(teams_json, output_file, indent=2)

        print("Complete")

    def sval_calc(self):

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

            team_game_path = "lib/2018/{0}/Week{1}.json".format(team, self.week_num)

            with open(team_game_path, "r") as tm:
                game_json = json.load(tm)

            for gs in game_json:

                # region set game stats
                # if team is first team in game file
                if gs["teams"][0]["school"] == team:
                    opponent = gs["teams"][1]["school"]
                    if "José" in opponent:
                        opponent = opponent.replace("José", "Jose")

                    opponent_str_mod = float(opp_strength(opponent))

                    # set offensive values
                    team_o_points_scored = int(gs["teams"][0]["points"])
                    for i in gs["teams"][0]["stats"]:
                        if i['category'] == 'yardsPerRushAttempt':
                            team_o_yrds_rush = float(i["stat"])

                        if i['category'] == 'yardsPerPass':
                            team_o_yrds_pass = float(i["stat"])

                        if i['category'] == 'totalYards':
                            team_o_yrds_total = int(i["stat"])

                        if i['category'] == 'possessionTime':
                            team_o_possession_time = float((i["stat"]).split(":")[0]) + \
                                                     (float((i["stat"]).split(":")[1]) / 60)

                    # set defensive values
                    team_d_points_allow = int(gs["teams"][1]["points"])
                    for i in gs["teams"][1]["stats"]:
                        if i['category'] == 'yardsPerRushAttempt':
                            if float(i["stat"]) == 0:
                                team_d_yrds_rush = 1.0
                            else:
                                team_d_yrds_rush = float(i["stat"])

                        if i['category'] == 'yardsPerPass':
                            team_d_yrds_pass = float(i["stat"])

                        if i['category'] == 'totalYards':
                            team_d_yrds_total = int(i["stat"])

                        if i['category'] == 'possessionTime':
                            team_d_possession_time = float((i["stat"]).split(":")[0]) + \
                                                     (float((i["stat"]).split(":")[1]) / 60)

                    # set team values
                    team_game_margin = int(gs["teams"][0]["points"]) - int(gs["teams"][1]["points"])
                    for i in gs["teams"][1]["stats"]:
                        if i['category'] == 'turnovers':
                            opp_game_to = int(i["stat"])

                    for i in gs["teams"][0]["stats"]:
                        if i['category'] == 'turnovers':
                            team_game_to = int(i["stat"])

                        if i['category'] == 'totalPenaltiesYards':
                            team_game_penalties = int((i["stat"]).split("-")[0])

                    team_game_turnover_margin = opp_game_to - team_game_to

                    # print(f"team: {gs['teams'][0]['school']} - time: {team_game_penalties}")

                # if team is second team in game file
                else:
                    opponent = gs["teams"][0]["school"]
                    opponent_str_mod = float(opp_strength(opponent))
                    # print(f"Team: {team}, Opp: {opponent}, Mod: {opponent_str_mod}")

                    # set offensive stats
                    team_o_points_scored = int(gs["teams"][1]["points"])
                    for i in gs["teams"][1]["stats"]:
                        if i['category'] == 'yardsPerRushAttempt':
                            team_o_yrds_rush = float(i["stat"])

                        if i['category'] == 'yardsPerPass':
                            team_o_yrds_pass = float(i["stat"])

                        if i['category'] == 'totalYards':
                            team_o_yrds_total = int(i["stat"])

                        if i['category'] == 'possessionTime':
                            team_o_possession_time = float((i["stat"]).split(":")[0]) + \
                                                     (float((i["stat"]).split(":")[1]) / 60)

                    # set defensive stats
                    team_d_points_allow = int(gs["teams"][0]["points"])
                    for i in gs["teams"][0]["stats"]:
                        if i['category'] == 'yardsPerRushAttempt':
                            if float(i["stat"]) == 0:
                                team_d_yrds_rush = 1.0
                            else:
                                team_d_yrds_rush = float(i["stat"])

                        if i['category'] == 'yardsPerPass':
                            team_d_yrds_pass = float(i["stat"])

                        if i['category'] == 'totalYards':
                            team_d_yrds_total = int(i["stat"])

                        if i['category'] == 'possessionTime':
                            team_d_possession_time = float((i["stat"]).split(":")[0]) + \
                                                     (float((i["stat"]).split(":")[1]) / 60)

                    # set team stats
                    team_game_margin = int(gs["teams"][1]["points"]) - int(gs["teams"][0]["points"])
                    for i in gs["teams"][1]["stats"]:
                        if i['category'] == 'totalPenaltiesYards':
                            team_game_penalties = int((i["stat"]).split("-")[0])

                        if i['category'] == 'turnovers':
                            team_game_to = int(i["stat"])

                    for i in gs["teams"][0]["stats"]:
                        if i['category'] == 'turnovers':
                            opp_game_to = int(i["stat"])

                    team_game_turnover_margin = opp_game_to - team_game_to
                # endregion

                # region offense calculations
                if team_o_points_scored == 0:
                    o_sval_points = 0
                else:
                    o_sval_points = (.36 * (team_o_points_scored / self.model_o_points_scored))

                o_sval_ypr = (.18 * (team_o_yrds_rush / self.model_o_yrds_rush))
                o_sval_ypp = (.18 * (team_o_yrds_pass / self.model_o_yrds_pass))
                o_sval_yd_total = (.18 * (team_o_yrds_total / self.model_o_yrds_total))
                o_sval_possession = (.1 * (team_o_possession_time / self.model_o_possession_time))

                if (o_sval_points + o_sval_ypr + o_sval_ypp + o_sval_yd_total + o_sval_possession) > 1:
                    o_sval = 1.0
                else:
                    o_sval = (o_sval_points + o_sval_ypr + o_sval_ypp + o_sval_yd_total + o_sval_possession)
                # endregion

                # region defense calculations
                if team_d_points_allow == 0:
                    d_sval_points_allowed = (.4 * 1)
                else:
                    d_sval_points_allowed = (.4 * (1 / (team_d_points_allow / self.model_d_points_allow)))

                try:
                    if team_d_yrds_rush <= 0:
                        d_sval_ypr = (.15 * 1.0)
                    else:
                        d_sval_ypr = (.15 * (1 / (team_d_yrds_rush / self.model_d_yrds_rush)))
                except ZeroDivisionError:
                    d_sval_ypr = (.15 * 1.0)

                try:
                    d_sval_ypp = (.15 * (1 / (team_d_yrds_pass / self.model_d_yrds_pass)))
                except ZeroDivisionError:
                    d_sval_ypp = (.15 * 1.0)

                try:
                    if team_d_yrds_total <= 0:
                        d_sval_yd_given = (.15 * 1.0)
                    else:
                        d_sval_yd_given = (.2 * (1 / (team_d_yrds_total / self.model_d_yrds_total)))
                except ZeroDivisionError:
                    d_sval_yd_given = (.2 * 1.0)

                if team_d_possession_time < self.model_d_possession_time:
                    d_sval_pos_time_allowed = (.1 * (self.model_d_possession_time / team_d_possession_time))
                else:
                    d_sval_pos_time_allowed = (.1 * (1 / (team_d_possession_time / self.model_d_possession_time)))

                if (d_sval_points_allowed + d_sval_ypr + d_sval_ypp + d_sval_yd_given + d_sval_pos_time_allowed) > 1:
                    d_sval = 1.0
                else:
                    d_sval = (
                            d_sval_points_allowed + d_sval_ypr + d_sval_ypp + d_sval_yd_given + d_sval_pos_time_allowed)
                # endregion

                # region misc calculations
                if (.2 * (team_game_margin / self.model_game_margin)) > 0.4:
                    m_sval_margin = 0.4
                elif (.2 * (team_game_margin / self.model_game_margin)) < -0.4:
                    m_sval_margin = -0.4
                else:
                    m_sval_margin = (.2 * (team_game_margin / self.model_game_margin))

                if team_game_penalties == 0:
                    m_sval_penalties = (.05 * 1)
                else:
                    m_sval_penalties = (.05 * (1 / (team_game_penalties / self.model_game_penalties)))

                if team_game_turnover_margin > 1:
                    m_sval_turnovers = (.1 * (.5 * (team_game_turnover_margin / self.model_game_turnover_margin)))
                elif team_game_turnover_margin == 1:
                    m_sval_turnovers = (.1 * 1)
                else:
                    m_sval_turnovers = (.1 * ((team_game_turnover_margin / self.model_game_turnover_margin) - 1))

                if (opponent_str_mod < 1.0) and self.week_num <= 3:
                    opponent_str = (.65 * 0.1)
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

                key_var = "Week" + str(self.week_num)
                t['S-Val-History'][key_var] = sval

                acm_sval = 0.0
                i = 1

                while i <= self.week_num:
                    key_variable = "Week" + str(i)

                    if key_variable in t['S-Val-History']:
                        acm_sval = acm_sval + t['S-Val-History'][key_variable]
                        i = i + 1
                    else:
                        i = i + 1

                if team_game_margin < 0:
                    t['S-Val'] = (acm_sval / len(t['S-Val-History'])) * .985
                else:
                    t['S-Val'] = (acm_sval / len(t['S-Val-History']))

                print_sval = (acm_sval / len(t['S-Val-History']))

                # t['Talent_Mod'] = recalc_talent_mod(print_sval)

                # print(len(t['S-Val-History']))
                print(f"{team}, {print_sval}, {o_sval}, {d_sval}, {m_sval}")

        with open(self.output_path, "w") as output_file:
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
    #     with open(self.output_path, 'w') as output_file:
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
    #         # school_name = t['School']
    #
    #         t['S-Val-History'] = {}
    #         t['S-Val'] = 0.0
    #
    #     with open(self.output_path, 'w') as output_file:
    #         json.dump(teams_json, output_file, indent=2)
    #
    #     print('Complete')
    # endregion


def main():
    # now = datetime.datetime.now()
    # year = now.year
    year = 2018
    week_number = 8

    a = App("lib/2018/teams-fbs.json", "lib/2018/output.json", year, week_number)
    # a.get_weekly_games(week_number)
    a.sval_calc()

    if week_number >= 1:
        a.recalc_talent_mod()

    # a.update_teamsjson()


if __name__ == "__main__":
    main()
