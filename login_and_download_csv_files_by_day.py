import requests
from datetime import datetime, timedelta

def login():
	global session
	login_url = "<login_url>"

	data = {
			"username": "<username>",
			"password": "<pass>",
	}

	#POST request
	response = session.post(login_url, data=data)

	#update session cookie based on response
	session.cookies.update(response.cookies)

	print(response.status_code)
	print(response.headers)
	print(response.cookies)

retries = 0
def download_file(url, filename):
	global retries
	try:
		#call URL & generate file
		response = session.get(url)
		print(response.status_code)

		if(response.status_code == 401):
			print("Unauthorized encountered, login in")
			login()
			raise Exception("Throwing to retry")
		
		if(response.status_code != 200):
			raise Exception("Throwing to retry")	
		
		file = open(filename,"w",encoding="utf-8")
		file.write(response.text)
		file.close()
		retries = 0

	except Exception as e:
		# If there is an error, print the exception
		print(e)

		if(retries <= 1):
			print("Retrying...{0}".format(filename))
			retries += 1
			download_file(url, filename)
		else:
			print("Maximum retries for ...{0}".format(filename))
			retries = 0
		

#set start & end date for loop
start_date = datetime.strptime('<YYYY-MM-DD>', "%Y-%m-%d")
end_date = datetime.strptime('<YYYY-MM-DD>', "%Y-%m-%d")

#create session
session = requests.Session()

#attempt to login in existing session
login()

#loop through days (downloading one csv per day)
while start_date < end_date:
	request_date = start_date.strftime("%d-%b-%y")
	csv_url = "<csv_url>?fromDate={0}&toDate={1}".format(request_date,request_date)

	download_file(csv_url, "file_{0}.csv".format(start_date.strftime("%Y%m%d")))

	#increment day
	start_date += timedelta(days=1)