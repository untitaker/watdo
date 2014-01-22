# A task-manager for the command line.

*   Watdo stores task lists as directories and tasks as
    [iCalendar](https://en.wikipedia.org/wiki/ICalendar) files in these
    directories. Because CalDAV basically uses the same storage structure, it
    is very easy to access tasks of a remote CalDAV server using watdo and
    davfs.

*   Watdo will open a markdown-file containing your tasks in an editor of your
    choice. Any changes you make to that file will be mirrored to the described
    storage system after closing the editor.

*   Watdo will *never* support syncronization to remote servers in the core.
    Instead, these tasks should be accomplished by additional programs that
    access watdo's storage. This concept is inspired by the popular combination
    of mutt and offlineimap.

*   The only Python version watdo is tested with is 2.7.


# Full tutorial: watdo + davfs + owncloud

1.  Install watdo with `pip install --user watdo`.

2.  First you will need the proper CalDAV URL for your calendars. For ownCloud
    5 this is `https://my.server/remote.php/caldav/calendars/yourusername/`.

3.  Configure davfs. I won't go into this. [ArchLinux' wiki has a complete yet
    concise guide on it.](https://wiki.archlinux.org/index.php/Davfs) I'll
    assume you have your `/etc/fstab` set up to mount your calendar at
    `/mnt/calendar`. Add `mount /mnt/calendar` to the autostart of your desktop
    and you won't have to bother about authentication any more.

5.  Run `watdo` from the command line. It will ask you a few questions. If it
    asks you where your tasks are stored, say `/mnt/calendar`.

6.  Your favorite editor should open. Edit the file as you wish. It's a file
    whose format kind-of resembles
    [todo.txt](https://github.com/ginatrapani/todo.txt-cli/wiki/The-Todo.txt-Format).

    The first line of a task contains the summary and some other metadata. It
    looks something like this:

        My task description due:2014/09/09 @computers id:1 status:IN-PROCESS

    The date format for the `due` flag can be either YYYY/mm/dd,
    YYYY/mm/dd-HH:MM or HH:MM.

    The `@computers` indicates the task is saved in the calendar/task-list
    called "computers".

    The `status` flag can contain any value specified in [the iCalendar
    standard](http://www.kanzaki.com/docs/ical/status.html). Tasks with
    `status:CANCELLED` or `status:COMPLETED` will get hidden from the list.
    Use `watdo -a` to show them too.

    After this first line, optional lines indented with four spaces form the
    description field of the task.

    If you get the syntax of your file wrong, watdo *should* allow you to edit
    it again after showing an error. It's still in alpha though.

7.  Save and close the file. Watdo shows all changes you've made in a basic
    overview:
    
        0.  Modify: My cool task => My super-cool task
        1.  Delete: Something useless

    If you don't want watdo to do these things, enter ``0 1`` and hit enter.
    You could also hit `^C`.

8.  Tasks with the status `COMPLETED` or `CANCELLED` are not shown by default.
    You can view these tasks with `watdo -a`.

# Bonus: Offline sync
1.  Play around with watdo and look what it does to the files in
    `/mnt/calendar`. Then take a look at
    [Unison](http://www.cis.upenn.edu/~bcpierce/unison/). It is able to sync
    two folders, like rsync. But unlike rsync, it doesn't ignore changes on one
    side.

2.  Edit `~/.watdo/config` and remove your custom path. Create the directory
    `~/.watdo/tasks/` and copy everything from `/mnt/calendar/` over there.
    Then run `unison -perms 0 -dontchmod -batch /mnt/calendar/
    ~/.watdo/tasks/`. It won't do anything, since both folders are up-to-date.

3.  Use watdo to modify your tasks somehow. You probably will notice the
    performance improvements.

4.  Run the unison command again. It should syncronize your changes back to the
    server.

5.  Set up some sort of cronjob that runs the unison command for you. Note:
    Unison might encounter merging conflicts, you should therefore figure out
    some way to get notified if unison exits with a non-zero code.
