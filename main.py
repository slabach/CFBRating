# core modules
import sys, os, json, requests, re, datetime, statistics
from bs4 import BeautifulSoup

# other modules
# import wikipedia
# import numpy as np


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
        print(f"Getting week {self.week_num} games...")

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
                    self.cur_year, team)
            else:
                req_url = "https://api.collegefootballdata.com/games/teams?year={0}&week={1}&seasonType=regular&team={2}".format(
                    self.cur_year, self.week_num, team)

            page_text = requests.get(req_url).text
            page_json = json.loads(page_text)

            weekly_result_path = "lib/{2}/{0}/Week{1}.json".format(t["School"], self.week_num, self.cur_year)

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
                multiplier = 1.95
            elif 0.925 <= perc_from_top < 0.950:
                multiplier = 1.9
            elif 0.920 <= perc_from_top < 0.925:
                multiplier = 1.85
            elif 0.910 <= perc_from_top < 0.920:
                multiplier = 1.8
            elif 0.900 <= perc_from_top < 0.910:
                multiplier = 1.75
            elif 0.890 <= perc_from_top < 0.900:
                multiplier = 1.65
            elif 0.880 <= perc_from_top < 0.890:
                multiplier = 1.55
            elif 0.870 <= perc_from_top < 0.880:
                multiplier = 1.5
            elif 0.850 <= perc_from_top < 0.870:
                multiplier = 1.45
            elif 0.750 <= perc_from_top < 0.850:
                multiplier = 1.35
            elif 0.690 <= perc_from_top < 0.750:
                multiplier = 1.25
            elif 0.05 <= perc_from_top < 0.690:
                multiplier = 1.15
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
                updated_talent_mod = updated_talent_mod * .675

            t['Talent_Mod'] = updated_talent_mod

        with open(self.output_path, "w") as output_file:
            json.dump(teams_json, output_file, indent=2)

        # print("Complete")

    def sval_calc(self):
        print(f"Calculating Week {self.week_num} SVal")

        def opp_strength(name):

            with open(self.teamsPath, "r") as ostr:
                talent_json = json.load(ostr)

            for entry in talent_json:
                if any(entry['School'] == name for entry in talent_json):

                    if name == entry['School']:
                        return entry['Talent_Mod']
                else:
                    return 0.175

        with open(self.teamsPath, "r") as t:
            teams_json = json.load(t)

        for t in teams_json:
            team = t["School"]

            team_game_path = "lib/{2}/{0}/Week{1}.json".format(team, self.week_num, self.cur_year)

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
                            
                        # if i['category'] == 'turnovers':
                        #     team_o_turnovers_lost = float(i["stat"])

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

                        # if i['category'] == 'turnovers':
                        #     team_d_turnovers_won = float(i["stat"])

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
                               
                        # if i['category'] == 'turnovers':
                        #     team_o_turnovers_lost = float(i["stat"])

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
                            
                        # if i['category'] == 'turnovers':
                        #     team_d_turnovers_won = float(i["stat"])

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

                #region write values
                if ((.4 * o_sval) + (.4 * d_sval) + (.2 * m_sval)) > 1:
                    sval = 1.0000
                else:
                    sval = ((.4 * o_sval) + (.4 * d_sval) + (.2 * m_sval))

                if team_game_margin < 0 and self.week_num >= 14:
                    sval = sval * .95
                elif team_game_margin < 0:
                    sval = sval * .925
                else:
                    pass

                key_var = "Week" + str(self.week_num)
                t['History']['SVal'][key_var] = sval

                if opponent_str_mod < 1.2:
                    t['History']['Off'][key_var] = o_sval * (1-((1-(opponent_str_mod/1.2))*0.15))
                    t['History']['Def'][key_var] = d_sval * (1-((1-(opponent_str_mod/1.2))*0.15))
                else:
                    t['History']['Off'][key_var] = o_sval
                    t['History']['Def'][key_var] = d_sval

                acm_sval = 0.0
                acm_o_sval = 0.0
                acm_d_sval = 0.0
                i = 1

                while i <= self.week_num:
                    key_variable = "Week" + str(i)

                    if key_variable in t['History']['SVal']:
                        acm_sval = acm_sval + t['History']['SVal'][key_variable]
                        acm_o_sval = acm_o_sval + t['History']['Off'][key_variable]
                        acm_d_sval = acm_d_sval + t['History']['Def'][key_variable]
                        i = i + 1
                    else:
                        i = i + 1

                if team_game_margin < 0:
                    t['S-Val'] = (acm_sval / len(t['History']['SVal'])) * .985
                else:
                    t['S-Val'] = (acm_sval / len(t['History']['SVal']))

                t['Off-SVal'] = (acm_o_sval / len(t['History']['SVal']))
                t['Def-SVal'] = (acm_d_sval / len(t['History']['SVal']))

                # print_sval = (acm_sval / len(t['History']['SVal']))
                #endregion

                # print(f"{team}, {print_sval}, {o_sval}, {d_sval}, {m_sval}")

        with open(self.output_path, "w") as output_file:
            json.dump(teams_json, output_file, indent=2)

        print("Complete")

    def win_probability(self):
        def last_year(name):
            last_year_path = "lib/{0}/teams-fbs.json".format(self.cur_year-1)

            with open(last_year_path, "r") as ostr:
                past_json = json.load(ostr)

            for entry in past_json:
                if any(entry['School'] == name for entry in past_json):

                    if name == entry['School']:
                        return entry['S-Val']
                else:
                    return 0.35
        
        def opp_talent_find(name):
            with open(self.teamsPath, "r") as ostr:
                past_json = json.load(ostr)

            for entry in past_json:
                if any(entry['School'] == name for entry in past_json):

                    if name == entry['School']:
                        return entry['Talent_Mod']
                else:
                    return 0.35

        print(f"Week {self.week_num} Win Probability...")

        with open(self.teamsPath, "r") as t:
            teams_json = json.load(t)

        for t in teams_json:
            url_team = t["School"]
            team = t["School"]

            if " " in url_team:
                url_team = url_team.replace(" ", "%20")

            if "&" in url_team:
                url_team = url_team.replace("&", "%26")

            if "Jose" in url_team:
                url_team = url_team.replace("Jose", "Jos%C3%A9")

            req_url = "https://api.collegefootballdata.com/games?year={0}&week={1}&seasonType=regular&team={2}".format(
                self.cur_year, self.week_num, url_team)

            page_text = requests.get(req_url).text
            page_json = json.loads(page_text)
            # print(page_json)

            for gm in page_json:
                
                if gm["home_team"] == team:
                    opponent = gm["away_team"]
                    is_away = False
                else: 
                    opponent = gm["home_team"]
                    is_away = True

                opp_last_year_sval = (last_year(opponent) * 1000) * 2
                team_last_year_sval = (last_year(team) * 1000) * 2
                team_talent = float(t["Talent_Mod"]) * 50
                opp_talent = opp_talent_find(opponent) * 50
                opp_val = opp_last_year_sval + opp_talent
                team_val = team_last_year_sval + team_talent

                if is_away:
                    win_perc = 1 / (1 + (pow(10, 
                                        ( ( ( opp_val + 50 ) - ( team_val ) ) / 400)
                                    )))

                    print(f"{team},{win_perc}, (@ {opponent})")
                else:
                    win_perc = 1 / (1 + (pow(10, 
                                        ( ( ( opp_val ) - ( team_val + 50 ) ) / 400) 
                                    )))

                    print(f"{team},{win_perc}, (vs {opponent})")

        print("Complete")

    # region old code
    # def create_file_structure(self):
    #     with open(self.teamsPath, "r") as t:
    #         teams_json = json.load(t)
    
    #     for t in teams_json:
    #         path = "lib/"+str(self.cur_year)+"/"+t["School"]
    
    #         try:
    #             os.mkdir(path)
    #         except OSError:
    #             print ("Creation of the directory %s failed" % path)
    #         else:
    #             print ("Successfully created the directory %s " % path)
    
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
    #         t['Off-Sval'] = 0.0
    #         t['Def-SVal'] = 0.0
    #
    #     with open(self.output_path, 'w') as output_file:
    #         json.dump(teams_json, output_file, indent=2)
    #
    #     print('Complete')
    #
    #
    # def new_year_talent(self):
    #
    #     def find_new_talent_mod(name):
    #         with open("lib/"+str(self.cur_year)+"/new_year_talent.json", "r") as nytm:
    #             talent_json = json.load(nytm)
    #
    #         for entry in talent_json:
    #             if any(entry['School'] == name for entry in talent_json):
    #
    #                 if name == entry['School']:
    #                     return entry['Talent_Mod']
    #
    #     with open(self.teamsPath, "r") as teamlist:
    #         team_json = json.load(teamlist)
    #
    #     for team in team_json:
    #         new_talent_mod = float(find_new_talent_mod(team['School']))
    #         team['Talent_Mod'] = new_talent_mod
    #         print(f"{team['School']}, {new_talent_mod}")
    #
    #     with open(self.output_path, "w") as output_file:
    #         json.dump(team_json, output_file, indent=2)
    # endregion


def main():
    now = datetime.datetime.now()
    year = now.year
    # year = 2018
    week_number = 1

    # while week_number <= 15:
    a = App("lib/{0}/teams-fbs.json".format(year), "lib/{0}/teams-fbs.json".format(year), year, week_number)
    # a.get_weekly_games()
    # a.sval_calc()

    # if week_number >= 1:
    #     a.recalc_talent_mod()
        
        # week_number = week_number + 1

    # a.new_year_talent()

    # a.update_db()

    a.win_probability()


if __name__ == "__main__":
    main()
