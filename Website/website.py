from typing import List
from Sentinel.utils import llmCall

class WebSite(Sentinel): 
    def __init__(self, 
                 coins : int = 0, 
                 NumOfDeepWrkDays : int = 0,
                 MaxFocusTime: int = 0,
                 NumHoursPerDay: int = 0,


                 ):
        self.coins = coins
        self.NumOfDeepWrkDays = NumOfDeepWrkDays
        self.MaxFocusTime = MaxFocusTime
        self.NumHoursPerDay = NumHoursPerDay

        pass 
    def createSchedule(self, time: List[int]) -> List[str]:

        

