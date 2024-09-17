import os
import ctypes
import time
import requests
from lxml import etree

# Enable ANSI escape sequences in Windows PowerShell
def enable_virtual_terminal_processing():
    if os.name == 'nt': 
        kernel32 = ctypes.windll.kernel32
        handle = kernel32.GetStdHandle(-11)  # STD_OUTPUT_HANDLE
        mode = ctypes.c_ulong()
        kernel32.GetConsoleMode(handle, ctypes.byref(mode))
        kernel32.SetConsoleMode(handle, mode.value | 0x0004)  # ENABLE_VIRTUAL_TERMINAL_PROCESSING

# Call this function at the start
enable_virtual_terminal_processing()

# ANSI color codes
CYAN = "\033[96m"
WHITE = "\033[97m"
YELLOW = "\033[93m"
RESET = "\033[0m"

# Function to fetch XML from a URL or load from a local file
def load_xml(source):
    try:
        if source.startswith("http://") or source.startswith("https://"):
            headers = {
                "Accept": "application/xml, text/xml;q=0.9, */*;q=0.8",  
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3"
            }
            response = requests.get(source, headers=headers)
            response.raise_for_status()  # Check if the request was successful
            xml_data = response.content
            return etree.fromstring(xml_data)
        else:
            return etree.parse(source)
    except requests.exceptions.HTTPError as http_err:
        print(f"{YELLOW}HTTP error occurred: {http_err}{RESET}")
    except Exception as e:
        print(f"{YELLOW}Error loading XML: {e}{RESET}")
    return None

# Function to list teams and allow the user to select a team
def list_teams(tree):
    teams = tree.xpath("//team")
    team_dict = {}
    print(f"{CYAN}Teams Available:{RESET}")
    for team in teams:
        team_name = team.attrib['name']
        print(f"- {CYAN}{team_name}{RESET}")
        team_dict[team_name.lower()] = team

    return team_dict

# Function to list players from a selected team and allow the user to select a player
def list_players_by_team(team_element):
    players = {}
    team_name = team_element.attrib['name']
    print(f"\n{CYAN}Players in Team: {team_name}{RESET}")
    for player in team_element.xpath(".//player"):
        uniform = player.attrib['uni']
        name = player.attrib['name']
        print(f"  {WHITE}{uniform}: {name}{RESET}")
        players[f"{uniform} {name}"] = player

    return players

# Function to get the player's passing stats using the generated XPath
def get_passing_stats(player_element):
    pass_stats = player_element.xpath(".//pass")
    if pass_stats:
        pass_element = pass_stats[0]
        att = pass_element.attrib.get("att", "N/A")
        comp = pass_element.attrib.get("comp", "N/A")
        yds = pass_element.attrib.get("yds", "N/A")
        td = pass_element.attrib.get("td", "N/A")
        int_ = pass_element.attrib.get("int", "N/A")

        return {
            "attempts": att,
            "completions": comp,
            "yards": yds,
            "touchdowns": td,
            "interceptions": int_
        }
    else:
        return None

# Function to format the player's name as "LASTNAME, F."
def format_player_name(name):
    name_parts = name.split()
    if len(name_parts) < 2:
        # If no last name is provided, return the full name in uppercase
        return name.upper()

    first_name = name_parts[0]
    last_name = name_parts[-1]  # Handles middle names too
    formatted_name = f"{last_name.upper()}, {first_name[0].upper()}."
    return formatted_name

# Function to write the player's passing stats to an output XML file
def write_output_xml(formatted_name, stats, output_file):
    root = etree.Element("playerStats")
    player_element = etree.SubElement(root, "player", name=formatted_name)
    
    pass_stats = etree.SubElement(player_element, "passStats")
    
    etree.SubElement(pass_stats, "attempts").text = stats['attempts']
    etree.SubElement(pass_stats, "completions").text = stats['completions']
    etree.SubElement(pass_stats, "yards").text = stats['yards']
    etree.SubElement(pass_stats, "touchdowns").text = stats['touchdowns']
    etree.SubElement(pass_stats, "interceptions").text = stats['interceptions']
    
    tree = etree.ElementTree(root)
    tree.write(output_file, pretty_print=True, xml_declaration=True, encoding="UTF-8")
    print(f"{CYAN}Output written to {output_file}{RESET}")

# Function to allow the user to select a valid team
def select_team(tree):
    teams = list_teams(tree)
    while True:
        team_input = input(f"{CYAN}Enter the team name (or part of it) to select the team: {RESET}").lower()

        selected_team = None
        for team_name, team_element in teams.items():
            if team_input in team_name:
                selected_team = team_element
                break

        if selected_team:
            return selected_team
        else:
            print(f"{YELLOW}Invalid team name. Please try again.{RESET}")

# Function to allow the user to select a valid player
def select_player(selected_team):
    players = list_players_by_team(selected_team)
    while True:
        player_input = input("Enter the player's uniform number or name to select them: ")

        selected_player = None
        for key, player_element in players.items():
            if player_input.lower() in key.lower():
                selected_player = player_element
                break

        # Explicitly check if selected_player is not None
        if selected_player is not None:
            return selected_player
        else:
            print("Invalid player selection. Please try again.")


# Main function to run the program in a loop every 5 seconds
def main():
    print(f"{CYAN}Coyote Sports Network - PrestoStats Football XML parser for NewTek/Vizrt LiveText{RESET}")
    print(f"{CYAN}Version 0.6.1{RESET}")
    print(f"{CYAN}Written by: Trae Toelle{RESET}")
    print("\n")
    input_source = input(f"{CYAN}Enter the input XML file path or URL: {RESET}")
    output_file = input(f"{CYAN}Enter the output XML file path (default: output.xml): {RESET}") or "output.xml"

    # Load the XML
    tree = load_xml(input_source)
    if tree is None:
        print(f"{YELLOW}Failed to load the XML file.{RESET}")
        return

    # Allow the user to select a team and a player
    selected_team = select_team(tree)
    selected_player = select_player(selected_team)

    player_name = selected_player.attrib['name']
    formatted_name = format_player_name(player_name)

    # Loop to query the XML every 5 seconds and write the output to an XML file
    try:
        while True:
            print(f"\n{CYAN}Querying passing stats for {WHITE}{formatted_name}{RESET}...")
            print(f"{YELLOW}Press Ctrl+C to stop{RESET}")

            # Reload the XML to get updated stats
            tree = load_xml(input_source)
            if tree is None:
                print(f"{YELLOW}Failed to reload the XML. Retrying in 5 seconds...{RESET}")
                time.sleep(5)
                continue

            # Get the player's passing stats
            stats = get_passing_stats(selected_player)
            if stats:
                print(f"  {CYAN}Attempts: {WHITE}{stats['attempts']}{RESET}")
                print(f"  {CYAN}Completions: {WHITE}{stats['completions']}{RESET}")
                print(f"  {CYAN}Yards: {WHITE}{stats['yards']}{RESET}")
                print(f"  {CYAN}Touchdowns: {WHITE}{stats['touchdowns']}{RESET}")
                print(f"  {CYAN}Interceptions: {WHITE}{stats['interceptions']}{RESET}")

                # Write the stats to an XML file
                write_output_xml(formatted_name, stats, output_file)
            else:
                print(f"{YELLOW}No passing stats available for {formatted_name}.{RESET}")

            # Wait for 5 seconds before querying again
            time.sleep(5)
    except KeyboardInterrupt:
        print(f"\n{YELLOW}Program stopped.{RESET}")

if __name__ == "__main__":
    main()
