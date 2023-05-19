from main import create_db_connection
import pandas as pd
import matplotlib.pyplot as plt
import plotly.graph_objs as go
from plotly.offline import plot
import datetime

def avg_rank_by_placement(stony = False):
    connection = create_db_connection()
    cursor = connection.cursor()

    if stony != False:
        stony = (input('Will these be the true rankings? Y/N '))

    query = """
    SELECT school_name, AVG(team_placement) AS average_placement
    FROM placement
    GROUP BY school_name
    ORDER BY average_placement ASC
    """

    cursor.execute(query)
    results = cursor.fetchall()

    if stony == 'Y' or stony == 'y':
        # Find the index of the row with school_name "SUNY Stony Brook" and move it to the front of the list
        for i in range(len(results)):
            if results[i][0] == "SUNY Stony Brook":
                results.insert(0, results.pop(i))
                break

    print('\n')
    print("Team Rankings based off average placement: ")
    #print('\n')
    school_name_list = []

    for rank, (school_name, average_placement) in enumerate(results, start=1):

        if stony == 'Y' and school_name == 'SUNY Stony Brook':
            average_placement = 1.00
        elif stony == 'y' and school_name == 'SUNY Stony Brook':
            average_placement = 1.00
        else:
            round(average_placement, 5)
        print(f"{rank}. {school_name}: Average Placement - {average_placement}")
        school_name_list.append(school_name)

    return school_name_list

def conference_avg_rank_by_placement():
    connection = create_db_connection()
    cursor = connection.cursor()

    query = """
    SELECT t.conference, p.school_name, AVG(p.team_placement) AS average_placement
    FROM placement AS p
    JOIN teams AS t ON p.school_name = t.school_name
    GROUP BY t.conference, p.school_name
    ORDER BY t.conference, average_placement ASC
    """

    cursor.execute(query)
    results = cursor.fetchall()

    current_conference = None
    print("Average Team Rankings by Conference: ")

    place = 0
    for row in results:
        conference = row[0]
        school_name = row[1]
        average_placement = row[2]
        place += 1

        if conference != current_conference:
            print(f"\nConference: {conference}")
            current_conference = conference
            place = 1


        print(f"{place}. {school_name}: Average Placement - {average_placement}")


    cursor.close()
    connection.close()


def team_distribution():
    connection = create_db_connection()
    cursor = connection.cursor()

    query = """
    SELECT school_name, state
    FROM teams
    """

    cursor.execute(query)
    results = cursor.fetchall()
    #print(results)

    state_dict = {}
    for row, (name, state) in enumerate(results):
        if state not in state_dict:
            state_dict[state] = 1
        else:
            state_dict[state] += 1

    #print(state_dict)

    states = list(state_dict.keys())
    counts = list(state_dict.values())

    # Create a choropleth map
    fig = go.Figure(data=go.Choropleth(
        locations=states,  # set state names as the location
        z=counts,  # set the data values as the z-values
        locationmode='USA-states',  # set the location mode to USA-states
        #colorscale='Reds',  # set the color scale
        colorbar_title='Count'  # set the color bar title
    ))

    # Set the map title
    fig.update_layout(
        title_text='Number of Teams from Each State',
        geo_scope='usa'
    )
    # Show the map
    plot(fig)
    cursor.close()
    connection.close()

