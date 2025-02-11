from utils.readFile import *
import pandasql as ps
import pandas as pd

# Requires file with following tables:
# Joint Coordinates
# Joint Reactions


class jointReaction:
    def __init__(self, **kwargs):
        self.conn = self.getConnection()
        self.reaction = self.getReaction()
        self.coord = self.getCoord()
    
