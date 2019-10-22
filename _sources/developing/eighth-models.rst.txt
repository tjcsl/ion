*******************************
Understanding the Eighth models
*******************************

Most of Ion's apps either do not have models or only have very basic models. The ``eighth`` app, however, has a complicated system of models.

What follows is a brief list of the eighth models with a description of each. More information is available in comments of the source code.

- ``EighthSponsor``: Represents a sponsor for an eighth period activity. Stores some information on the sponsor, including first/last name and department name. The ``user`` field that associates the ``EighthSponsor`` with a ``User`` is optional, but almost always set.

- ``EighthRoom``: Represents a room in which an eighth period activity can be held. Stores the name, the capacity, and whether the room is available for use in eighth period activities. If the capacity is -1, that is considered to be infinite capacity.

- ``EighthActivity``: Represents an eighth period activity. Note that this represents an activity, not a specific scheduling of the activity. In other words, only one of these exists for each club/team/special activity.

  In addition to the name and the description, this stores a lot of information about the activity that will be explained later.

- ``EighthBlock``: Represents an eighth period block. Stores the date, the time to sign up by, the "letter" of the block, whether the block is locked, and some other miscellaneous information.

- ``EighthScheduledActivity``: Represents a scheduling of an eighth period activity during a particular block. Has ``ForeignKey``\s to the the ``EighthBlock`` and the ``EighthActivity`` that it is associated with, and keeps track of whether it has been cancelled and whether it has had its attendance taken. As with ``EighthActivity``, this will be explained in more detail later.

  The ``add_user()`` method of this class is where all of the logic to sign a user up for an activity is. Be *very* careful when modifying it.

- ``EighthSignup``: Represents that a user is signed up for a particular ``EighthScheduledActivity`` during the block for which it is scheduled. Has ``ForeignKey``\s to the ``EighthScheduledActivity`` and the ``User`` objects. Also stores some information such as whether the user signed up after the deadline (assumed to be a pass), whether the user signed themselves up or was signed up by an eighth admin, the name and sponsor list of the activity they were signed up for previously (if applicable), whether they were absent, etc.
  
  **Note**: Since Ion's launch, it has been plagued by duplicate ``EighthSignup``\s (``EighthSignup``\s for the same user during the same block) being created. There are multiple checks before the object is saved to make sure it is unique, and uniqueness is enforced on a per-user, per- ``EighthScheduledActivity`` basis at the model level, but the problem has continued. As of summer 2019, measures have been enacted that will hopefully minimize the occurrences of this issue in the future, as well as allow better diagnosing of the problem if it occurs again.

- ``EighthWaitlist``: Ion has all of the backend logic to implement waitlists for each activity, but it is not enabled in production (``settings.ENABLE_WAITLIST`` is ``False``). When the waitlist is enabled, an ``EighthWaitlist`` object represents that a user signed up for the waitlist for a particular ``EighthScheduledActivity`` at a particular time. The user's position in the waitlist is calculated dynamically by finding the number of users who signed up for the waitlist before them.

- ``EighthActivitySimilarity``: Keeps track of the similarity index of two activities, based on which users attend which activities. Used to recommend activities.


More details on ``EighthActivity`` and ``EighthScheduledActivity``
==================================================================

There are a number of fields (the sponsor list, the room list, the activity capacity, whether the activity runs both blocks, whether it is restricted, etc.) that are usually the same for all schedulings of an ``EighthActivity``, but sometimes change on a per-activity basis. Hence, both ``EighthActivity`` and ``EighthScheduledActivity`` have fields that record this information, and ``EighthScheduledActivity`` has helper methods that check both fields to determine the "real" value.

For ``BooleanField``\s, this is simple: if either of the ``EighthScheduledActivity``'s field and the ``EighthActivity``'s field is set to ``True``, the activity is considered to have that property. For the room list and the sponsor list, the ``EighthScheduledActivity``'s list is used if it has at least one room/sponsor; otherwise, the ``EighthActivity``'s list is used.

In addition, the capacity has multiple overrides:

- If the ``EighthScheduledActivity`` has the ``capacity`` field set, it is used.
- If the ``EighthScheduledActivity`` has at least one room, the sum of all of their capacities is used.
- If the ``EighthActivity`` has the ``default_capacity`` field set, it is used.
- Finally, the sum of all of the capacities of the ``EighthActivity``'s rooms is used.

Note that if the capacity is -1, it denotes unrestricted capacity. If the capacity calculation ends up using the sum of the capacities of a set of rooms and one of the room's capacities is -1, the activity's capacity will also be -1.
