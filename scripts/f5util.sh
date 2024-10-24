# Our present method to remove a webfarm node from the F5 pool

rm -f /var/www/html/index.php >& /dev/null
if [ "$1" = "ON" ]; then
 cat > /var/www/html/index.php <<EOM
<?php
sleep(300);
header("Status: 500 Internal Server Error");

EOM
fi
