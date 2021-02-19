#!/bin/sh

for theme in cerulan cosmo cyborg darkly flatly journal litera lumen lux materia minty morph pulse quartz sandstone simplex sketchy slate solar spacelab superhero united vapor yeti zephyr; do
    mkdir -p "characters/static/css/bootswatch/$theme"
    wget -O "characters/static/css/bootswatch/$theme/_variables.scss"  "https://raw.githubusercontent.com/thomaspark/bootswatch/v5/dist/$theme/_variables.scss"
    wget -O "characters/static/css/bootswatch/$theme/_bootswatch.scss"  "https://raw.githubusercontent.com/thomaspark/bootswatch/v5/dist/$theme/_bootswatch.scss"
done
