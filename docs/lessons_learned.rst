=================
Lessons Learned
=================

Some of these are common sense, and others we learned during the events in question.

DjangoCon 2010
==============

* For sprints, show up early the first day.

* Stay in a hotel near the sprint. If you have to spend an hour going each way that's up to 20% of sprint time you are wasting each day. If necessary, switch hotels.

PyCon 2011
==========

Getting Sprinters
-----------------

* Mark easy stuff for beginners. After they knock out an issue or two the stuff they've learned lets them handle harder tasks.

* Sit-down with each new contributor individually for at least 15 minutes to help them through the installation process. They get started much faster. you'll spot the mistakes in your docs, and they'll hang around longer.

* If you see anyone during the sprints who looks lost or without a project, invite them to join you.

* If you have a full sprint table and a non-sprinter is sitting with you get them to contribute something small. They go from being a distraction to a valued member of the team.

* Go out for dinner at a fun restaurant the first night with just your team. On other nights try to keep meals short since long meals mean hours of missed sprint time.

Assigning Work
--------------

* Assign issues in the issue tracker to specific people. No one should work a task unless they have had it assigned to them. This way you avoid duplication of effort.

* Tell people if they get stuck on something for 30 minutes to ask questions. We are all beginners and the hardest problems often become simple spelling mistakes when you try and explain them.

Be conservative
---------------

You don't want to stall people from doing the work they are trying to get done. So that means:

* Keep the database as stable as possible during a large sprint.

* Freeze the design during a sprint. Have designer-oriented people prettify neglected views e.g. the login page, server error pages.

Helping people get stuff done
------------------------------

* If you are leading a sprint don't expect to get any code done yourself. Your job is to facilitate other people to have fun hacking, learning, and getting things done.

* Go around and ask questions of your sprinters periodically. People are often too shy to come up to you but if you go up to them they'll readily ask for help.

* Update your install documentation as your sprinters discover problems.

* If you have new dependencies, let everyone know as soon and as loudly as possible.

* Good documentation is as important as code. When people ask questions rather than just answering the question, walk them through the specific answer in your docs. If the answer doesn't exist, document it yourself and have them help you write the answer.

* Demonstrate coverage.py to the sprinters, show them how to write tests, and provide good test examples. Good test coverage will save everyone a lot of grief during development and deployment.

* Have your code working on all major platforms with installation instructions for each platform. Your code on all platforms will be that much stable for it.

* Have a portable drive with the dependencies for your project on it. You can never count on the network being reliable at a sprint.

* If a beginning developer asks for help, try to get your advanced sprinters to answer the questions and possibly pair with them for a while.

* When someone is working really hard and is trying to focus, run interference for them.

Pull Requests
-------------

* Provide good and bad pull request examples.

* Don't be afraid of sounding stupid if you don't understand someone's pull request. If it confuses you it's going to confuse newcomers even more and hence make your code unmaintainable. Remember that simplicity is a virtue and is one of the best things of projects like Python, Pyramid, and Flask.

* Each time someone submits a pull request, ask them if they've run the full test suite. Yeah, it's repetitive but they'll thank you for it.

* If someone submits a broken pull request, see if you can work out the issue with them. If the problem is not easily corrected, ask them to fix the problem and resubmit the pull request.