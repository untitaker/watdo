# A task-manager for the command line.

*   Watdo stores task lists as directories and tasks as `.ics` files in these
    directories. Because CalDAV uses a similar storage structure, it is very
    easy to access tasks of a remote CalDAV server using watdo and davfs.

*   Watdo will open a markdown-file containing your tasks in an editor of your
    choice. Any changes you make to that file will be mirrored to the described
    storage system after closing the editor.

*   Watdo will *never* support syncronization to remote servers in the core.
    Instead, these tasks should be accomplished by additional programs that
    access watdo's storage. This concept is inspired by the popular combination
    of mutt and offlineimap.

*   Watdo is written in Python 2 and depends on the icalendar package on PyPI.


# Tutorial: watdo + davfs + owncloud

1.  Install watdo with `pip install --user watdo`.

2.  First you will need the proper CalDAV URL for your calendars. For ownCloud
    5 this is `https://my.server/remote.php/caldav/calendars/yourusername/`.

3.  Configure davfs. I won't go into this. [ArchLinux' wiki has a complete yet
    concise guide on it.](https://wiki.archlinux.org/index.php/Davfs) I'll
    assume you have your `/etc/fstab` set up to mount your calendar at
    `/mnt/calendar`. Add `mount /mnt/calendar` to the autostart of your desktop
    and you won't have to bother about authentication any more.

4.  Set the environment variable `$WATDO_PATH` to `/mnt/calendar`.

5.  Run `watdo` from the command line.


# All configuration possibilities

*   `$WATDO_EDITOR` specifies the editor to use. It defaults to `$EDITOR`.

*   `$WATDO_PATH` specifies the directory path to save the calendars to. It
    defaults to `~/.watdo/tasks/`

*   `$WATDO_TMPPATH` specifies the directory path to create needed temporary
    files in. Because these files may contain sensitive data, this option does
    not default to `/tmp`, because its permissions allow other system users to
    delete the file and recreate it with different content. Instead, it
    defaults to `~/.watdo/tmp/`.


# Things that are broken right now

*   It should have a real config file instead of all these envvars.

*   It should expose more metadata to the user.

*   It should be more easily scriptable, by exposing CLI options.

*   It should have unit tests.

*   Indention of subsequent lines follows the markdown specification (four
    spaces or one tab), but looks really ugly if list indices are > 9.
