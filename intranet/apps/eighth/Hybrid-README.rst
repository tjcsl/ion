**********
Changes made to Ion Eighth for Hybrid Learning
**********

The purpose of this document is to help whoever has to revert these changes that were made to support hybrid eighth periods by detailing exactly what was done. If it's not me (ldelwiche) doing it, please reach out with questions. As a general note, I'm going for clarity over neatness because this changes are dealing with a delicate part of Ion and because they are temporary and should be easy to later revert.

The motivation behind these changes was:
1) Avoid putting any extra burden on the 8PO
2) Keep these changes as seperate as possible so that they can be reverted
3) Not break ``eighth``

First, this document assumes that all students have been sorted into four groups named ``virtual``, ``in-person (a-k)``, ``in-person (l-z)`` and ``in-person``, that these groups are always correct and that each student is in only one group. It is on 8PO and/or the main office to ensure that these groups are accurate, not us. These groups NEED to be created for the code to work with ENABLE_HYBRID_EIGHTH set to True.

###########
Conventions
###########
Block Names --> ``* - Virt``, ``* - P1``, ``* - P2`` where the * is the block letter

* ``virtual`` will always sign up for the ``* - Virt`` blocks
* ``in-person (a-k)`` will sign up for ``* - P1`` blocks if they are present, else they will sign up for ``* - Virt`` blocks
* ``in-person (l-z)`` will sign up for ``* - P2`` blocks if they are present, else they will sign up for ``* - Virt`` blocks
* ``in-person`` will always sign up for the ``* - P1`` or ``* - P2`` blocks

Most of the work is done in either the block creation process or the activity scheduling process. However, there is other work done to hide extra blocks for students, to ensure teachers remember to take attendance and to clean up some naming. There is a setting called ``ENABLE_HYBRID_EIGHTH`` which is used extensively to enable these changes. When this is ``False``, Ion should behave like normal. However, be careful when setting this to ``False`` because the hybrid blocks won't display correctly. Nothing will break per se, but it won't be very user friendly. Specifics are below.

***********
Blocks
***********
* In ``intranet/templates/eighth/admin/add_blocks.html``, a checkbox is added to give 8PO control over if groups are automatically stickied into the appropriate blocks or not.

* In ``intranet/apps/eighth/views/admin/blocks.py``, everything that has been changed is placed between two lines of comments and is behind an if statement checking if the ``ENABLE_HYBRID_EIGHTH`` setting is ``True``. In ``edit_block_view``, a simple warning is given that changing a block name will not change the students that are stickied for that block. Trying to to this here just creates conflicts. 8PO is encouraged to just delete the block and create a new one. In ``add_block_view``, different ``visable_blocks`` are shown and additional context is added. If the "assign_hybrid" checkbox is checked, the appropriate groups will be sticked into the correct admin acitivity according to comments provided throughout and the naming conventions above. As a note, ``attendance_taken`` is set to true, although ``was_absent`` in ``EighthSignup`` is left blank. This is so that 8PO doesn't have to manually take attendance and no one will be marked absent.

* In ``intranet/apps/eighth/tasks.py``, a celery task for hybrid signups is added.

***********
Signups
***********
The block creation is all set up now, but let's improve user friendliness. For teachers/admin, this involves organizing their Activity Schedule widget and reminding them to take attendance for both of their blocks. For students, this involves organizing their Upcoming Eighth Periods widget to show only the ones they can sign up for and doing something similar to the Signup tab. It's a lot of changing little lines and passing context, but there are some more interesting querys in here. 

* In ``intranet/apps/eighth/models.py``, a property called ``hybrid_text`` is added to ``EighthBlock`` (between two lines of comments) which essentially takes the block names above and makes them more palatable for the end user.

