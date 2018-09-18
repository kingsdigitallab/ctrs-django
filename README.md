# ctrs-django

This is the repository for the ctrs project at [Kings Digital Lab](https://kdl.kcl.ac.uk)

This project uses the technologies outlined in our [Technology Stack](https://stackshare.io/kings-digital-lab/django) and is configured to use [Vagrant](https://www.vagrantup.com/) for local development and [Fabric](http://www.fabfile.org/) for deployment.

## Getting started
1. Enter the project directory: `cd ctrs-django`
2. Start the virtual machine: `vagrant up`
3. SSH into the virtual machine: `vagrant ssh`
4. Run the local development server: `./manage.py runserver 0:8000`

You can then access the site locally at [http://localhost:8000](http://localhost:8000)

If the project is ldap-enabled, you can login using your LDAP credentials. Note: LDAP authentication will only work within the college firewall. Alternatively, use the default superuser login:

username: `vagrant`
password: `vagrant`

Note: This login will only work on a locally deployed virtual machine.

## Requirements
* Ansible >= 2.3
* NodeJS
* Vagrant >= 1.9
* VirtualBox >= 5.0

## Release 0.5.2 Beta
* Added TableBlock to the Stramfield components

## Release 0.5.1 Beta
* Fixed child page of type 'People page'

## Release 0.5 Beta
* Design applied
* Design implemented:
  * Model for home page boxes
  * Model for people index pages
  * Model for peopl page
  * Style blog index and blog post pages
  * Style index pages
  * Added sidebar
* Added Foundation Zurb framework
* Added FontAwesome

## Release 0.2.2

* Added funders and partners
* Typography styling
* Added description field display for team members pages
* Menu collapses on small screens (css only)

## Release 0.2.1

* Added feed image for blog index page
* Added feed image for index pages
* Changed the link for Cookie and Privacy policy to a single page

## Release 0.2

* Added Blog page types

## Release 0.1

First release of the basic site.

* Main templates in place:
    * 404
    * 500
    * Homepage
    * Index page
    * Richtext page

* Includes:
    * Main navigation
    * Index page children

Basic styling (CSS) in place.