# Synchronize /opt/iem from git and do the following, since the iemweb code
# may have updated and we need to restart wsgi processes to pick up the changes

# 1. As user mesonet, git pull the latest code
sudo -u mesonet git -C /opt/iem pull

# 2. Killall iemwsgi_ap processes
ps auxw | grep iemwsgi | awk '{print $2}' | xargs kill
