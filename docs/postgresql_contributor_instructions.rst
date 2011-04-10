PostgreSQL setup instructions for new contributors
==================================================

Mac
---

If you're on the Mac, add this to /etc/sysctl.conf::

    kern.sysv.shmmax=8388608
    kern.sysv.shmmin=1
    kern.sysv.shmmni=64
    kern.sysv.shmseg=8
    kern.sysv.shmall=32768

Add this to your .bashrc::

    export PGDATA="/path/to/home/folder/for/db/tables", such as /home/audreyr/pgdata or /Users/audreyr/pgdata

Reload your .bashrc::

    source ~/.bashrc

Initialize PostgreSQL::

    initdb

Edit your pg_hba.conf::

    sudo su - postgres
    

Start the database server::

    pg_ctl start

Create a PostgreSQL database::

    createdb packaginator

Ubuntu
------

tbd

Windows
-------

tbd
