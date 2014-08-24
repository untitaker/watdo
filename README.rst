=====
watdo
=====

A task-manager for the command line
===================================

* Watdo stores task lists as directories and tasks as `iCalendar
  <https://en.wikipedia.org/wiki/ICalendar>`_ files in these directories.
  Because CalDAV basically uses the same storage structure, a neat hack can be
  used to access tasks of some CalDAV servers using watdo and davfs.

* Watdo will open a file containing your tasks in an editor of your choice.
  Any changes you make to that file will be mirrored to the described storage
  system after closing the editor.

* You can use `vdirsyncer <https://github.com/untitaker/vdirsyncer>`_ to sync
  your tasks with online services.

* watdo works with Python 2.7+


Simple usage of watdo
=====================

1. Install watdo with ``pip install --user watdo``.

2. Run ``watdo`` from the command line. It will ask you a few questions, all of
   which you can skip if you don't care.

3. Your favorite editor should open. Edit the file as you wish. It's a file
   whose format kind-of resembles `todo.txt
   <https://github.com/ginatrapani/todo.txt-cli/wiki/The-Todo.txt-Format>`_.

   The first line of a task contains the summary and some other metadata. It
   looks something like this::

       My task description due:2014-09-09 @computers id:1

   The date format for the ``due`` flag can be either ``YYYY-mm-dd``,
   ``YYYY-mm-dd/HH:MM`` or ``HH:MM?``. It can also be ``today``, ``now`` or ``tomorrow``.

   The ``@computers`` indicates the task is saved in the calendar/task-list
   called "computers".

   After this first line, optional lines indented with four spaces form the
   description field of the task.

   You can mark this task as done by placing a ``x`` in front of it::

       x My task description due:2014-09-09 @computers id:1

   Or write ``COMPLETED`` instead of the ``x``::

       COMPLETED My task description due:2014-09-09 @computers id:1

   Or really any valid value for the ``STATUS`` property in the `the iCalendar
   standard <http://www.kanzaki.com/docs/ical/status.html>`_. There is also
   ``.`` as a shortcut for ``IN-PROCESS``. ``NEEDS-ACTION`` is ignored.

   If you get the syntax of your file wrong, watdo *should* allow you to edit
   it again after showing an error. It's still in alpha though.

7. Save and close the file. Watdo shows all changes you've made in a basic
   overview::
    
       0.  Modify: My cool task => My super-cool task
       1.  Delete: Something useless

   If you don't want watdo to do these things, enter ``0 1`` and hit enter.
   You could also hit ``^C``.

8. Tasks with the status ``COMPLETED`` or ``CANCELLED`` are not shown by default.
   You can view these tasks with ``watdo -a``.

License
=======

watdo is released under the Expat/MIT License, see ``LICENSE`` for more
details.
