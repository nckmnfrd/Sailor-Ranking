from bs4 import BeautifulSoup
import requests
import mysql
import mysql.connector
import numpy as np

# # Make a request to the website
# url = 'https://scores.collegesailing.org/f22/'
# page = requests.get(url)
#
# # Create a BeautifulSoup object
# soup = BeautifulSoup(page.content, 'html.parser')
#
# # Find all instances of class "row0" and "row1"
# rows = soup.find_all('tr', attrs={'class': 'row0'}) + soup.find_all('tr', attrs={'class': 'row1'})
#
# # Print the text content of each row
# for row in rows:
#     row_data = [td.get_text(strip=True) for td in row.find_all('td')]
#     print(row_data)


def main():
    connection = create_db_connection()
    if connection is not None:
        #get_teams()
        #get_regattas()
        get_team_attendance()
        # other code that requires a database connection
        connection.close()
    else:
        print("Unable to connect to database.")

def create_db_connection():
    try:
        connection = mysql.connector.connect(
            host = '192.168.1.153',
            username = 'Nicholass-MBP',
            password = 'Rubbish019!',
            database = 'sailor_ranking'
        )
        # check if the connection was successful
        if connection.is_connected():
            print("Connection to MySQL database established!")
            print('\n')
            return connection
        else:
            print("Connection failed.")
            return None
    except mysql.connector.Error as e:
        print(f"Error connecting to MySQL database: {e}")
        return None



def get_teams():
    url ='https://scores.collegesailing.org/schools/'
    page = requests.get(url)
    soup = BeautifulSoup(page.content, 'html.parser')

    connection = create_db_connection()

    # Find all instances of class "school name"
    teams = soup.find_all('tr', class_=['row0', 'row1'])

    MAISA = ['DC', 'VA', 'NY', 'PA', 'MD', 'NJ', 'ON', 'DE']
    MCSA = ['OH', 'MI', 'IN', 'IA', 'IL', 'WI', 'NE', 'MO', 'MN']
    NEISA = ['MA', 'ME', 'RI', 'CT', 'NH', 'QC', 'VT']
    NWICSA = ['OR', 'BC', 'WA']
    PCCSC = ['AZ', 'CA', 'HI']
    SAISA = ['AL', 'SC', 'GA', 'NC', 'FL', 'TN']
    SEISA = ['TX', 'LA', 'OK', 'KS']

    lst = []
    #team_list = np.array([])
    for team in teams:
        row_data = [td.get_text(strip=True) for td in team.find_all('td')]
        school_link = team.find('a', href=True)['href']
        state = row_data[3]

        if state in MAISA:
            conference = 'MAISA'
        elif state in MCSA:
            conference = 'MCSA'
        elif state in NEISA:
            conference = 'NEISA'
        elif state in NWICSA:
            conference = 'NWICSA'
        elif state in PCCSC:
            conference = 'PCCSC'
        elif state in SAISA:
            conference = 'SAISA'
        elif state in SEISA:
            conference = 'SEISA'
        else:
            conference = 'N/A'

        # Insert the team into the database
        cursor = connection.cursor()
        query = "INSERT INTO teams (school_name, state, conference, link) VALUES (%s, %s, %s, %s)"
        values = (row_data[1], row_data[3], conference, url[:-9] + school_link)
        cursor.execute(query, values)
        connection.commit()

    # Close the database connection
    connection.close()


def get_regattas():
    url = "https://scores.collegesailing.org"
    seasons = ['/s15/', '/s15/', '/f16/','/s16/','/f17/','/s17/', '/f18/','/s18/', '/f19/','/s19/', '/f20/','/s20/']
    connection = create_db_connection()


    for season in seasons:
        season_url = url + season
        page = requests.get(season_url)
        soup = BeautifulSoup(page.content, 'html.parser')

        regattas = soup.find_all('tr', class_=['row0', 'row1'])

        # Clean up the HTML rows
        for row in regattas:
            regatta = row.find_all('td')
            # Check if the first cell contains a link, and extract its text
            link_cell = regatta[0].find('a')
            if link_cell:
                regatta_title = link_cell.get_text()
            type = regatta[2].get_text()
            date = regatta[4].get_text()
            winner = regatta[-1].get('title')
            print(regatta_title, type, date, winner)

            cursor = connection.cursor()
            query = "INSERT INTO regattas (regatta_title, type, date, winner) VALUES (%s, %s, %s, %s)"
            values = (regatta_title, type, date, winner)
            cursor.execute(query, values)
            connection.commit()

    connection.close()

def get_team_attendance():
    connection = create_db_connection()
    cursor = connection.cursor()

    query = 'SELECT school_name, link FROM teams'
    cursor.execute(query)

    results_tups = cursor.fetchall()
    seasons = ['/s15/', '/s15/', '/f16/', '/s16/', '/f17/', '/s17/', '/f18/', '/s18/', '/f19/', '/s19/', '/f20/', '/s20/']

    for result in results_tups:  # grab the school name and their link
        school_name = result[0]
        url = result[1]
        url = url[:-1]
        #print(url)

        for season in seasons:
            season_url = url + season
            page = requests.get(season_url)
            soup = BeautifulSoup(page.content, 'html.parser')

            regattas = soup.find_all('tr', class_=['row0', 'row1'])

            for regatta in regattas:
                regatta_name = regatta.find('span', itemprop='name').text
                regatta_date = regatta.find('time', itemprop='startDate').text
                regatta_info = regatta.find_all('td')
                team_placement = regatta_info[6].get_text()
                regatta_type = regatta_info[2].get_text()

                #print(school_name, regatta_name, regatta_type, regatta_date, team_placement, season)
                insert_query = "INSERT INTO placement (school_name, regatta_name, regatta_type, regatta_date, team_placement, season) VALUES (%s, %s, %s, %s, %s, %s)"
                values = (school_name, regatta_name, regatta_type, regatta_date, team_placement, season)
                cursor.execute(insert_query, values)
                connection.commit()



    cursor.close()
    connection.close()


if __name__ == '__main__':
    main()