def team_performance():
    connection = create_db_connection()

    query = """
    SELECT school_name, regatta_date, team_placement, season 
    FROM placement
    """

    cursor = connection.cursor()
    cursor.execute(query)

    results = cursor.fetchall()

    data = []
    for result in results:
        school = result[0]
        race_date = result[1] + ' 20' + result[3][2 : 4]
        placement = result[2]
        season = result[3].strip('/')
        chars = ['/', ',']
        for char in chars:
            if char in placement:
                placement = placement.split(char)[0]

        data.append((school, race_date, placement, season))

    df = pd.DataFrame(data, columns=['school_name', 'regatta_date', 'team_placement', 'season'])
    df['regatta_date'] = pd.to_datetime(df['regatta_date'], format='%b %d %Y')
    #print(len(df))
    df = df.drop_duplicates()
    df = df.dropna()
    df.drop(df[df['team_placement'] == ''].index, inplace=True)

    #print(df)

    result = {}
    # Group the DataFrame by school_name and regatta_date at a monthly frequency
    grouped = df.groupby(['school_name', pd.Grouper(key='regatta_date', freq='M')])

    # Iterate over each group (i.e., each school and each month)
    for name, group in grouped:
        # Unpack the name into separate variables for school and date
        school, date = name

        # Extract the placement values for this school and month as a list
        placement_values = group['team_placement'].values.tolist()

        # Construct a string representation of the month and year (e.g., '5-2023' for May 2023)
        month_year = '{}-{}'.format(date.month, date.year)

        # If this is the first time we've seen this school, create an empty dictionary for it
        if school not in result:
            result[school] = {}

        # Store the list of placement values for this school and month in the result dictionary
        result[school][month_year] = placement_values

    #print(result)
    for school in result:
        for month in result[school]:
            placement = result[school][month]
            place_vals = [int(place) for place in placement]
            place_sum = sum(place_vals)
            place_len = len(place_vals)
            result[school][month] = round(place_sum/place_len, 5)

    #print(result)
    school_name_list = avg_rank_by_placement()


    fig, ax = plt.subplots(figsize=(16, 6))
    for idx, i in enumerate(school_name_list):
        if idx >= 5:
            break
        school_data = result[i]
        x = list(school_data.keys())
        y = list(school_data.values())
        x = [datetime.datetime.strptime(date_str, '%m-%Y') for date_str in x]  # convert strings to datetime
        x, y = zip(*sorted(zip(x, y)))  # sort the data based on datetime
        ax.plot(x, y, label=i)
    ax.set_xlim(min(x), max(x))
    ax.set_xlabel('Month-Year')
    ax.set_ylabel('Average Team Placement')
    ax.set_title('Average Team Placement by Year')
    ax.legend()
    plt.xticks(rotation=45)
    plt.show()

    cursor.close()
    connection.close()

def team_participation():
    connection = create_db_connection()
    cursor = connection.cursor()

    query = """
    SELECT school_name, COUNT(*) AS participation_count
    FROM placement
    GROUP BY school_name
    """

    cursor.execute(query)
    results = cursor.fetchall()

    #print(results)

    team_names = [row[0] for row in results]
    participation_count = [row[1] for row in results]

    # sort teams by descending participation count
    sorted_teams = sorted(results, key = lambda x: x[1], reverse = True)

    # Get the top 20 teams and their counts
    top_20 = sorted_teams[:20]
    top_20_teams = [row[0] for row in top_20]
    top_20_participation = [row[1] for row in top_20]

    # Get the bottom 20 teams and their counts
    bottom_20 = sorted_teams[-20:]
    bottom_20_teams = [row[0] for row in bottom_20]
    bottom_20_participation = [row[1] for row in bottom_20]

    # Plot each school and participation pair
    fig, axs = plt.subplots(2, 1, figsize = (10, 12))

    axs[0].bar(top_20_teams, top_20_participation)
    axs[0].set_xlabel('Team')
    axs[0].set_ylabel('Partipaction Count')
    axs[0].set_title('Top 20 Teams by Regatta Participation')
    axs[0].tick_params(axis = 'x', rotation = 90)

    axs[1].bar(bottom_20_teams, bottom_20_participation)
    axs[1].set_xlabel('Team')
    axs[1].set_ylabel('Partipaction Count')
    axs[1].set_title('Bottom 20 Teams by Regatta Participation')
    axs[1].tick_params(axis = 'x', rotation = 90)

    plt.tight_layout()
    plt.show()

#avg_rank_by_placement()
#conference_avg_rank_by_placement()
#plot_regatta_type_team_performance()
#team_distribution()
#team_performance()
team_participation()