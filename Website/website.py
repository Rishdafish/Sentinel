import time
from typing import List
import random
from google.cloud import storage

class WebSite(): 
    def __init__(self):
        self.coins = 0
        self.ConsecWorkDays = 0
        self.MaxFocusTime = 0
        self.AvrNumDeepWrkDaily = 0
        self.NumTotalHours = 0
        self.Projects = []
        self.Subjects = []
        self.weeklyTasks = [] 
        self.currSubject = ""
        self.currProject = None
        self.isFocused = False
        self.TimeForCurSubject = 0
        self.currSchedule = []
        self.quests = []
        self.inSchedule = False 
        self.currentRank = "Iron 1"
        self.TotalRanks = ["Iron 1", "Iron 2", "Iron 3", "Bronze 1", "Bronze 2", "Bronze 3", "Silver 1", "Silver 2", "Silver 3",
                           "Gold 1", "Gold 2", "Gold 3", "Platinum 1", "Platinum 2", "Platinum 3",
                           "Diamond 1", "Diamond 2", "Diamond 3", "Ascendant 1", "Ascendant 2", "Ascendant 3",
                           "Immortal 1", "Immortal 2", "Immortal 3", "Radiant"]

    def createSchedule(self):
        if self.inSchedule: 
            return self.currSchedule
        else: 
            self.inSchedule = True

    def addProject(self, projectName: str, projectDescription: str, endDate: List[int], projectGithub: str, projectStatus: str, projectTech: str):
        random_id = random.randint(100000, 999999)
        for id in self.Projects:
            if id["id"] == random_id:
                random_id = random.randint(100000, 999999)
        project = {
            "name": projectName,
            "id": random_id,
            "description": projectDescription,
            "endDate": endDate,
            "github": projectGithub,
            "status": projectStatus,
            "tech": projectTech
        }
        self.Projects.append(project)
        if projectStatus == "Developing" and self.currProject == "":
            self.currProject = project
        elif projectStatus == "Developing" and self.currProject != "":
            if self.currProject["endDate"]

    def deleteProject(self, projectID: int):
        for project in self.Projects:
            if project["id"] == projectID:
                if self.currProject and self.currProject["id"] == projectID:
                    self.currProject = None
                self.Projects.remove(project)
    
    def changeProjectInfo(self, projectID : int, newProjectName: str, newProjectDescription: str, newEndDate: List[int], newProjectGithub: str, newProjectStatus: str, newProjectTech: str):
        for project in self.Projects:
            if project["id"] == projectID:
                if self.currProject["id"] == projectID and newProjectStatus == "Completed":
                    self.currProject = None
                    self.coins += 100
                
                project["name"] = newProjectName
                project["description"] = newProjectDescription
                project["endDate"] = newEndDate
                project["github"] = newProjectGithub
                project["status"] = newProjectStatus
                project["tech"] = newProjectTech
                break

    def purchase(self):
        pass 

    def storeInfo(self, bucketName: str) -> bool: 
        pass 
    def LLMCall(self, Prompt):
        pass 



    


        
