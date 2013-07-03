# -*- coding: utf-8 -*-
"""
    fabfile

    Fab file to build and push documentation to github

    :copyright: © 2013 by Openlabs Technologies & Consulting (P) Limited
    :license: BSD, see LICENSE for more details.
"""
import time

from fabric.api import local, lcd


def upload_documentation():
    """
    Build and upload the documentation HTML to github
    """
    temp_folder = '/tmp/%s' % time.time()
    local('mkdir -p %s' % temp_folder)

    # Build the documentation
    with lcd('doc'):
        local('make html')
        local('mv build/html/* %s' % temp_folder)

    # Checkout to gh-pages branch
    local('git checkout gh-pages')

    # Copy back the files from temp folder
    local('rm -rf *')
    local('mv %s/* .' % temp_folder)

    # Add the relevant files
    local('git add *.html')
    local('git add *.js')
    local('git add *.js')
    local('git add *.inv')
    local('git add _images')
    local('git add _sources')
    local('git add _static')
    local('git commit -m "Build documentation"')
    local('git push')

    print "Documentation uploaded to Github."
    print "View at: http://openlabs.github.io/magento-integration"
