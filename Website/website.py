from typing import List
import random
from google.cloud import storage

class WebSite(): 
    def __init__(self):
        self.coins = 0
        self.dailyStreak = 3
        self.averagePerDay = 0
        self.averagePerWeek = 0
        self.totalhours = 0
        self.timeTillProject = 0
        self.numSleepOnDesk = 0 
        self.subjects = []
        self.tasks = []
        self.schedule = []
        self.isFocused = False
        self.quests = []
        self.currentRank = "Iron 1"
        self.TotalRanks = ["Iron 1", "Iron 2", "Iron 3", "Bronze 1", "Bronze 2", "Bronze 3", "Silver 1", "Silver 2", "Silver 3",
                           "Gold 1", "Gold 2", "Gold 3", "Platinum 1", "Platinum 2", "Platinum 3",
                           "Diamond 1", "Diamond 2", "Diamond 3", "Ascendant 1", "Ascendant 2", "Ascendant 3",
                           "Immortal 1", "Immortal 2", "Immortal 3", "Radiant"]
        
    def addCoins(self, amount: int):
        self.coins += amount
    
    def removeCoins(self, amount: int):
        if self.coins >= amount:
            self.coins -= amount
        else:
            raise ValueError("Not enough coins to remove")

    def getCoins(self) -> int:
        return self.coins

    def getDailyStreak(self) -> int:
        return self.dailyStreak
    
    def addQuest(self, quest: str, reward: int):
        self.quests.append(quest)

    def completeQuest(self, quest: str):
        if quest in self.quests:
            self.quests.remove(quest)
            # Assuming each quest gives a fixed reward of 100 coins
            self.addCoins(100)
        else:
            raise ValueError("Quest not found")
        
    def getQuests(self) -> List[List]:
        return self.quests

    

    
    


        
