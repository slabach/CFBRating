# core modules
# import numpy as np
import sys, os, json, requests, re, datetime
# from urllib.parse import urlencode
# from urllib.request import urlopen
from bs4 import BeautifulSoup

# other modules
import wikipedia
# from lxml import etree


class App:
    def __init__(self, teams_path):
        self.teamsPath = teams_path

    def get_weekly_games(self, week_num):
        # now = datetime.datetime.now()
        # year = now.year
        year = 2018

        with open(self.teamsPath, "r") as t:
            teams_json = json.load(t)

        for t in teams_json:
            team = t["School"]

            if " " in team:
                team = team.replace(" ", "%20")

            req_url = "https://api.collegefootballdata.com/games/teams?year={0}&week={1}&seasonType=regular&team={2}".format(
                year, week_num, team)
            page_text = requests.get(req_url).text
            page_json = json.loads(page_text)

            weekly_result_path = "lib/2018/{0}/Week{1}.json".format(t["School"], week_num)

            with open(weekly_result_path, 'w') as output_file:
                json.dump(page_json, output_file, indent=2)

            print(req_url)

    def sval_calc(self, week_num):
        #region Model Values
        model_points_scored = 35

        #endregion

        with open(self.teamsPath, "r") as t:
            teams_json = json.load(t)

        for t in teams_json:
            team = t["School"]
            team_game_path = "lib/2018/{0}/Week{1}.json".format(t["School"], week_num)


    #region old code
    # def create_file_structure(self):
    #     with open(self.teamsPath, "r") as t:
    #         teams_json = json.load(t)
    
    #     for t in teams_json:
    #         path = "lib/2018/"+t["School"]
    
    #         try:
    #             os.mkdir(path)
    #         except OSError:
    #             print ("Creation of the directory %s failed" % path)
    #         else:
    #             print ("Successfully created the directory %s " % path)
    
    #     print('Completed')
    
    # def get_school_conferences(self):
    #     with open(self.teamsPath, "r") as t:
    #         teams_json = json.load(t)
    
    #     for t in teams_json:
    #         # if str(t["School"]) == "Purdue":
    #         search_string = str(t["School"]+ " " + t["Mascot"] + " football")
    #         wiki_search = wikipedia.search(search_string)
    #         wiki_page = wikipedia.page(wiki_search[0])
    #         wiki_url = wiki_page.url
    #         page_text = requests.get(wiki_url).text
    #         req = BeautifulSoup(page_text, 'lxml')
    
    #         infobox = req.find('table', {'class': 'infobox'})
    #         conferenceHTag = infobox.find('th', string='Conference')
    #         conferenceNameTag = conferenceHTag.find_next_sibling('td').text
    
    #         t['Conference'] = conferenceNameTag
    
    #     with open("lib/output.json", 'w') as output_file:
    #         json.dump(teams_json, output_file)
    
    #     print('Complete')

    # def update_teamsjson_w_scoreval(self):
    #     with open(self.teamsPath, "r") as t:
    #         teams_json = json.load(t)

    #     for t in teams_json:
    #         scoreval = 0.00
    #         t['S-Val'] = scoreval

    #     with open("lib/output.json", 'w') as output_file:
    #         json.dump(teams_json, output_file, indent=2)

    #     print('Complete')
    #endregion


def main():
    a = App("lib/2018/teams-fbs.json")
    # a.get_weekly_games(1)
    a.sval_calc(1)


if __name__ == "__main__":
    main()
