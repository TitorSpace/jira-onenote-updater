import yaml
import requests
from jira import JIRA
from config import CURRENT_SPRINT_ID, CONFIG_YAML_PATH, AllTicketStatuses

#Read the current elements of the yaml file
def read_yaml(file_path):
    with open(file_path, 'r') as file:
        return yaml.safe_load(file)

#Overwrites the current elements of the yaml file
def write_yaml(file_path, data):
    with open(file_path, 'w') as file:
        yaml.dump(data, file)

def create_onenote_table():
    columns = ["Who", "Description", "Ticket", "Status", "Priority", "Status Symbol"]
    table = "<table border='1' cellpadding='5' cellspacing='0'>\n"
    table += "  <tr>\n"
    for column in columns:
        table += f"    <th>{column}</th>\n"
    table += "  </tr>\n"
    return table

def add_issues_to_table(issues):
    table = create_onenote_table()
    sorted_issues = sorted(issues, key=lambda issue: issue.fields.assignee.displayName if issue.fields.assignee else 'Unassigned')
    for issue in sorted_issues:
        status = issue.fields.status.name
        if status in [AllTicketStatuses.OPEN, AllTicketStatuses.IN_SPECIFICATION]:
            status_symbol = "⬛"  # Black square
        elif status in [AllTicketStatuses.IN_REVIEW, AllTicketStatuses.IN_PROGRESS]:
            status_symbol = "🟨"  # Green square
        elif status == AllTicketStatuses.RESOLVED:
            status_symbol = "🟩"  # Blue square
        else:
            status_symbol = "🟥"  # Gray square
        ticket_link = f"https://jira.cc.bmwgroup.net/browse/{issue.key}"
        table += "  <tr>\n"
        table += f"    <td>{issue.fields.assignee.displayName if issue.fields.assignee else 'Unassigned'}</td>\n"
        table += f"    <td>{issue.fields.summary}</td>\n"
        table += f"    <td><a href='{ticket_link}'>{issue.key}</a></td>\n"
        table += f"    <td>{status}</td>\n"
        table += f"    <td>{issue.fields.priority.name if issue.fields.priority else 'None'}</td>\n"
        table += f"    <td>{status_symbol}</td>\n"
        table += "  </tr>\n"
    table += "</table>\n"  # Ensure the table is properly closed
    return table

def take_data_from_query():
    yaml_data= read_yaml(CONFIG_YAML_PATH)
    server_url =yaml_data['server_url']
    token_auth_jira = yaml_data['access_token_jira']
    jira = JIRA(server=server_url, token_auth=token_auth_jira)
    statuses = ', '.join([f'"{status.value}"' for status in AllTicketStatuses])
    jql_query = f'project = SWP AND issuetype in (Bug, Task) AND status in ({statuses}) AND Sprint = {CURRENT_SPRINT_ID} AND assignee in (bartoszbrykpartner, miguelruizpartner, fidellorenzopartner)'
    issues = jira.search_issues(jql_query)
    table = add_issues_to_table(issues)
    return table

def get_and_store_page_id(page_title):
    '''
    This method calls the GRAPH MICROSOFT API to gather info about a page id according to a ONENOTE page name.
    The id will be printed and stored in the yaml file
    '''
    # Import the data of the yaml file
    yaml_data= read_yaml(CONFIG_YAML_PATH)
    access_token =yaml_data['access_token_graph_microsoft']
    # Microsoft Graph API endpoint for OneNote section
    url_with_id = f"https://graph.microsoft.com/v1.0/me/onenote/pages?$filter=title eq '{page_title}'"
    # Set up the headers with the access token
    headers = {
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/json'
    }
    response = requests.get(url_with_id, headers=headers)
    if response.status_code == 200:
        section_data = response.json()
        print(f"Section: {section_data['value'][0]['id']}")
        yaml_data['page_id'] = section_data['value'][0]['id']
    else:
        print(f"Error: {response.status_code}")
        print(response.json())
    write_yaml(CONFIG_YAML_PATH, yaml_data)

def patch_in_page(page_title):
    '''
    This method calls the GRAPH MICROSOFT API to PATCH info in a specific OneNote page
    '''
    get_and_store_page_id(page_title)
    yaml_data = read_yaml(CONFIG_YAML_PATH)
    access_token = yaml_data['access_token_graph_microsoft']
    page_id = yaml_data['page_id']

    # Add the new content
    onenote_table = take_data_from_query()
    request_content = f'This is the current sprint table.<br>{onenote_table}'
    url = f'https://graph.microsoft.com/v1.0/me/onenote/pages/{page_id}/content'
    html_content = f'<p>{request_content}</p>'
    headers = {
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/json'
    }
    body = [
        {
            'target': 'body',
            'action': 'append',
            'content': html_content
        }
    ]
    response = requests.patch(url, headers=headers, json=body)
    if response.status_code == 204:
        print('Text added successfully!')
    else:
        print(f'Failed to add text. Status code: {response.status_code}')
        print(response.json())