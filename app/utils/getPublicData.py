from app.models import *

def getAllCars():
    return CarInformation.objects.all()

def getAllUsersInfoData():
    return User.objects.all()

def getAllComment():
    return SpiderCarComment.objects.all()


