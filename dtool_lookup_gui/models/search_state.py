
class SearchState:
    """The client model of the search state, e.g. current pagination, sorting, search keywords, ..."""

    def __init__(self):

        self._search_text = ""

        self._page_size = 10
        self._fetching_results = False

        self.reset_pagination()
        self.reset_sorting()

        self.sort_field_label_dict = {
            "uri": "URI",
            "name": "name",
            "base_uri": "base URI",
            "created_at": "created at",
            "frozen_at": "frozen at",
            "uuid": "UUID",
            "creator_username": "creator username",
        }
        self.label_sort_field_dict = {value: key for key, value in self.sort_field_label_dict.items()}
        self.page_size_choices = [5, 10, 20, 50, 100]

    def reset_pagination(self):
        """Reset pagination information to single page"""
        self._current_page = 1
        self._first_page = 1
        self._last_page = 1
        self._total_pages = 1
        self._total_number_of_entries = 0

    def reset_sorting(self):
        """Reset sorting information to uri"""
        self._sort_fields = ["uri"]
        self._sort_order = [1]

    # search_text property
    def get_search_text(self):
        return self._search_text

    def set_search_text(self, value):
        self._search_text = value

    # current_page property
    def get_current_page(self):
        return self._current_page

    def set_current_page(self, value):
        # if not isinstance(value, int) or value < 1:
        #    raise ValueError("Current page must be a positive integer")
        if value < 1:
            value = 1
        elif value > self.last_page:
            value = self.last_page
        self._current_page = value

    # last_page property
    def get_last_page(self):
        return self._last_page

    def set_last_page(self, value):
        if not isinstance(value, int) or value < 1:
            raise ValueError("Last page must be a positive integer")
        self._last_page = value

    # first_page property
    def get_first_page(self):
        return self._first_page

    def set_first_page(self, value):
        if not isinstance(value, int) or value < 1:
            raise ValueError("Last page must be a positive integer")
        self._first_page = value

    # page_size property
    def get_page_size(self):
        return self._page_size

    def set_page_size(self, value):
        if not isinstance(value, int) or value < 1:
            raise ValueError("Page size must be a positive integer")
        self._page_size = value

    # fetching_results property
    def get_fetching_results(self):
        return self._fetching_results

    def set_fetching_results(self, value):
        if not isinstance(value, bool):
            raise ValueError("Fetching results must be a boolean")
        self._fetching_results = value

    # sort_fields property
    def get_sort_fields(self):
        return self._sort_fields

    def set_sort_fields(self, value):
        if isinstance(value, str):
            value = [value]
        if not isinstance(value, list):
            raise ValueError("Sort fields must be a list")
        for sort_field in value:
            if sort_field not in self.sort_field_label_dict:
                raise ValueError("Sort field %s not allowed", sort_field)
        self._sort_fields = value

    # sort_order property
    def get_sort_order(self):
        return self._sort_order

    def set_sort_order(self, value):
        if isinstance(value, int):
            value = [value]
        if not isinstance(value, list):
            raise ValueError("Sort order must be a list")
        if len(value) != len(self.sort_fields):
            raise ValueError("Sort order list must have same length as sort fields list")
        self._sort_order = value

    def ingest_pagination_information(self, pagination):
        """Sets pagination information to values found in dict of format

           {"total": 284, "total_pages": 29, "first_page": 1, "last_page": 29, "page": 1, "next_page": 2}
        """
        self.first_page = pagination.get("first_page", 1)
        self.last_page = pagination.get("last_page", 1)
        self.current_page = pagination.get("page", 1)
        self._total_pages = pagination.get("total_pages", 1)
        self._total_number_of_entries = pagination.get("total", 0)

    def ingest_sorting_information(self, sorting):
        """Sets sorting information to values found in dict of format

               {"base_uri": 1, "name": -1}
        """
        sort_fields = []
        sort_order = []

        sort_info = sorting.get("sort", {})
        for key, value in sort_info.items():
            sort_fields.append(key)
            sort_order.append(value)

        self.sort_fields = sort_fields
        self.sort_order = sort_order

    # Properties
    search_text = property(get_search_text, set_search_text)
    current_page = property(get_current_page, set_current_page)
    last_page = property(get_last_page, set_last_page)
    first_page = property(get_first_page, set_first_page)
    page_size = property(get_page_size, set_page_size)
    fetching_results = property(get_fetching_results, set_fetching_results)
    sort_fields = property(get_sort_fields, set_sort_fields)
    sort_order = property(get_sort_order, set_sort_order)

    @property
    def next_page(self):
        if self.current_page >= self.last_page:
            return self.last_page
        else:
            return self.current_page + 1

    @property
    def previous_page(self):
        if self.current_page <= self.first_page:
            return self.first_page
        else:
            return self.current_page - 1
    @property
    def total_pages(self):
        return self._total_pages

    @property
    def total_number_of_entries(self):
        return self._total_number_of_entries