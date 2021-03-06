# -*- coding: utf-8 -*-
"""
Math Render Plugin for Pelican
==============================
This plugin allows your site to render Math. It uses
the MathJax JavaScript engine.

For markdown, the plugin works by creating a Markdown
extension which is used during the markdown compilation stage.
Math therefore gets treated like a "first class citizen" in Pelican

For reStructuredText, the plugin instructs the rst engine
to output Mathjax for for math.

The mathjax script is automatically inserted into the HTML.

Typogrify Compatibility
-----------------------
This plugin now plays nicely with Typogrify, but it requires
Typogrify version 2.04 or above.

User Settings
-------------
Users are also able to pass a dictionary of settings in the settings file which
will control how the MathJax library renders things. This could be very useful
for template builders that want to adjust the look and feel of the math.
See README for more details.
"""

import os
import sys

from pelican import signals

try:
    from bs4 import BeautifulSoup
except ImportError as e:
    BeautifulSoup = None

try:
    from . pelican_mathjax_markdown_extension import PelicanMathJaxExtension
except ImportError as e:
    PelicanMathJaxExtension = None

def process_settings(pelicanobj):
    """Sets user specified MathJax settings (see README for more details)"""

    mathjax_settings = {}

    # NOTE TO FUTURE DEVELOPERS: Look at the README and what is happening in
    # this function if any additional changes to the mathjax settings need to
    # be incorporated. Also, please inline comment what the variables
    # will be used for

    # Default settings
    mathjax_settings['auto_insert'] = True  # if set to true, it will insert mathjax script automatically into content without needing to alter the template. 
    mathjax_settings['align'] = 'center'  # controls alignment of of displayed equations (values can be: left, right, center)
    mathjax_settings['indent'] = '0em'  # if above is not set to 'center', then this setting acts as an indent
    mathjax_settings['show_menu'] = 'true'  # controls whether to attach mathjax contextual menu
    mathjax_settings['process_escapes'] = 'true'  # controls whether escapes are processed
    mathjax_settings['latex_preview'] = 'TeX'  # controls what user sees while waiting for LaTex to render
    mathjax_settings['color'] = 'inherit'  # controls color math is rendered in
    mathjax_settings['linebreak_automatic'] = 'false'  # Set to false by default for performance reasons (see http://docs.mathjax.org/en/latest/output.html#automatic-line-breaking)
    mathjax_settings['tex_extensions'] = ''  # latex extensions that can be embedded inside mathjax (see http://docs.mathjax.org/en/latest/tex.html#tex-and-latex-extensions)
    mathjax_settings['responsive'] = 'false'  # Tries to make displayed math responsive
    mathjax_settings['responsive_break'] = '768'  # The break point at which it math is responsively aligned (in pixels)
    mathjax_settings['mathjax_font'] = 'default'  # forces mathjax to use the specified font.
    mathjax_settings['process_summary'] = BeautifulSoup is not None  # will fix up summaries if math is cut off. Requires beautiful soup

    # Source for MathJax: Works boths for http and https (see http://docs.mathjax.org/en/latest/start.html#secure-access-to-the-cdn)
    mathjax_settings['source'] = "'//cdn.mathjax.org/mathjax/latest/MathJax.js?config=TeX-AMS-MML_HTMLorMML'"

    # Get the user specified settings
    try:
        settings = pelicanobj.settings['MATH_JAX']
    except:
        settings = None

    # If no settings have been specified, then return the defaults
    if not isinstance(settings, dict):
        return mathjax_settings

    # The following mathjax settings can be set via the settings dictionary
    for key, value in ((key, settings[key]) for key in settings):
        # Iterate over dictionary in a way that is compatible with both version 2
        # and 3 of python

        if key == 'align':
            try:
                typeVal = isinstance(value, basestring)
            except NameError:
                typeVal = isinstance(value, str)

            if not typeVal:
                continue

            if value == 'left' or value == 'right' or value == 'center':
                mathjax_settings[key] = value
            else:
                mathjax_settings[key] = 'center'

        if key == 'indent':
            mathjax_settings[key] = value

        if key == 'show_menu' and isinstance(value, bool):
            mathjax_settings[key] = 'true' if value else 'false'

        if key == 'auto_insert' and isinstance(value, bool):
            mathjax_settings[key] = value

        if key == 'process_escapes' and isinstance(value, bool):
            mathjax_settings[key] = 'true' if value else 'false'
        
        if key == 'latex_preview':
            try:
                typeVal = isinstance(value, basestring)
            except NameError:
                typeVal = isinstance(value, str)

            if not typeVal:
                continue

            mathjax_settings[key] = value
        
        if key == 'color':
            try:
                typeVal = isinstance(value, basestring)
            except NameError:
                typeVal = isinstance(value, str)

            if not typeVal:
                continue

            mathjax_settings[key] = value
        
        if key == 'linebreak_automatic' and isinstance(value, bool):
            mathjax_settings[key] = 'true' if value else 'false'
        
        if key == 'process_summary' and isinstance(value, bool):
            if value and BeautifulSoup is None:
                print("BeautifulSoup4 is needed for summaries to be processed by render_math\nPlease install it")
                value = False

            mathjax_settings[key] = value
        
        if key == 'responsive' and isinstance(value, bool):
            mathjax_settings[key] = 'true' if value else 'false'
        
        if key == 'responsive_break' and isinstance(value, int):
            mathjax_settings[key] = str(value)

        if key == 'tex_extensions' and isinstance(value, list):
            # filter string values, then add '' to them
            try:
                value = filter(lambda string: isinstance(string, basestring), value)
            except NameError:
                value = filter(lambda string: isinstance(string, str), value)

            value = map(lambda string: "'%s'" % string, value)
            mathjax_settings[key] = ',' + ','.join(value)

        if key == 'mathjax_font':
            try:
                typeVal = isinstance(value, basestring)
            except NameError:
                typeVal = isinstance(value, str)

            if not typeVal:
                continue

            value = value.lower()

            if value == 'sanserif':
                value = 'SansSerif'
            elif value == 'fraktur':
                value = 'Fraktur'
            elif value == 'typewriter':
                value = 'Typewriter'
            else:
                value = 'default'

            mathjax_settings[key] = value

    return mathjax_settings

