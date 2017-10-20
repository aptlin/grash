# * Variables


ASSETS = "assets"
BUILD_PATH = "build"
ENCODING = "utf8"
PANDOC_DIRS = []
PANDOC_TYPES = ["org"]
TEMPLATE_DIRECTORY = "templates"

# * Classes


class Settings:
    """A class for configuring Grash rendering.

    Attributes:

        encoding (:obj:`str`):
            A string representing the encoding of the rendered templates.

        templatePath (:obj:`str`):
            The path where templates reside.

        buildDir (:obj:`str`):
            The path to the build directory

        pandocDirs (:obj:`str`):
            The path to the directory with files to be processed with pandoc.

        pandocTypes (:obj:`list` of :obj:`str`):
            A list of file formats to process with pandoc.

        staticDirs  (:obj:`list` of :obj:`str`):
            The list of paths to the directories with static files.
            Defaults to ['pages', 'posts']

    """
    def __init__(self,
                 buildDir=BUILD_PATH,
                 staticDirs=ASSETS,
                 templatePath=TEMPLATE_DIRECTORY,
                 pandocDirs=PANDOC_DIRS,
                 pandocTypes=PANDOC_TYPES,
                 encoding=ENCODING):

        self.templatePath = templatePath
        self.buildDir = buildDir
        self.staticDirs = staticDirs
        self.encoding = encoding
        self.pandocDirs = pandocDirs
        self.pandocTypes = pandocTypes
