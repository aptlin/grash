#! /usr/bin/python3
# -*- coding: utf-8 -*-

# * Libraries


import logging
import os
import pathlib
import shutil

import pypandoc

from jinja2 import Environment, FileSystemLoader

from .watcher import Watcher
from .config import Settings


# * Variables


settings = Settings()

TEMPLATE_DIRECTORY = settings.templatePath
ENCODING = settings.encoding
BUILD_PATH = settings.buildDir
ASSETS = settings.staticDirs
PANDOC_DIRS = settings.pandocDirs
PANDOC_TYPES = settings.pandocTypes

# * Classes


class GrashSite:

    """Main Grash class :: configures and generates pages from templates.

    Attributes:

        encoding (:obj:`str`):
            A string representing the encoding of the rendered templates.

        jinjaEnv (:obj:`jinja2.Environment`):
            Main class for Jinja

        templatePath (:obj:`str`):
            The path where templates reside.

        buildDir (:obj:`str`):
            The path to the build directory

        staticDirs  (:obj:`list` of :obj:`str`):
            The list of paths to the directories with static files.

        pandocDirs(:obj:`str`):
            The path to the directory with files to process with pandoc.

        pandocTypes (:obj:`list` of :obj:`str`):
            A list of file formats to process with pandoc.

        logger (:obj:`logging.Logger`):
            Event logger

        verbose (:obj:`bool`):
            True if the methods should be verbose on execution,
            False otherwise.

    """
    def __init__(self,
                 encoding,
                 jinjaEnvironment,
                 logger,
                 templatePath,
                 buildDir,
                 staticDirs=[],
                 pandocDirs=PANDOC_DIRS,
                 pandocTypes=PANDOC_TYPES,
                 verbose=True):
        # Variables
        self.encoding = encoding

        # Paths
        self.buildDir = buildDir
        self.staticDirs = staticDirs
        self.templatePath = templatePath

        # Pandoc

        self.pandocDirs = pandocDirs
        self.pandocTypes = pandocTypes

        # Jinja Configuration
        self._jinjaEnv = jinjaEnvironment

        # Utilities
        self.logger = logger
        self.verbose = verbose

    def __repr__(self):
        return "GrashSite({}, {})".format(self.templatePath, self.buildDir)

    def _ensureParent(self, filename):
        """Ensure the parent directory of a file exists.

        Args:

            filename (:obj: `str`): The name of a file (with or without dir.)

        Returns:

            None.

        """
        parent = os.path.dirname(filename)
        if parent:
            dirpath = os.path.join(self.buildDir, parent)
            pathlib.Path(dirpath).mkdir(parents=True, exist_ok=True)

    # * Instance properties

    @property
    def templateNames(self):
        """Return a list of template names.

        Returns:

            (:obj:`list` of :obj:`str`): A list of template names.

        """
        return self._jinjaEnv.list_templates(filter_func=self.isTemplate)

    @property
    def templates(self):
        """Yield a generator of templates.

        Returns:
            (:obj:`generator`): A generator of templates.

        """
        for templateName in self.templateNames:
            yield self.getTemplate(templateName)

    @property
    def staticFiles(self):
        """Return a list of names corresponding to static files.

        Returns:

            (:obj:`list` of :obj:`str`):
                A list of names corresponding to static files.

        """
        return self._jinjaEnv.list_templates(filter_func=self.isStatic)

    # * Getters

    def getTemplate(self, templateName):
        """Get an instance of jinja2 template from the environment by name.

        Args:
            templateName (:obj:`str`):
                A string representing the name of a template to look for.
        """
        return self._jinjaEnv.get_template(templateName)

    def getDependencies(self, filename):
        """Get a list of files dependent on the file ~filename~.

        Args:
            filename (:obj:`str`): the name of a file

        Returns:
            A `list` of `str`, files dependent on the file ~filename~.

        """
        if self.isModule(filename):
            return self.templates
        elif self.isTemplate(filename):
            return [self.getTemplate(filename)]
        elif self.isStatic(filename) or self.isPandoc:
            return [filename]
        else:
            return []

    # * Typisation

    def isStatic(self, dirname):
        """Check whether a directory contains static files.

        Static files are not processed by Jinja2.

        Args:
            filename (:obj: `str`): the name of a directory being checked
        Returns:
            True if the directory is considered static,
            False otherwise.

        """
        if not self.staticDirs:
            # No directories with static files are listed.
            return False
        else:
            for dirpath in self.staticDirs:
                if dirpath.startswith(dirname):
                    return True
                else:
                    return False

    def isPandoc(self, dirname):
        """Check whether a directory or a file is to be processed with pandoc.

        Args:
            filename (:obj: `str`): the name of a directory being checked
        Returns:
            True if the directory or file is to be processed with pandoc,
            False otherwise.

        """
        if not self.pandocDirs:
            # No directories with static files are listed.
            return False
        else:
            for dirpath in self.pandocDirs:
                if dirpath.startswith(dirname):
                    return True
                else:
                    return False

    def isModule(self, path):
        """Checks if a file or directory with the ~path~ is/has a template module.

        Template modules are templates which are not stand-alone, but which are
        used in rendering other templates.

        A file is considered a template module if its name or names of
        any of its parent directories are prefixed with ``'_'``.

        Args:
            path (:obj: `str`): the name of a file or directory being checked
        Returns:
            True if the file or directory is/has a template module,
            False otherwise.

        """
        return any((route.startswith("_")
                    for route in path.split(os.path.sep)))

    def isPrivate(self, path):
        """Checks if a file or directory is private.

        Private files are neither rendered nor used as template modules.

        A file is considered private if its name or names of any of
        its parent directories are prefixed with ``'.'``.

        Args:
            path (:obj: `str`): the name of a file or directory being checked
        Returns:
            True if the file or directory is private,
            False otherwise.

        """

        return any((route.startswith(".")
                    for route in path.split(os.path.sep)))

    def isTemplate(self, path):
        """Checks if a file is a template.

        A file is considered a template if it is not a static file or a module.

        Args:

            path (:obj: `str`): the name of a file being checked

        Returns:

            True if the file is a template.
            False otherwise.
        """

        if self.isModule(path) or self.isPrivate(path)\
           or self.isStatic(path) or self.isPandoc(path):
            return False
        else:
            return True

    # * Deal with Static Files

    def copyStatic(self, paths, verbose=True):
        """Copies static files or directories given in dirpaths to the build directory.

        Args:

            paths (:obj:`list` of :obj:`str`):
                a list of paths to files or directories

        Returns:

            None
        """
        for path in paths:
            source = os.path.join(os.getcwd(), path)
            destination = os.path.join(self.buildPath, path)
            if verbose:
                print("Copying {} to {}...".format(path, destination))
            self._ensureParent(path)
            shutil.copy2(source, destination)

    # * Deal with Pandoc Files

    def _platify(self, string, template):
        """Wraps a string as a template.

        Args:

            string (:obj:`str`): the string to wrap.

            template (:obj:`str`): the name of a template to use

        Returns:

            (:obj:`str`): The string wrapped as a template.

        """
        prefix = '{{% extends "{}" %}}\n{{% block body %}}'\
                 .format(template)
        suffix = '{% endblock %}'
        return '{}\n{}\n{}'.format(prefix, string, suffix)

    def renderDoc(self, docType, path, prettyLink=True, verbose=True):
        """Renders a file at the filepath via pandoc.

        Requires the existence of a template in ~self.templatePath~ with the
        name corresponding to a parent directory in ~self.pandocDirs~.

        Args:

            docType (:obj:`str`):
                Type of the document to look out for.
                Must be the input type supported by pandoc.

            path (:obj:`str`):
                A relative path to the directory with files

        Returns:

            None

        """
        source = os.path.join(os.getcwd(), path)
        destination = os.path.join(self.templatePath, path)

        docfilepaths = pathlib.Path(source).glob('*.' + docType)
        docTemplate = "_" + os.path.basename(path) + ".html"

        templatePath = os.path.join(self.templatePath, docTemplate)
        assert os.path.isfile(templatePath) is True, \
            "No template {} has been found, aborting.".format(templatePath)

        for filepath in docfilepaths:
            with open(str(filepath), 'r') as docfile:
                htmltext = pypandoc.convert(docfile.read(), "html",
                                            format=docType)
            htmltext = self._platify(htmltext, docTemplate)
            if prettyLink:
                pagedir = os.path.join(destination,
                                       filepath.with_suffix('').name)
                newFilepath = os.path.join(pagedir, "index.html")
                pathlib.Path(pagedir).mkdir(parents=True, exist_ok=True)
                with open(newFilepath, 'w') as f:
                    f.write(htmltext)
            else:
                newFilepath = os.path.join(destination, filepath.name)
                with open(newFilepath, 'w') as f:
                    f.write(htmltext)

    def renderDocs(self, docType, dirpaths, prettyLink=True, verbose=True):
        """Renders files given in filepaths via pandoc.

        Requires the existence of templates in ~self.templatePath~ with the
        names corresponding to each directory in ~self.pandocDirs~.

        Args:

            docType (:obj:`str`):
                Type of the document to look out for.
                Must be the input type supported by pandoc.

            dirpaths (:obj:`list` of :obj:`str`):
                A list of relative paths to directories with files

        Returns:

            None

        """

        for path in dirpaths:
            self.renderDoc(docType, path, prettyLink=True, verbose=True)

    # * Deal with Templates

    def renderTemplate(self, template):
        """Renders a jinja2 template to a corresponding file.

        Args:

            template (:obj:`jinja2.Template`): A jinja2 template to render.

        Returns:

            None.
        """

        self._ensureParent(template.name)
        filepath = os.path.join(self.buildDir, template.name)
        template.stream().dump(filepath, self.encoding)

    def renderTemplates(self, templates):
        """Render a list of jinja2 templates.
        Args:

            templates (:obj:`list` of :obj:`jinja2.Template`): a template list

        Returns:

            None.

        """

        for template in templates:
            self.renderTemplate(template)

    def render(self, prettyLink=True, reloader=False):
        """Generate pages.

        Args:

            reloader (:obj:`bool`):
                If True, a watchdog is spawned to look for
                changes in templates.

        """
        pathlib.Path(self.buildDir).mkdir(parents=True, exist_ok=True)
        for docType in self.pandocTypes:
            self.renderDocs(docType, self.pandocDirs, prettyLink)
        self.renderTemplates(self.templates)
        self.copyStatic(self.staticFiles, verbose=self.verbose)

        if reloader:
            self.logger.info("Watching for changes in {}..."
                             .format(self.templatePath))
            self.logger.info("Press Ctrl + C to stop.")
            Watcher(self, self.verbose).watch()


