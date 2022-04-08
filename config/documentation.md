# Create an Ion Development Enviornment

## Prerequisites
- [Docker](https://www.docker.com) is the containization framework that runs Ion's individual services. Installation is OS-specific and instructions can be found [here](ttps://www.docker.com/products/docker-desktop/). On Windows and Mac, install Docker Desktop.
- [GitHub](https://github.com) is the version control system used by the CSL. Make sure that you have an account and an SSH key tied to that account that will allow you to push and pull code.


## Set Up
1. Create your own fork of the [``tjcsl/ion`` repository](https://github.com/tjcsl/ion.git).
2. Clone the Ion repositiory from your Ion fork by running ``git clone git@github.com:<YOUR_GITHUB_USERNAME>/ion.git``.
3. Inside the Ion repository, edit the ``config/make_admin.py`` file, replacing "\<YOURUSERNAME\>" with your Ion username.
4. Run ``cd config``.
5. Run ``docker-compose up -d``.


## Post Set Up
Navigate to http://localhost:8000 in the web browser of your choice. You might have to wait up to 60 seconds the first time that you create the container. When presented with the login page, log in with your Ion username and the password "nofish" (without the quotes).


## Useful Commands
### Interacting with the application:
If you need to run a Django command like ``makemigrations``, ``collectstatic`` or ``shell_plus``, run ``docker exec -it application bash`` in your terminal. That wlll give you a shell into the application container. You can also use this to run scripts like ``build_sources.sh``. If you need to view the output from or restart ``runserver``, run ``docker attach application``. 