* In ``intranet/apps/eighth/views/signup.py``, a section (between comment lines and behind an ENABLE_HYBRID_EIGHTH if statement) is changed to use ``hybrid_text`` over ``block_letter``. Another similar section passes hybrid context. In that same view, two similar sections are used to filter out the blocks where students are sticked into the admin activity. For these last two segments, 8PO (and other eigth_admins) will see all of the blocks, but students will only see the ones they aren't stickied for.

* In ``intranet/apps/dashboard/views.py``, changes (between comment lines and behind an ENABLE_HYBRID_EIGHTH if statement) essentially filter out blocks where a student is signed up for the "Hybrid Sticky" activity that indicates that block isn't applicable to them. Context is also added to pass onto both the teacher and student dashboard widgets.

* In ``intranet/apps/eighth/views/profile.py``, a section (between comment lines and behind an ENABLE_HYBRID_EIGHTH if statement) is changed to hide the stickied activities from students (but not eighth_admin). Context is passed in another section.

* In ``intranet/apps/eighth/views/attendance.py``, context is added to the take_attendance view to pass into the template based on the ENABLE_HYBRID_EIGHTH setting.

* In ``intranet/templates/eighth/take_attendance.html``, a reminder for teachers to take attendance is added to the top of the page and one line is changed to use ``block.hybrid_text`` instead of ``block.block_letter``.

* In ``intranet/templates/eighth/sponsor_widget.html``, one line is changed to use ``block.hybrid_text`` instead of ``block.block_letter``.

* In ``intranet/templates/eighth/signup_widget.html``, one line is changed to use ``block.hybrid_text`` instead of ``block.block_letter``.

* In ``intranet/templates/eighth/signup.html``, one line is changed to use ``block.hybrid_text`` instead of ``block.block_letter``.

* In ``intranet/templates/eighth/empty_state.html``, one line is changed to use ``block.hybrid_text`` instead of ``block.block_letter``.

* In ``intranet/templates/eighth/profile.html``, two lines are changed to use ``block.hybrid_text`` instead of ``block.block_letter``.

* In ``intranet/templates/eighth/profile_signup.html``, two lines are changed to use ``block.hybrid_text`` instead of ``block.block_letter``.

As I noted above, you (person reading this) probably have eighth_admin priviledges on production Ion and certainly have them on your dev environement. This means you WILL see all the blocks except in the widget on the dashboard. Log in as an unpriviledged student to get the full effect of the hidden activities.

***********
Admin
***********
At the request of 8PO, some normal eighth period admin actions that they use a lot are rewritten and placed in a seperate "Hybrid" section. The intention of this section is to give them tools adapted to the above configuration. The reason that I didn't modify the regular action is twofold: (a) IF this ever actually gets used, I want it to be easy to revert and (b) there is quite probably going to be a transition period where we are still virtual and doing normal eighth periods, but these hybrid changes are up. The understanding is that these functions assume a block is hybrid and won't work as expected when hybrid blocks aren't being used. The functions won't break if used with non-hybrid blocks, but I'd rather leave the originals to use in this case. 8PO understands and is good with this line of reasoning.

* In ``intranet/apps/eighth/views/admin/general.py``, context is passed in the dashboard view based on the ENABLE_HYBRID_EIGHTH setting.

* In ``intranet/templates/eighth/admin/dashboard.html``, a section containing links to the new hybrid tools is added according to hybrid context that is passed.

* In ``intranet/apps/eighth/urls.py``, urls are added for the new hybrid tools.

* In ``intranet/apps/eighth/views/admin/hybrid.py``, the ``activities_without_attendance_view`` and ``list_sponsor_view`` from other admin views are rewritten with hybrid Ion in mind. This is a new file.

* In ``intranet/templates/eighth/admin/list_sponsors_hybrid.html``, the ``list_sponsor.html`` template is rewritten. This is a new file.

* In ``intranet/templates/eighth/admin/activities_without_attendance_hybrid.html``, the ``activities_without_attendance.html`` template is rewritten. This is a new file.