# * Main Functions


def make(templatePath=TEMPLATE_DIRECTORY,
         buildDir=BUILD_PATH,
         pandocDirs=PANDOC_DIRS,
         pandocTypes=PANDOC_TYPES,
         staticDirs=ASSETS,
         encoding=ENCODING,
         verbose=True):
    """Instantiate a GrashSite object.

    Args:

        encoding (:obj:`str`):
            A string representing the encoding of the rendered templates.

        jinjaEnv (:obj:`jinja2.Environment`):
            Main class for Jinja

        templatePath (:obj:`str`):
            The path where templates reside.

        buildDir (:obj:`str`):
            The path to the build directory

        staticDirs  (:obj:`list` of :obj:`str`):
            The list of paths to the directories with static files.

        pandocDirs (:obj:`str`):
            The path to the directory with files to be processed with pandoc.

        pandocTypes (:obj:`list` of :obj:`str`):
            A list of file formats to process with pandoc.

        logger (:obj:`logging.Logger`):
            Event logger

        verbose (:obj:`bool`):
            True if the methods should be verbose on execution,
            False otherwise.

    """
    jinjaEnvArgs = {}
    jinjaEnvArgs['loader'] = FileSystemLoader(searchpath=templatePath,
                                              encoding=encoding,
                                              followlinks=True)
    jinjaEnvironment = Environment(**jinjaEnvArgs)

    logger = logging.getLogger(__name__)
    logger.setLevel(logging.INFO)
    logger.addHandler(logging.StreamHandler())
    return GrashSite(encoding=encoding,
                     jinjaEnvironment=jinjaEnvironment,
                     logger=logger,
                     templatePath=templatePath,
                     buildDir=buildDir,
                     pandocDirs=pandocDirs,
                     staticDirs=staticDirs,
                     verbose=verbose)