def process_summary(instance):
    """Ensures summaries are not cut off. Also inserts
    mathjax script so that math will be rendered"""

    summary = instance._get_summary()
    summary_parsed = BeautifulSoup(summary, 'html.parser')
    math = summary_parsed.find_all(class_='math')

    if len(math) > 0:
        last_math_text = math[-1].get_text()
        if len(last_math_text) > 3 and last_math_text[-3:] == '...':
            content_parsed = BeautifulSoup(instance._content, 'html.parser')
            full_text = content_parsed.find_all(class_='math')[len(math)-1].get_text()
            math[-1].replace_with("%s\ \ldots\)" % full_text[:-2])
            summary = summary_parsed.encode('ascii')
  
        instance._summary = "%s<script type='text/javascript'>%s</script>" % (summary, process_summary.mathjax_script)

def configure_typogrify(pelicanobj, mathjax_settings):
    """Instructs Typogrify to ignore math tags - which allows Typogfrify
    to play nicely with math related content"""

    # If Typogrify is not being used, then just exit
    if not pelicanobj.settings.get('TYPOGRIFY', False):
        return

    try:
        import typogrify
        from distutils.version import LooseVersion

        if LooseVersion(typogrify.__version__) < LooseVersion('2.0.7'):
            raise TypeError('Incorrect version of Typogrify')

        from typogrify.filters import typogrify

        # At this point, we are happy to use Typogrify, meaning
        # it is installed and it is a recent enough version
        # that can be used to ignore all math
        # Instantiate markdown extension and append it to the current extensions
        pelicanobj.settings['TYPOGRIFY_IGNORE_TAGS'].extend(['.math', 'script'])  # ignore math class and script

    except (ImportError, TypeError, KeyError) as e:
        pelicanobj.settings['TYPOGRIFY'] = False  # disable Typogrify

        if isinstance(e, ImportError):
            print("\nTypogrify is not installed, so it is being ignored.\nIf you want to use it, please install via: pip install typogrify\n")

        if isinstance(e, TypeError):
            print("\nA more recent version of Typogrify is needed for the render_math module.\nPlease upgrade Typogrify to the latest version (anything equal or above version 2.0.7 is okay).\nTypogrify will be turned off due to this reason.\n")

        if isinstance(e, KeyError):
            print("\nA more recent version of Pelican is needed for Typogrify to work with render_math.\nPlease upgrade Pelican to the latest version or clone it directly from the master GitHub branch\nTypogrify will be turned off due to this reason\n")

