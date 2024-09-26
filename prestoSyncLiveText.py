import os
import time
import requests
from lxml import etree
import ctypes

# Enable ANSI escape sequences in Windows PowerShell
def enable_virtual_terminal_processing():
    if os.name == 'nt':  # If we're on Windows
        kernel32 = ctypes.windll.kernel32
        handle = kernel32.GetStdHandle(-11)  # STD_OUTPUT_HANDLE
        mode = ctypes.c_ulong()
        kernel32.GetConsoleMode(handle, ctypes.byref(mode))
        kernel32.SetConsoleMode(handle, mode.value | 0x0004)  # ENABLE_VIRTUAL_TERMINAL_PROCESSING

# Enable ANSI escape sequences
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

# Function to select a team based on user input and vh (Home/Visitor) attribute
def select_team(tree):
    teams = tree.xpath("//team")
    team_dict = {}
    print(f"{CYAN}Teams Available:{RESET}")
    
    # Map teams based on their name and vh (Home or Visitor)
    for team in teams:
        team_name = team.attrib.get('name')
        vh = team.attrib.get('vh').upper()  # Capitalize the abbreviation
        if team_name:  # Only add teams with a valid name
            team_key = f"{team_name} ({vh})"  # Capitalize each word in team_name and abbreviation
            print(f"  {WHITE}{team_key}{RESET}")
            team_dict[(team_name.lower(), vh)] = team
    
    while True:
        team_input = input(f"{CYAN}Enter the team name (or part of it) to select the team: {RESET}").lower()

        matched_teams = []
        for (team_name, vh), team_element in team_dict.items():
            if team_input in team_name:  # Partial match for team name
                matched_teams.append((team_name, team_element))

        if len(matched_teams) == 1:
            selected_team_name, selected_team = matched_teams[0]
            print(f"Selected Team: {selected_team_name.title()} ({'Home' if selected_team.attrib.get('vh') == 'H' else 'Visitor'})")  # Confirm selected team
            return selected_team_name, selected_team  # Return the selected team name and element
        elif len(matched_teams) > 1:
            print("Multiple teams matched your input. Please be more specific.")
            # Optionally, display the matched teams for the user
            for team_name, team in matched_teams:
                print(f"- {team_name.title()} ({'Home' if team.attrib.get('vh') == 'H' else 'Visitor'})")
        else:
            print(f"{YELLOW}No team matched your input. Please try again.{RESET}")

# Function to list players from a selected team and allow the user to select a player
def list_players_by_team(team_name, team_element):
    players = {}
    
    print(f"\n{CYAN}Players in Team: {team_name.title()}{RESET}")
    
    # Ensure we're selecting players within the specific team element
    for player in team_element.xpath("./player"):  # Use `./player` to select only players within the team element
        uniform = player.attrib.get('uni', 'Unknown')  # Handle missing 'uni' attribute
        name = player.attrib.get('name', 'Unknown Player')  # Handle missing 'name' attribute
        print(f"  {WHITE}{uniform}: {name}{RESET}")
        players[f"{uniform} {name}"] = player

    return players

# Function to format the player's name as "LASTNAME, F."
def format_player_name(full_name):
    name_parts = full_name.split()
    if len(name_parts) >= 2:
        last_name = name_parts[-1].upper()
        first_initial = name_parts[0][0].upper() + "."
        formatted_name = f"{last_name}, {first_initial}"
    else:
        formatted_name = full_name.upper()  # In case the name is just one word
    return formatted_name

# Function to write the player's stats to the output XML file
def write_output_xml(player_name, stats, output_file):
    formatted_name = format_player_name(player_name)  # Format the player's name as "LASTNAME, F."
    
    root = etree.Element("playerStats")
    player_element = etree.SubElement(root, "player", name=formatted_name)
    
    # Add passStats as a child of the player element
    pass_stats_element = etree.SubElement(player_element, "passStats")
    
    # Write each stat to the passStats element
    etree.SubElement(pass_stats_element, "attempts").text = stats.get('att', '0')
    etree.SubElement(pass_stats_element, "completions").text = stats.get('comp', '0')
    etree.SubElement(pass_stats_element, "yards").text = stats.get('yds', '0')
    etree.SubElement(pass_stats_element, "touchdowns").text = stats.get('td', '0')
    etree.SubElement(pass_stats_element, "interceptions").text = stats.get('int', '0')

    tree = etree.ElementTree(root)
    with open(output_file, "wb") as f:
        tree.write(f, pretty_print=True, xml_declaration=True, encoding="UTF-8")

