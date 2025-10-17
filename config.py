from enum import Enum

CURRENT_SPRINT_ID= 234234

CONFIG_YAML_PATH= "./config_microsoft_graph.yaml"

class AllTicketStatuses (Enum):
    OPEN = 'Open'
    IN_SPECIFICATION = 'In Specification'
    IN_PROGRESS = 'In Progress'
    IN_REVIEW = 'In Review'
    PENDING = 'Pending'
    CLOSED = 'Closed'
    RESOLVED = 'Resolved'