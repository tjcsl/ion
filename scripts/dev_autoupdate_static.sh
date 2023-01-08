#!/bin/bash
# FOR DEVELOPMENT ONLY
# Automatically copies modified static files in intranet/static to intranet/collected_static
# Run from root ion directory, e.g. ./scripts/dev_autoupdate_static.sh
# Use this when WHITENOISE_USE_FINDERS is set to False in settings

cd intranet/static

# CSS
sass --watch css:../collected_static/css &

# Everything else
inotifywait --format '%w%f %e' -rm -e modify -e create -e delete --exclude '\.scss$' . | 
while read -r file action; do
    file=${file#./}  # Remove leading ./ from file path
    if [ "$action" = "CREATE" ] || [ "$action" = "MODIFY" ]; then
        cp "$file" ../collected_static/"$file"
        echo "Copied $file to ../collected_static/$file"
    elif [ "$action" = "DELETE" ]; then
        rm ../collected_static/"$file"
        echo "Deleted ../collected_static/$file"
    fi
done