# Function to extract the player's stats from the XML
def get_player_stats(player_element):
    stats = {}
    pass_element = player_element.find(".//pass")  # Find pass stats under the player
    if pass_element is not None:
        stats['att'] = pass_element.attrib.get('att', '0')
        stats['comp'] = pass_element.attrib.get('comp', '0')
        stats['yds'] = pass_element.attrib.get('yds', '0')
        stats['td'] = pass_element.attrib.get('td', '0')
        stats['int'] = pass_element.attrib.get('int', '0')
    return stats

# Function to display stats in the console
def display_stats(player_name, stats):
    formatted_name = format_player_name(player_name)  # Format the player's name
    print(f"  {CYAN}Attempts: {WHITE}{stats.get('att', '0')}{RESET}")
    print(f"  {CYAN}Completions: {WHITE}{stats.get('comp', '0')}{RESET}")
    print(f"  {CYAN}Yards: {WHITE}{stats.get('yds', '0')}{RESET}")
    print(f"  {CYAN}Touchdowns: {WHITE}{stats.get('td', '0')}{RESET}")
    print(f"  {CYAN}Interceptions: {WHITE}{stats.get('int', '0')}{RESET}")


# Main function to run the program
def main():
    try:
        print(f"{CYAN}Coyote Sports Network - PrestoStats Football XML Parser for NewTek/Vizrt LiveText")
        print(f"{CYAN}Version: {WHITE}0.7.3")
        print(f"{CYAN}Written by: {WHITE}Trae Toelle")
        input_source = input(f"{CYAN}Enter the input XML file path or URL: {RESET}")
        output_file = input(f"{CYAN}Enter the output XML file path (default: output.xml): {RESET}") or "output.xml"

        # Load the XML initially to allow the user to select the team and player
        tree = load_xml(input_source)
        if tree is None:
            print(f"{YELLOW}Failed to load the XML file.{RESET}")
            return

        while True:
            # Allow the user to select a team and a player
            selected_team_name, selected_team = select_team(tree)
            players = list_players_by_team(selected_team_name, selected_team)
            
            # Prompt the user to select a player by uniform number or name
            player_input = input(f"{CYAN}Enter the player's uniform number or name to select them: {RESET}").lower()
            selected_player = None
            for key, player_element in players.items():
                if player_input in key.lower():
                    selected_player = player_element
                    break

            if selected_player is not None:
                player_name = selected_player.attrib.get('name')
                formatted_name = format_player_name(player_name)
                print(f"Selected player: {formatted_name}")

                # Query the player's stats every 5 seconds and output to XML
                while True:
                    try:
                        # Inform the user that the program is querying the stats
                        print(f"\n{CYAN}Querying passing stats for {WHITE}{formatted_name}...{RESET}")
                        print(f"{YELLOW}Press Ctrl+C to change player/team or exit{RESET}")
                        
                        # Refresh the XML to get updated stats
                        tree = load_xml(input_source)
                        # Retrieve the updated player stats
                        updated_player_element = tree.xpath(f"//player[@name='{player_name}']")[0]
                        stats = get_player_stats(updated_player_element)
                        
                        # Display the stats in the console
                        display_stats(player_name, stats)

                        # Write stats to the output file
                        write_output_xml(player_name, stats, output_file)
                        print(f"\n{CYAN}Output written to {WHITE}{output_file}.{RESET}")
                        
                        
                        # Wait 5 seconds before re-querying
                        time.sleep(5)
                    
                    except KeyboardInterrupt:
                        print(f"\n{YELLOW}Querying stopped. Do you want to:{RESET}")
                        print(f"{CYAN}1. Switch team and player{RESET}")
                        print(f"{CYAN}2. Exit{RESET}")
                        choice = input(f"{CYAN}Enter your choice: {RESET}")

                        if choice == '1':
                            break  # Break out of the loop, allows user to select a new team/player
                        elif choice == '2':
                            print(f"{YELLOW}Exiting...{RESET}")
                            return
            else:
                print(f"{YELLOW}No matching player found.{RESET}")
    
    except KeyboardInterrupt:
        print(f"\n{YELLOW}Program interrupted by user. Exiting...{RESET}")

if __name__ == "__main__":
    main()
