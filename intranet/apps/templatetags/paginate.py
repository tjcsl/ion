from django import template

register = template.Library()


@register.simple_tag
def query_transform(request, **kwargs):
    query = request.GET.copy()
    for k, v in kwargs.items():
        query[k] = v
    return query.urlencode()


@register.filter  # TODO: replace return type with list[int | None]
def page_list(paginator, current_page) -> list[int | None]:
    """Pagination

    If there is a ``None`` in the output, it should be replaced
    with ...'s.
    """
    SURROUNDING_PAGES = 2
    BEGINNING_PAGES = 2
    END_PAGES = 2
    total_pages = paginator.page_range

    # The page numbers to show
    actual_numbers = [
        page
        for page in total_pages
        if (
            page >= total_pages[-1] - END_PAGES + 1
            or page <= BEGINNING_PAGES
            or (current_page.number - SURROUNDING_PAGES <= page <= current_page.number + SURROUNDING_PAGES)
        )
    ]

    pages = []
    for i, number in enumerate(actual_numbers[:-1]):
        pages.append(number)
        # if there is a mismatch, that means we should add a ...
        if actual_numbers[i + 1] != number + 1:
            pages.append(None)
    pages.append(actual_numbers[-1])
    return pages
