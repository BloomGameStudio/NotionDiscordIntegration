# NotionDiscordIntegration
Notion Integration Into Discord

### How to Deploy:


**Setup** 

1. Do one of the following:
    - Clone the repo. 
    - Copy the docker-compose.yml file to where you wannt to run the bot.

2. Rename the env.example file to .env  
Alternativly create a .env file in the same dir of the application from where the application will be executed

3. Replace the example values in the now called .env file with the needed real values 
Alternativly if you have created the .env file without renaming the example file 
Populate the .env file with the needed enviorment variables
Reference the env.example files for needed enviorment variables and examples


**How to run in production** 

1. Open a terminal window in the directory where the Docker Compose file is located.

2. Start the containers by running the command:

        docker-compose up -d

    Wait for the containers to start. This may take a few minutes.

