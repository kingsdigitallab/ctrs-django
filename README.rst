The community of the realm in Scotland, 1249–1424
=================================================

TODO: The community of the realm in Scotland, 1249–1424 description...

.. image:: https://img.shields.io/badge/License-MIT-yellow.svg
    :target: https://opensource.org/licenses/MIT
    :alt: MIT
.. image:: https://travis-ci.org/kingsdigitallab/cotr.svg?branch=master
    :target: https://travis-ci.org/kingsdigitallab/cotr
.. image:: https://coveralls.io/repos/github/kingsdigitallab/cotr/badge.svg?branch=master
    :target: https://coveralls.io/github/kingsdigitallab/cotr?branch=master
.. image:: https://readthedocs.org/projects/radical-translations/badge/?version=latest
    :target: https://cotr.readthedocs.io/en/latest/?badge=latest
    :alt: Documentation Status
.. image:: https://img.shields.io/badge/built%20with-Cookiecutter%20Django-ff69b4.svg
    :target: https://github.com/kingsdigitallab/cookiecutter-django/
    :alt: Built with Cookiecutter Django
.. image:: https://img.shields.io/badge/code%20style-black-000000.svg
    :target: https://github.com/ambv/black
    :alt: Black code style

Settings
--------

See detailed `cookiecutter-django settings documentation`_.

.. _cookiecutter-django settings documentation: http://cookiecutter-django-kingsdigitallab.readthedocs.io/en/latest/settings.html

Development
-----------

Local with Docker
^^^^^^^^^^^^^^^^^

See detailed `cookiecutter-django development with Docker documentation`_.

.. _cookiecutter-django development with Docker documentation: https://cookiecutter-django-kingsdigitallab.readthedocs.io/en/latest/developing-locally-docker.html

Local without Docker
^^^^^^^^^^^^^^^^^^^^

See detailed `cookiecutter-django local development documentation`_.

.. _cookiecutter-django local development documentation: https://cookiecutter-django-kingsdigitallab.readthedocs.io/en/latest/developing-locally.html

Basic Commands
--------------

Setting Up Your Users
^^^^^^^^^^^^^^^^^^^^^

* To create a **normal user account**, just go to Sign Up and fill out the
  form. Once you submit it, you'll see a "Verify Your E-mail Address" page. Go
  to your console to see a simulated email verification message. Copy the link
  into your browser. Now the user's email should be verified and ready to go.

* To create an **superuser account**, use this command::

    $ python manage.py createsuperuser

For convenience, you can keep your normal user logged in on Chrome and your
superuser logged in on Firefox (or similar), so that you can see how the site
behaves for both kinds of users.

Type checks
^^^^^^^^^^^

Running type checks with mypy:

::

  $ mypy cotr

Test coverage
^^^^^^^^^^^^^

To run the tests, check your test coverage, and generate an HTML coverage report::

    $ coverage run -m pytest
    $ coverage html
    $ open htmlcov/index.html

Running tests with py.test
~~~~~~~~~~~~~~~~~~~~~~~~~~

::

  $ pytest

Live reloading and Sass CSS compilation
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Moved to `Live reloading and SASS compilation`_.

.. _`Live reloading and SASS compilation`: http://cookiecutter-django-kingsdigitallab.readthedocs.io/en/latest/live-reloading-and-sass-compilation.html





Deployment
----------

The following details how to deploy this application.



Docker
^^^^^^

See detailed `cookiecutter-django Docker documentation`_.

.. _`cookiecutter-django Docker documentation`: http://cookiecutter-django-kingsdigitallab.readthedocs.io/en/latest/deployment-with-docker.html



