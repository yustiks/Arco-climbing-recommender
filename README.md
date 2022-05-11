**Recommender system for crags and climbing routes in Arco, Italy**
_______________________________________________________________________________________________________________

In this repository, the prototype for Recommender System for climbing crags and climbing routes is published.
The webpage currently running:
```
http://arco-climbing-recommender.site/login
```
password can be found in the paper.

In addition, we included Usability Study results.

How to run website:
clone the repository, create new environment:
```
python3 -m venv env
```
activate environment:
```
source env/bin/activate
```
install flask and other libraries via pip:
```
pip install -r requirements.txt
```
and run throuh the flask:
```
flask run
```
By default, Flask will run the application you defined in app.py on port 5000. While the application is running, go to http://localhost:5000 using your web browser. You’ll see a web page containing the system interface.
_______________________________________________________________________________________________________________
Usability results:

Q11: What is your age?

![Question 11 summary](/Usability_study/img/Q11.png?raw=true "Participants' age")

Q12: What is your sex?

![Question 12 summary](/Usability_study/img/Q12.png?raw=true "Participants' sex")

Q13: How many years have you climbed?

![Question 13 summary](/Usability_study/img/Q13.png?raw=true "Participants' climbing experience")

Q14: What type of climbing guidebook do you usually use?

![Question 14 summary](/Usability_study/img/Q14.png?raw=true "Participants' type of climbing guidebooks")

Q14.1: The name of e-climbing guidebook source?

![Question 14.1 summary](/Usability_study/img/Q14.1.png?raw=true "Name of e-climbing guidebook source")

Q15: What is your prefereed climbing styles?

![Question 15 summary](/Usability_study/img/Q15.png?raw=true "Participants' climbing styles")
