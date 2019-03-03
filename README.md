# CFBRating

Python Application for a College football rating model

Using data from api.collegefootball.com

Enter the week of games to analyze. 
Foreach game during that week, script pulls a team's data for their game, compares it to the model and it's % away from the model, weights it and assigns the team an "s-value" for that game. 

Each team is ranked based on their running average of that s-value.