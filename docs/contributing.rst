Ways to contribute
==================

1. Report issues and bugs. A simple way that anyone can contribute is simply to
   report bugs and issues to the developing team. You can either send an email
   to the `pymatgen's Google Groups page`_ or even
   better, submit an Issue in our
   `github page <https://github.com/materialsproject/pymatgen/issues>`_.
   
2. Submitting new code. Another way to contribute is to submit new
   code/bugfixes to pymatgen. While you can always zip your code and email it
   to the maintainer of pymatgen, the best way for anyone to develop pymatgen
   is by adopting the collaborative Github workflow (see section below).
   
Collaborative Github Workflow
=============================

For developers interested in expanding pymatgen for their own purposes, we
recommend forking pymatgen directly from the 
`pymatgen GitHub repo`_. Here's a typical workflow (adapted from
http://www.eqqon.com/index.php/Collaborative_Github_Workflow):

.. note::

   Ignore the Github fork queue. Let the maintainer of pymatgen worry about
   the fork queue.

1. Create a free GitHub account (if you don't already have one) and perform the
   necessary setup (e.g., install SSH keys etc.).
2. Fork the pymatgen GitHub repo, i.e., go to the main 
   `pymatgen GitHub repo`_ and click fork to create a copy of the pymatgen code
   base on your own Github account.
3. Install git on your local machine (if you don't already have it).
4. Clone *your forked repo* to your local machine. You will work mostly with
   your local repo and only publish changes when they are ready to be merged:

   ::
   
       git clone git@github.com:YOURNAME/pymatgen.git

5. It is highly recommended you install all the optional dependencies as well.
6. Code (see `Coding Guidelines`_). Commit early and commit often. Keep your
   code up to date. You need to add the main repository to the list of your
   remotes. Let's name the upstream repo as mpmaster (materialsproject master).
   
   ::
       
       git remote add mpmaster git://github.com/materialsproject/pymatgen.git

   Make sure your repository is clean (no uncommitted changes) and is currently
   on the master branch. If not, commit or stash any changes and switch to the
   master.

   ::
   
      git checkout master
   
   Then you can pull all the new commits from the main line
   
   ::
   
      git pull mpmaster master
      
   Remember, pull is a combination of the commands fetch and merge, so there may
   be merge conflicts to be manually resolved.

7. Publish your contributions. Assuming that you now have a couple of commits
   that you would like to contribute to the main repository. Please follow the
   following steps:
   
   a. If your change is based on a relatively old state of the main repository,
      then you should probably bring your repository up-to-date first to see if
      the change is not creating any merge conflicts. 
   b. Check that everything compiles cleanly and passes all tests.
      The pymatgen repo comes with a complete set of tests for all modules. If
      you have written new modules or methods, you must write tests for the new
      code as well (see `Coding Guidelines`_). Install and run nosetest in your
      local repo directory and fix all errors before continuing further. There
      must be **no errors** for the nosetest.
   c. If everything is ok, publish the commits to your github repository.

      ::
      
         git push origin master

8. Now that your commit is published, it doesn't mean that it has already been
   merged into the main repository. You should issue a merge request to 
   pymatgen' maintainers. They will pull your commits and run their own tests
   before releasing.
   
   
Coding Guidelines
=================

Given that pymatgen is intended to be long-term code base, we adopt very strict
quality control and coding guidelines for all contributions to pymatgen. The
following must be satisfied for your contributions to be accepted into pymatgen.

1. **Unittests** are required for all new modules and methods. The only way to
   minimize code regression is to ensure that all code are well-tested. If the
   maintainer cannot test your code, the contribution will be rejected.
2. **Python PEP 8** `code style <http://www.python.org/dev/peps/pep-0008/>`_.
   We allow a few exceptions when they are well-justified (e.g., Element's
   atomic number is given a variable name of capital Z, in line with accepted
   scientific convention), but generally, PEP 8 must be observed.
3. **Documentation** required for all modules, classes and methods. In
   particular, the method docstrings should make clear documentation, the
   arguments expected and the return values. For complex algorithms (e.g., an
   Ewald summation), a summary of the alogirthm should be provided, and
   preferably with a link to a publication outlining the method in detail.
   
For the above, if in doubt, please refer to the core classes in pymatgen for
examples of what is expected.

.. _`pymatgen's Google Groups page`: https://groups.google.com/forum/?fromgroups#!forum/pymatgen/
.. _`pymatgen GitHub repo`: https://github.com/materialsproject/pymatgen