# * Libraries


import os
from time import sleep
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler


# * Classes
class ActionHandler(FileSystemEventHandler):
    def __init__(self, handler):
        super().__init__()
        self.handler = handler

    def on_any_event(self, event):
        if not event.is_directory:
            return self.handler(event.event_type, event.src_path)


class Watcher:
    """Watches for changes in the GrashSite template path and renders on change.

    Attributes:

        site (:obj:`GrashSite`): an instance of a Grash site
        verbose (:obj:`bool`):
            True if the output on progress must be included, False otherwise

    """

    def __init__(self, site, verbose=True):
        self.site = site
        self.verbose = verbose

    @property
    def projectPath(self):
        return self.site.templatePath

    def isHandled(self, actionType, source):
        """Determines whether a given action is handled.

        Args:
            actionType (:obj:`str`)
                A string representing the type of the action.
                Only ~modified~ and ~created~ action types are acted upon.

            source (:obj:`str`):
                The path to the file on which the action has been applied.

        Returns:

            True if the file is handled, False otherwise.

        """
        handledActions = {"modified", "created"}
        return actionType in handledActions\
            and source.startswith(self.projectPath)\
            and os.path.isfile(source)

    def actionHandler(self, actionType, source, verbose=True):
        """Re-render the website upon any significant change in files.

        Args:
            actionType (:obj:`str`):
                A string representing the type of the action.
                Only ~modified~ and ~created~ action types are acted upon.

            source (:obj:`str`):
                The path to the file on which the action has been applied.

            verbose (:obj:`bool`):
                A boolean to control the verbosity of the output.
                Silent if False.

        Returns:

            None.

        """
        filename = os.path.relpath(source, self.projectPath)
        if self.isHandled(actionType, source):
            if verbose:
                print("{} {}".format(actionType, filename))
            if self.site.isStatic(filename):
                staticFiles = self.site.getDependencies(filename)
                self.site.copyStatic(staticFiles)
            elif self.site.isPandoc(filename):
                docType = os.path.splitext(filename)[1][1:]
                self.site.renderDoc(docType, filename)
            else:
                templates = self.site.getDependencies(filename)
                self.site.renderTemplates(templates)

    def watch(self):
        """Watch and re-render upon the creation or modification of files.

        Returns:

            None.

        """
        observer = Observer()
        observer.schedule(ActionHandler(self.actionHandler),
                          path=self.projectPath,
                          recursive=True)
        observer.start()
        try:
            while True:
                sleep(1)
        except KeyboardInterrupt:
            observer.stop()
        observer.join()
