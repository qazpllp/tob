if theres anissue with the database getting out of sync.
Move the app 'zone' away from the folder.
Remove traces of it in settings and url in 'tob'
Delete database info
run manage.py migrate
Add files and info back in
run migrate again