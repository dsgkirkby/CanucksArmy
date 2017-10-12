# How to Write a Scraper

This will walk through the basics of creating a scraper, with `modules/roster.py` as an example.

## Step 1: find the page containing the info you need and request it

For our mock scraper, we want to get all the roster info for a season. On eliteprospects, we can find this at http://www.eliteprospects.com/team.php?team=1580.

We can use a Python module like `requests` to then fetch this page to work with in Python code:

```python
team_request = requests.get('http://www.eliteprospects.com/team.php?team=1580')
```

## Step 2: examine the page layout to find the structure of the elements we're interested in

On the roster page, we want each row of the table, to pull each player's data from. We can right click -> inspect element on a row to view the underlying markup.

We can parse the page we fetched using `requests` using a library like `BeautifulSoup`:

```python
team_page = BeautifulSoup(team_request.text, "html.parser")
```

We can then navigate the parsed page to get to the team table. We can find elements by their attributes (`id`, `class`, etc.), or we can navigate from the root of the page down to the element. For the roster, we'll find the header with the tabs (roster/stats/depth chart/in the system) by its unique id, `globalnav`, and navigate from there to the table containing the players and grab all its rows (`<tr>...</tr>` tags):

```python
def global_nav_tag(tag):
        return tag.has_attr('id') and tag.attrs['id'] == 'globalnav'

player_table = team_page.find(global_nav_tag).find_next_sibling('table')

players = player_table.find_all('tr')
```

From there, for each player we can grab the information from each row and store it in a list. Note that `Name`/`ID`/etc are numeric constants we've defined elsewhere, to represent the position of the various pieces of information in the row.

```python
name = player_stats[NAME].a.text.strip()
number = player_stats[ID].text.strip()[1:]
position = player_stats[NAME].font.text.strip()[1:-1]
dob = player_stats[DOB].text.strip()
hometown = player_stats[HOMETOWN].a.text.strip()
height = player_stats[HEIGHT].find_all('span')[METRIC].text
weight = player_stats[WEIGHT].find_all('span')[METRIC].text
shoots = player_stats[SHOOTS].text

results_array.append([
    number,
    name,
    position,
    season,
    league_name,
    team_name,
    dob,
    hometown,
    height,
    weight,
    shoots
])
```

## Step 3: Automate the Rest

Now that we successfully collect the information we're interested in, we need to automate the process of finding all the pages. This will depend a lot on the website we're scraping, but we can hopefully either predict all the URLs we'll need from their structure (for example, if the page URL contains a `page={x}` parameter), or find another page on the website that links to everything we'll need (which we can then grab in much the same manner as explained above).
