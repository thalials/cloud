import requests
from sys import argv

with open("DNSName.txt", "r") as file:
        DNSName = file.readlines()

users = '/users/'
groups = '/groups/'

url = 'http://' + DNSName[0] 
commands = ["get", "post", "delete"]

if __name__ == "__main__":
    if argv[1] == commands[0]:
        response = requests.get(url + users, auth=('cloud', 'cloud'))
        print(response)
    elif argv[1] == commands[1]:
        username = argv[2]
        email = argv[3]
        data = {'username':username, 'email': email}
        response = requests.post(url + users, auth=('cloud', 'cloud'), data=data)
        print(response)

    elif argv[1] == commands[2]:
        number =  argv[2] + '/'
        response = requests.delete(url + users + number, auth=('cloud', 'cloud'))
        print(response)
    
    else:
        print("Invalid command. Try again!")