def process_mathjax_script(mathjax_settings):
    """Load the mathjax script template from file, and render with the settings"""
    
    # Read the mathjax javascript template from file
    with open (os.path.dirname(os.path.realpath(__file__))+'/mathjax_script_template', 'r') as mathjax_script_template:
        mathjax_template = mathjax_script_template.read()

    return mathjax_template.format(**mathjax_settings)

def mathjax_for_markdown(pelicanobj, mathjax_script, mathjax_settings):
    """Instantiates a customized markdown extension for handling mathjax
    related content"""

    # Create the configuration for the markdown template
    config = {}
    config['mathjax_script'] = mathjax_script
    config['math_tag_class'] = 'math'
    config['auto_insert'] = mathjax_settings['auto_insert']

    # Instantiate markdown extension and append it to the current extensions
    try:
        pelicanobj.settings['MD_EXTENSIONS'].append(PelicanMathJaxExtension(config))
    except:
        sys.excepthook(*sys.exc_info())
        sys.stderr.write("\nError - the pelican mathjax markdown extension failed to configure. MathJax is non-functional.\n")
        sys.stderr.flush()

def mathjax_for_rst(pelicanobj, mathjax_script):
    """Setup math for RST"""

    pelicanobj.settings['DOCUTILS_SETTINGS'] = {'math_output': 'MathJax'}
    rst_add_mathjax.mathjax_script = mathjax_script

def pelican_init(pelicanobj):
    """Loads the mathjax script according to the settings. Instantiate the Python
    markdown extension, passing in the mathjax script as config parameter
    """

    # Process settings, and set global var
    mathjax_settings = process_settings(pelicanobj)

    # Generate mathjax script
    mathjax_script = process_mathjax_script(mathjax_settings)

    # Configure Typogrify
    configure_typogrify(pelicanobj, mathjax_settings)

    # Configure Mathjax For Markdown
    if PelicanMathJaxExtension:
        mathjax_for_markdown(pelicanobj, mathjax_script, mathjax_settings)

    # Configure Mathjax For RST
    mathjax_for_rst(pelicanobj, mathjax_script)

    # Set process_summary's mathjax_script variable
    process_summary.mathjax_script = None
    if mathjax_settings['process_summary']:
        process_summary.mathjax_script = mathjax_script

def rst_add_mathjax(instance):
    """Adds mathjax script for RST"""
    _, ext = os.path.splitext(os.path.basename(instance.source_path))
    if ext != '.rst':
        return

    # If math class is present in text, add the javascript
    if 'class="math"' in instance._content:
        instance._content += "<script type='text/javascript'>%s</script>" % rst_add_mathjax.mathjax_script

def pelican_connect(instance):
    """Adds mathjax script to RST and processes summaries"""

    if instance._content:
        rst_add_mathjax(instance)

        if process_summary.mathjax_script is not None:
            process_summary(instance)

def register():
    """Plugin registration"""
    signals.initialized.connect(pelican_init)
    signals.content_object_init.connect(pelican_connect)
