#!/bin/sh
echo "---- Running entrypoint script ----"

echo "Performing pre-startup tasks..."
export DEBUG=FALSE  # HUGE performance benefits. Manually enable if you need to debug.
python3 config/docker/entrypoint.py &  # For initial setup
sass --watch intranet/static/css:intranet/collected_static/css &  # Automatically compile modified scss files

echo "Starting web server..."
cat << END

██╗    ██╗███████╗██╗      ██████╗ ██████╗ ███╗   ███╗███████╗
██║    ██║██╔════╝██║     ██╔════╝██╔═══██╗████╗ ████║██╔════╝
██║ █╗ ██║█████╗  ██║     ██║     ██║   ██║██╔████╔██║█████╗ 
██║███╗██║██╔══╝  ██║     ██║     ██║   ██║██║╚██╔╝██║██╔══╝
╚███╔███╔╝███████╗███████╗╚██████╗╚██████╔╝██║ ╚═╝ ██║███████╗
 ╚══╝╚══╝ ╚══════╝╚══════╝ ╚═════╝ ╚═════╝ ╚═╝     ╚═╝╚══════╝

     ████████╗                  ██╗                   ██╗
     ╚══██╔══╝ ██████╗          ██║ ██████╗ ███╗   ██╗██║
        ██║   ██║   ██║         ██║██║   ██║██╔██╗ ██║██║
        ██║   ██║   ██║         ██║██║   ██║██║╚██╗██║╚═╝
        ██║   ╚██████╔╝         ██║╚██████╔╝██║ ╚████║██╗
        ╚═╝    ╚═════╝          ╚═╝ ╚═════╝ ╚═╝  ╚═══╝╚═╝

END

# Wrap the run command in a loop so that it restarts if it crashes, e.g. due to a syntax error
while :  # while true
do 
    python3 manage.py run 0.0.0.0:8080  # Custom run command that skips system checks for performance
    sleep 1
done
