# Docker Development Environment

To get started, install Docker Desktop from [here](https://www.docker.com/products/docker-desktop/).
After installing Docker, navigate to the 'DEV ENVIRONMENTS' page, and create a new devenvironment
clone the ion git repository, found [here](https://github.com/tjcsl/ion), into the dev environment.
Next, open the dev environment in vscode.
run 'cd config' to change your directory into config
In the config directory, edit the file 'make_admin.py', substituting '<YOURUSERNAME>' for your ion username
Then, to find the name of your dev environment, go to docker desktop and to the tab 'DEV ENVIRONMENTS'
the name should be in the form of 'ion-< >_< >'.
Edit the file 'docker-compose.yaml', replacing both instances of <DEFAULT_VOLUME_NAME> to 
'volume-(dev environment name)'
Finally, run 'docker-compose up' and wait while the development environment is set up.
The application will be running at localhost:8080.