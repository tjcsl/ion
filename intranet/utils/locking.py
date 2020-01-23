from typing import Dict, Iterable, List, Union

from django.db.models import Manager, Model, QuerySet


def lock_on(items: Iterable[Union[Model, Manager, QuerySet]]) -> None:
    """Given an iterable of ``Model`` instances, ``Manager``s, and/or ``QuerySet``s, locks the
    corresponding database rows.

    More specifically, this uses the Django ORM's ``select_for_update()`` method, which translates
    to a ``SELECT FOR UPDATE`` SQL query. For more information on what this actually does in
    PostgreSQL (used as the database backend in all environments) see PostgreSQL's
    documentation on locking at
    https://www.postgresql.org/docs/current/explicit-locking.html#LOCKING-ROWS.

    As described in Django's documentation at
    https://docs.djangoproject.com/en/stable/ref/models/queryset/#django.db.models.query.QuerySet.select_for_update,
    the ``select_for_update`` locks prevent other transactions from acquiring locks until
    this transaction is complete.

    This MUST by run in a transaction. A straightforward way to do this is to use the
    ``django.db.transaction.atomic`` wrapper.

    Args:
        items: An iterable of ``Model`` instances, ``Manager``s, and/or ``QuerySet``s representing
            the database rows to lock.

    """
    querysets_by_model: Dict[str, List[Union[Manager, QuerySet]]] = {}
    objects_by_model: Dict[str, List[Model]] = {}

    # First, we go through and categorize everything. Put instances in objects_by_model and
    # Managers/QuerySets in querysets_by_model.
    # Both are categorized by the dotted path to their class.
    for item in items:
        model_class = item.model if isinstance(item, (Manager, QuerySet)) else item.__class__
        model_fullname = model_class.__module__ + "." + model_class.__qualname__

        if isinstance(item, (Manager, QuerySet)):
            querysets_by_model.setdefault(model_fullname, [])
            querysets_by_model[model_fullname].append(item.all().nocache())
        else:
            objects_by_model.setdefault(model_fullname, [])
            objects_by_model[model_fullname].append(item)

    # Now we need to convert all the lists of instances to QuerySets. This is fairly
    # straightforward -- we get the PK (primary key) of each, then construct a QuerySet that
    # filters for those PKs, then add it to querysets_by_model.
    for model_fullname, objects in objects_by_model.items():
        # We only create the lists if we're about to put something in them, so this should never fail
        # unless the above code is modified in a way that breaks it
        assert objects

        # Get the model class and the PKs
        model_class = objects[0].__class__
        object_pks = [obj.pk for obj in objects]

        # Now construct a QuerySet and add it to the list
        querysets_by_model.setdefault(model_fullname, [])
        querysets_by_model[model_fullname].append(model_class.objects.filter(pk__in=object_pks).nocache())

    # Now, with all lists of QuerySets to lock in querysets_by_model, we actually do the locking.
    # We sort by the dotted name to the model class in an attempt to prevent deadlocks. If all workers
    # attempt to lock rows in the same order, they should never deadlock.
    for model_fullname in sorted(querysets_by_model.keys()):
        qs_list = querysets_by_model[model_fullname]

        # If this assertion fails, the above code has been modified in a way that breaks it
        assert qs_list

        # First, if there are multiple QuerySets for a given model, we need to combine them into one.
        combined_qs = qs_list.pop(0)
        if qs_list:
            # all=False explicitly only selects distinct values
            combined_qs = combined_qs.union(*qs_list, all=False)

        # Now we actually do the locking. We order by PK first in an attempt to prevent deadlocks.
        _ = list(combined_qs.order_by("pk").select_for_update().values_list("pk"))
