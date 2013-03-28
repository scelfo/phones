phones
======

Utility to watch your phones on your home network to figure out when you come
home and leave.  Automatically toggles Google Voice forwarding using the
https://github.com/pettazz/pygooglevoice library.

Run the compile.sh to get started.

Add a contab entry to run the home_phone.py script often such as every two minutes like this example:
*/2 * * * * /path/to/home_phone.py

If you don't want to have any emails from cron unless there is a problem use:
*/2 * * * * /path/to/home_phone.py > /dev/null
